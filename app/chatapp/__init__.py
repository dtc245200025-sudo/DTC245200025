import os
import time
import logging

from flask import Flask, request, session
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from prometheus_client import Counter, Histogram
from sqlalchemy import URL


db = SQLAlchemy()
socketio = SocketIO()
csrf = CSRFProtect()
HTTP_REQUESTS = Counter(
    "chat_http_requests_total", "HTTP requests", ["method", "endpoint", "status"]
)
HTTP_LATENCY = Histogram(
    "chat_http_request_duration_seconds", "HTTP request latency", ["endpoint"]
)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "development-only-key"),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", "sqlite:///chat-development.sqlite3"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=11 * 1024 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    if os.getenv("DB_HOST") and not test_config:
        app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
            "postgresql+psycopg",
            username=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=5432,
            database=os.environ["DB_NAME"],
        )
    if os.getenv("APP_ENV") == "production" and app.config["SECRET_KEY"] == "development-only-key":
        raise RuntimeError("SECRET_KEY must be configured for production")
    from .safe_logging import configure
    configure(app.logger)

    db.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app, async_mode="threading")

    from .routes import web
    from .events import register_events
    from .migrations import upgrade_email_schema, upgrade_profile_schema, upgrade_room_schema, upgrade_message_schema
    from .profiles import profiles
    from .rooms import room_actions
    from .friends import friends
    from .direct import direct, register_direct_events
    from .chat_tools import chat_tools
    from .notifications import notifications

    app.register_blueprint(web)
    app.register_blueprint(profiles)
    app.register_blueprint(room_actions)
    app.register_blueprint(friends)
    app.register_blueprint(direct)
    app.register_blueprint(chat_tools)
    app.register_blueprint(notifications)
    from .messaging import serialize
    app.jinja_env.globals["chat_payload"] = serialize
    register_events(socketio)
    register_direct_events(socketio)

    @app.before_request
    def start_timer():
        request._started_at = time.perf_counter()

    @app.after_request
    def record_request(response):
        if session.get("user_id"):
            response.headers["Cache-Control"] = "no-store"
        endpoint = request.endpoint or "unknown"
        HTTP_REQUESTS.labels(request.method, endpoint, response.status_code).inc()
        if response.status_code >= 400:
            app.logger.warning("http_request_rejected endpoint=%s status=%s", endpoint, response.status_code)
        if hasattr(request, "_started_at"):
            HTTP_LATENCY.labels(endpoint).observe(time.perf_counter() - request._started_at)
        return response

    with app.app_context():
        upgrade_email_schema(db.engine)
        upgrade_profile_schema(db.engine)
        upgrade_room_schema(db.engine)
        upgrade_message_schema(db.engine)
        db.create_all()

    return app
