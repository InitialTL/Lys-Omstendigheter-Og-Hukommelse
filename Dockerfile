# Build the frontend separately. Production runs no Node.js process.
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt \
    && apt-get update && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*
COPY backend/*.py ./backend/
COPY scripts/backup_sqlite.py ./scripts/backup_sqlite.py
COPY scripts/start_hosted.sh /usr/local/bin/start-hosted
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
ENV STUDY_DATABASE=/data/results.db \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN groupadd --gid 10001 study \
    && useradd --uid 10001 --gid study --home-dir /app --shell /usr/sbin/nologin study \
    && mkdir -p /data && chmod 700 /data \
    && chmod 755 /usr/local/bin/start-hosted \
    && chown -R study:study /app
# Do not declare VOLUME here: on managed hosts it could mask a missing
# persistent mount with disposable/anonymous storage.
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/start-hosted"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + __import__('os').environ.get('PORT','8000') + '/api/health', timeout=3).read()" || exit 1
