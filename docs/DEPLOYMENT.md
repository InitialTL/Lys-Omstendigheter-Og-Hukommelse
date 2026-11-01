# Production deployment — Hukommelse LM 2.7.1

The public study collects research data. **Software tests are not a substitute for**
checking consent rules for minors, Norwegian data-protection obligations, a
retention/deletion policy and secure off-device backups.

## Recommended architecture for Raspberry Pi 3

Cloudflare HTTPS → Cloudflare Tunnel on Pi → `http://127.0.0.1:8000` → one
FastAPI/Uvicorn worker → SQLite in a persistent private directory. **No port
forwarding** and no public inbound firewall rule. Avoid running Vite/Node in
production; serve the compiled frontend with FastAPI.

A 64-bit Raspberry Pi OS and adequate cooling/power/storage are recommended.
The backend and SQLite are light; the final build must be produced on a more
powerful machine. CI's Docker build verifies the production image on x86_64;
**a real Pi 3 has not been physically benchmarked**.

## Before accepting any participants

1. Obtain a domain managed through Cloudflare. In the Cloudflare dashboard,
   configure a remotely-managed Tunnel with the public hostname pointing to
   `http://localhost:8000` (when `cloudflared` runs on the Pi). Cloudflare
   documents this workflow at https://developers.cloudflare.com/tunnel/get-started/ .
   Do not publish `/api/admin/` without additional Cloudflare access controls.
2. Set `STUDY_ALLOWED_HOSTS=study.example.org,localhost,127.0.0.1` with your
   **actual** study domain and `STUDY_ALLOWED_ORIGINS=https://study.example.org`.
   Set `STUDY_TRUST_CLOUDFLARE=1` only if origin access is limited to the local
   Cloudflare Tunnel. Disable public inbound access to port 8000.
3. Generate an administrator secret with
   `python -c "import secrets; print(secrets.token_urlsafe(48))"`, keep it in a
   private `.env` file (`chmod 600`) or your secret manager, and never send it
   to participants. You can leave it unset to disable all admin downloads.
4. Plan encrypted off-device backups, retention and deletion. Do **not** add
   study files to Git, share database copies publicly or rely on an SD card as
   the only place holding study results.
5. Conduct a genuine pilot on each device class, verify that screen settings
   remain consistent, and freeze experimental stimuli before collecting data.

## Docker Compose (single private origin)

This repository has `Dockerfile` and `compose.yaml`. On a stronger machine,
build and publish an ARM64-compatible production image, or transfer the built
artifacts using a secure channel. **Do not try to build Node/Vite on a Pi 3 in
production**. Compose's default `build: .` is suitable for capable build hosts;
for Pi 3 use a prebuilt image and modify Compose `build:` to `image:`.

Create a private `.env` file from `backend/.env.example`, setting the three
public-origin variables and your optional admin secret. Start with
`docker compose up -d` on the host where the image was built, and check
`docker compose ps` and `curl -fsS http://127.0.0.1:8000/api/health`.

The container runs as UID 10001. **If upgrading an existing named data volume**
that was created by a root-running older container, run once *before* normal
startup:

```sh
docker compose run --rm --user root --entrypoint sh hukommelse-lm -c 'chown -R 10001:10001 /data'
```

On a deployment host without Docker, transfer `frontend/dist` from CI or a
computer, create a Python virtual environment, install
`backend/requirements.txt`, use persistent `STUDY_DATABASE` outside the repo,
and run **one** production Uvicorn worker bound to `127.0.0.1:8000` under a
restricted systemd service. Disable `--reload`.

## Preflight and backups

After building the frontend and setting your environment run:

```sh
python scripts/deployment_preflight.py
```

Back up with SQLite's online backup mechanism (not raw copying WAL files):

```sh
python scripts/backup_sqlite.py /private/off-device-backup-directory
```

In the Docker image:

```sh
docker compose exec -T hukommelse-lm python /app/scripts/backup_sqlite.py /data/backups
```

Copy the dated backup **out of the container and off the device**, encrypt it
and test restoring it. The built-in script does not upload or schedule backups;
use cron/systemd or your backup service for that. Make sure the backup storage
is inaccessible to participants. SQLite's backup API is documented at
https://www.sqlite.org/backup.html .

## Data recovery and integrity

Every completed recall round is saved in `study_results` immediately, before
perception questions. During recall, answers are also checkpointed into
`study_drafts` with a strictly increasing revision, then erased from drafts
after successful final submission. If the browser closes before final
submission, the incomplete checkpoint remains available to authorized
administrators via `/api/admin/drafts.csv` and can be resumed by the same
participant as long as the server deadline has not passed. These drafts are
**not** treated as valid completed rounds. Late submissions are flagged and
excluded from the primary analysis to avoid granting additional answering time.

To inspect data on the host, use `python backend/analyze_cli.py` with the
correct `STUDY_DATABASE`, or the admin CSV exports from a protected
connection. Historical protocol versions remain in the same database but
are excluded from the current protocol's primary analysis.

## Remaining deployment-specific checks

Verify the public hostname, TLS/Cloudflare rules, an actual Pi 3 memory/CPU
profile, SD-card write endurance, a real encrypted backup restore, and
participation consent obligations **before** publishing the research link.
No software can guarantee recovery of bytes never sent during a power failure
or offline tab closure. Rate limiting and bot defense at Cloudflare are still
required; the local application registration limiter is not a DDoS defense.
