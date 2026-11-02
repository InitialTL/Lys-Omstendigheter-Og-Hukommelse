# Publish Hukommelse LM without your own server (November 2026)

**Best for a first public pilot: Railway Hobby. Lowest practical bill: Fly.io.**
These instructions deploy the existing React static build and FastAPI API together
in one container, with SQLite on **one persistent volume**. A domain is optional;
both providers supply a free HTTPS hostname. The scientific protocol stays at
**2.7**; hosting changes do not alter timing, colors, questions or word lists.

## Prices and trade-offs

| Provider | Indicative monthly price | Advantages | Limitations |
| --- | --- | --- | --- |
| Railway Hobby | $5 minimum (includes $5 usage; pay overages) | GitHub deployments, simple domain/volume/backups | Cannot scale to multiple replicas with SQLite volume; a short restart on deploy |
| Fly.io, one shared CPU, 512 MB + 1 GB volume | approximately $3.50–$5+ (regional pricing and traffic vary) | Low baseline cost, HTTPS fly.dev hostname | Command-line setup, one-machine operations, physical volume tied to its host |
| Hetzner CX23 | €5.49+ excluding VAT/optional IPv4 (effective June 15 2026) | More VM resources | You administer a VPS, firewall, TLS and updates |
| Render | starter instance and persistent disk billed separately | Simple GitHub setup | More expensive than the above for an always-on SQLite app |

Official prices change: https://railway.com/pricing and https://fly.io/pricing/ .
Do not use ephemeral free hosting for participant data. Keep budget alerts enabled.

## Route A: Railway Hobby (recommended)

1. Use an account authorized to pay for the service, then sign in at https://railway.com/ .
2. In Railway, select **New Project → Deploy from GitHub repo**. Select
   `InitialTL/Lys-Omstendigheter-Og-Hukommelse` and choose branch
   `feature/hukommelse-lm-v2` in the source settings; the default/main branch
   may not contain the latest tested website. Set the service root directory
   to the **repository root**, where `Dockerfile` is located.
3. Add **one persistent volume**, attached to that service at mount path
   **`/data`**. Do this **before the first public deployment**. Use one replica,
   and keep the service awake throughout data collection. A missing volume makes
   this image refuse to start on Railway, preventing silent data loss.
4. In service **Variables**, set:

   ```text
   PORT=8000
   STUDY_DATABASE=/data/results.db
   STUDY_REQUIRE_PERSISTENT_VOLUME=1
   RAILWAY_RUN_UID=0
   STUDY_TRUST_CLOUDFLARE=0
   ```

   The `RAILWAY_RUN_UID=0` setting permits the startup script to take ownership
   of Railway's root-owned mounted volume. The startup script then launches
   Uvicorn as **UID 10001**, not root. This is intentional.
5. In **Settings → Networking → Public Networking**, choose **Generate Domain**.
   The app automatically allows the hostname in `RAILWAY_PUBLIC_DOMAIN`, if
   supplied by Railway. The domain is an HTTPS `*.up.railway.app` address.
   For a custom domain, additionally set:

   ```text
   STUDY_ALLOWED_HOSTS=localhost,127.0.0.1,your-real-study-domain.example
   ```

   Avoid `https://` or wildcard characters in `STUDY_ALLOWED_HOSTS`.
   Cross-origin requests are unnecessary because the site and API share an origin.
6. In **Settings → Healthcheck**, configure `/api/health`. Keep **restart on
   failure** enabled, set **region to Europe** (for Norwegian research data),
   and set **replicas = 1**. Railway's older `railway.toml` Config as Code has
   been deprecated for new services; configure the deployment settings in the
   Railway dashboard instead.
7. In the volume's **Backups** tab, enable at least **daily** backups. For
   off-provider copies, generate a consistent SQLite snapshot:

   ```sh
   railway ssh -- python /app/scripts/backup_sqlite.py /data/backups
   railway volume files list /backups
   railway volume files download /backups/<actual-backup-name>.db ./backup.db
   ```

   The bracketed name is a placeholder: use the filename printed by the backup
   tool, and keep downloaded copies private and encrypted. Test a restore
   before recruiting participants. Railway snapshots alone are not equivalent
   to independent off-provider backups.
8. Visit `https://<your-generated-hostname>/api/health` and confirm it returns
   `{"status":"ok"}` (with a software version). Open the main page in a
   private browser window and complete a **test** three-round session. Confirm
   results are saved, then exclude that pilot from your research analysis.
9. Set a **spending alert/limit** in Railway. Optional exports require a random
   secret `STUDY_ADMIN_TOKEN`; if absent, admin CSV endpoints are disabled.
   Generate it locally with
   `python -c "import secrets; print(secrets.token_urlsafe(48))"`, store in
   Railway's sealed variables, and never commit or share it.

**Cloudflare:** not required for the free Railway hostname; Railway already
handles public HTTPS. If you add a custom domain through Cloudflare, configure
DNS using the records Railway provides. Enable WAF/bot/rate rules for
`/api/participants`. Do **not** enable `STUDY_TRUST_CLOUDFLARE=1` on Railway:
the public Railway origin could still be accessed directly. Avoid a
Cloudflare Tunnel; that is intended for private, self-hosted origins.

**Existing local results:** the repository and downloaded ZIP do not contain
`results.db`. If you need to migrate local pilot data, first stop local writes
and use `python scripts/backup_sqlite.py <private-directory>` with the correct
`STUDY_DATABASE`. Transfer the resulting **consistent snapshot** to an empty
cloud volume *before* admitting participants. Never replace a live cloud DB or
copy its `results.db` file alone while WAL is active. If you already have cloud
participants, do not overwrite the database; plan a careful migration.

## Route B: Fly.io (lower-cost alternative)

Fly.io is less convenient but has a smaller baseline hosting cost for a single
Machine. **One volume means one Machine**: never deploy two independent SQLite
writers, and do not use Fly's default high-availability 2-Machine deployment.

1. Install `flyctl` on Windows PowerShell using the command in Fly's official
   documentation: https://fly.io/docs/flyctl/install/ . Sign in using
   `fly auth login`.
2. Create a unique app name (letters, numbers and hyphens), then create the app:

   ```powershell
   fly apps create your-unique-study-name
   ```

3. Edit `fly.toml` and replace `replace-with-your-unique-study-name` with your
   actual app name. Keep region `ams` (Amsterdam) and `memory = "512mb"`.
4. Create exactly one **encrypted persistent 1 GB volume** in that region:

   ```powershell
   fly volumes create study_data --app your-unique-study-name --region ams --size 1 --yes
   ```

5. Deploy **one** Machine, not the default pair:

   ```powershell
   fly deploy --app your-unique-study-name --ha=false
   fly status --app your-unique-study-name
   ```

   Ensure that there is one Machine and its `study_data` volume is attached.
   Your free provider hostname will be
   `https://your-unique-study-name.fly.dev`.
6. The app automatically allows that `*.fly.dev` hostname when `FLY_APP_NAME`
   is supplied. For a custom hostname, add `STUDY_ALLOWED_HOSTS` using
   `fly secrets set STUDY_ALLOWED_HOSTS=localhost,127.0.0.1,your.domain`.
   If you want admin CSV exports, store the token with `fly secrets set`.
7. Check `/api/health`, complete a pilot, monitor usage, and create separate
   SQLite backups with `fly ssh console` plus the backup script. Do not depend
   only on provider volume snapshots or assume regional HA for one Machine.

## Mandatory operational decisions (both platforms)

* **Never deploy without `/data` mounted.** The startup script refuses to run
  on managed platforms when the volume is absent; your results would otherwise
  disappear after a release.
* Use only **one** writable service instance for SQLite, with a single
  Uvicorn worker. Keep the app awake during your study.
* Deploy updates between participant sessions where practical. A rolling
  restart can interrupt someone currently answering; the existing draft
  checkpoints reduce data loss but cannot guarantee lossless recovery.
* Configure a privacy statement, a retention/deletion policy and a lawful
  basis for processing research data, especially for participants under 18.
  Ensure the chosen provider's data processing terms meet the school's policy.
* **Never expose an admin token in browser JavaScript**, GitHub commits, screenshots
  or public URLs. Prefer sealed variables and authenticated management access.
* Verify the experiment on representative phones and laptops before public
  distribution, then freeze protocol 2.7. Test runs should be labeled pilots.

## Updating the deployed code

Railway: push commits to `feature/hukommelse-lm-v2` if GitHub autodeploy is
configured, or deploy explicitly through its dashboard.
Fly.io: from the repository root, run
`fly deploy --app your-unique-study-name --ha=false` after reviewing changes.
The database volume survives these app updates; deleting the app or volume is
not an update and can permanently remove data.

### Data and participant continuity checklist

* Deploy to the **existing app**, with `study_data` still attached to `/data`.
  Keep `STUDY_DATABASE=/data/results.db` and a single writable Machine.
* Do not remove or replace the volume, deploy to a different application,
  or clear the existing participant tables on startup.
* The browser retains `lm_v2_participant` and `lm_v2_auth` in localStorage.
  After reload, it queries the server's authoritative round state, so a
  completed participant returns to the results screen, never a new enrollment.
* A finished participant cannot start or submit more study rounds with the
  existing identity. Consent withdrawal permanently deletes the old identity
  and its records, permitting a new registration from that browser.
* This is **one session per browser storage**, not guaranteed one person:
  private mode, clearing storage or another device can create a new session.
  Strict one-person eligibility would require distinct authenticated invitations.
* Roll out updates between participant sessions and verify backups first.
  In-progress deadlines still run during deployment, even when the website is
  temporarily unreachable.
