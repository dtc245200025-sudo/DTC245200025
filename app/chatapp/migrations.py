"""Additive, idempotent migration for accounts created by the first app version."""

from sqlalchemy import inspect, text


def upgrade_email_schema(engine):
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(320031)"))
        inspector = inspect(connection)
        if not inspector.has_table("users"):
            return
        columns = {column["name"] for column in inspector.get_columns("users")}
        if "email" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(254)"))
        connection.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_lower ON users (lower(email))"
        ))


def upgrade_profile_schema(engine):
    definitions = {
        "display_name": "VARCHAR(80)",
        "bio": "VARCHAR(150) NOT NULL DEFAULT ''",
        "profile_public": "BOOLEAN NOT NULL DEFAULT TRUE",
        "email_public": "BOOLEAN NOT NULL DEFAULT FALSE",
        "avatar_data": "BYTEA",
        "auth_version": "INTEGER NOT NULL DEFAULT 0",
    }
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(320033)"))
        inspector = inspect(connection)
        if not inspector.has_table("users"):
            return
        columns = {column["name"] for column in inspector.get_columns("users")}
        for name, definition in definitions.items():
            if name not in columns:
                # All identifiers/types are constants above, never request input.
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {definition}"))


def upgrade_room_schema(engine):
    definitions = {
        "visibility": "VARCHAR(10) NOT NULL DEFAULT 'public'",
        "join_mode": "VARCHAR(12) NOT NULL DEFAULT 'open'",
        "max_members": "INTEGER",
        "password_hash": "VARCHAR(255)",
        "invite_token_hash": "VARCHAR(64)",
    }
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(320032)"))
        inspector = inspect(connection)
        if not inspector.has_table("rooms"):
            return
        columns = {column["name"] for column in inspector.get_columns("rooms")}
        for name, definition in definitions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE rooms ADD COLUMN {name} {definition}"))


def upgrade_message_schema(engine):
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(320034)"))
        for table in ("messages", "direct_messages"):
            inspector = inspect(connection)
            if not inspector.has_table(table):
                continue
            columns = {column["name"] for column in inspector.get_columns(table)}
            if "receipts_tracked" not in columns:
                # Historic messages have no reliable receipt history. Never
                # fabricate delivered/seen times for them during an upgrade.
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN receipts_tracked BOOLEAN NOT NULL DEFAULT FALSE"))
            if table == "messages":
                if "client_nonce" not in columns:
                    connection.execute(text("ALTER TABLE messages ADD COLUMN client_nonce VARCHAR(64)"))
                connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_room_message_nonce ON messages (room_id, user_id, client_nonce)"))
