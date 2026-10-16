FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

RUN addgroup --system --gid 10001 chat && \
    adduser --system --uid 10001 --ingroup chat --home /srv/app chat

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=chat:chat chatapp ./chatapp
COPY --chown=chat:chat wsgi.py ./wsgi.py

USER 10001:10001
EXPOSE 5000

HEALTHCHECK --interval=20s --timeout=3s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/healthz', timeout=2)"

CMD ["gunicorn", "--workers", "1", "--threads", "100", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
