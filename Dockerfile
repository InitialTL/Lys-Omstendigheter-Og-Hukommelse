# Multi-stage build. HTTPS/reverse proxy must be configured separately.
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/*.py ./backend/
COPY scripts/backup_sqlite.py ./scripts/backup_sqlite.py
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
ENV STUDY_DATABASE=/data/results.db \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN groupadd --gid 10001 study && useradd --uid 10001 --gid study --home-dir /app --shell /usr/sbin/nologin study \
    && mkdir -p /data && chown -R study:study /data /app
USER study
VOLUME ["/data"]
EXPOSE 8000
WORKDIR /app/backend
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--limit-concurrency", "32", "--timeout-keep-alive", "5", "--backlog", "64"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).read()" || exit 1
