#!/bin/sh
# Shared Railway / Fly.io / Docker Compose startup. Bind PORT and drop privilege.
set -eu

PORT="${PORT:-8000}"
case "$PORT" in
  *[!0-9]*|'') echo >&2 'Invalid PORT'; exit 64 ;;
esac
if [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
  echo >&2 'Invalid PORT range'; exit 64
fi

# Cloud machines must never write experimental data to an ephemeral rootfs.
# Docker Compose may use either a mounted named volume or local storage.
if [ -n "${RAILWAY_SERVICE_ID:-}" ] || [ -n "${FLY_APP_NAME:-}" ] || [ "${STUDY_REQUIRE_PERSISTENT_VOLUME:-0}" = 1 ]; then
  if ! python -c 'import sys
mounts = [line.split()[4].replace("\\040", " ") for line in open("/proc/self/mountinfo", encoding="utf-8")]
sys.exit(0 if "/data" in mounts else 1)' ; then
    echo >&2 'REFUSING START: /data is not a mounted persistent volume. Attach one first.'
    exit 78
  fi
fi

if [ "$(id -u)" = 0 ]; then
  # Root is used only for storage mount initialization, never the web server.
  chown -R 10001:10001 /data
  cd /app/backend
  exec gosu study uvicorn server:app --host 0.0.0.0 --port "$PORT" \
    --workers 1 --limit-concurrency 32 --timeout-keep-alive 5 --backlog 64
fi

# Support locally launched containers with an explicit non-root UID.
cd /app/backend
exec uvicorn server:app --host 0.0.0.0 --port "$PORT" \
  --workers 1 --limit-concurrency 32 --timeout-keep-alive 5 --backlog 64
