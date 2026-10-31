# Security and privacy deployment checklist

This is a small research application, not a security-certified service. **No web
app is unhackable**. Cloudflare is useful, but it cannot compensate for exposing
an insecure origin, poor credentials, or an unpatched operating system.

## Safe Raspberry Pi 3 architecture

Build the React frontend in GitHub Actions or a development computer; run **only
Uvicorn + SQLite + compiled static files** on the Pi. A 64-bit Raspberry Pi OS
installation is recommended for currently maintained Python packages. Do not
install Node or run Vite in production.

Internet → Cloudflare Tunnel (HTTPS) → `127.0.0.1:8000` → one Uvicorn process →
SQLite database on a persistent volume. Configure the local firewall so port
8000 is **not** reachable from your LAN or the internet. Docker Compose binds
`127.0.0.1:8000`, runs the code read-only, mounts only the database directory
for writing, caps memory at 384 MiB and starts only one worker.

Set these private environment values **before** opening registrations:

```dotenv
STUDY_ADMIN_TOKEN=replace-with-at-least-32-random-bytes
STUDY_ALLOWED_HOSTS=study.example.org,localhost,127.0.0.1
STUDY_ALLOWED_ORIGINS=https://study.example.org
STUDY_TRUST_CLOUDFLARE=1
```

`STUDY_TRUST_CLOUDFLARE=1` is safe only when the application receives requests
**exclusively from a local Cloudflare Tunnel**. Without this guarantee, leave it
`0`, because clients can spoof `CF-Connecting-IP`. Never expose Uvicorn to the
internet with an open `0.0.0.0:8000` port. Use Cloudflare Access for the admin
interface if you add one; the current app has **no public admin UI**.

Generate the admin secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
Never put the admin token in browser JavaScript, Git, screenshots, URLs or logs.

## Application defenses

* Separate 256-bit random participant bearer token; only its SHA-256 digest is
  stored in SQLite. Participant UUID is not an authorization credential.
* Origin checks for browser writes, strict Host allow-list, no permissive CORS,
  API requests without caches, no external JS or trackers.
* Content Security Policy for the production SPA, clickjacking prevention,
  MIME sniffing prevention, restrictive browser permissions.
* API JSON bodies are capped at 8 KiB: the origin checks `Content-Length` and
  independently stops reading streamed/chunked bodies that exceed the cap.
  **Additionally enforce rate limits, request size and timeouts at Cloudflare
  or a reverse proxy**; an attacker can still exhaust slow connections before
  an application-level parser gets control.
* Registration rate limit is per process and per client IP (30 in 10 minutes).
  This is only a supplementary control; add Cloudflare WAF/bot rules and overall
  rate limiting. Do not treat it as DoS protection.
* SQLite uses parameterized statements, write transactions, foreign keys, a
  small page cache and WAL checkpoints. Database files must remain outside Git.
* Withdrawal requires the participant secret. Save encrypted backups, test
  recovery and define deletion/retention periods before collecting real data.

## Operational rules

1. Patch Raspberry Pi OS, Cloudflare Tunnel and pinned Python/Node dependencies
   regularly. Check GitHub Actions and run the test suite before deployment.
2. Disable development mode, `--reload`, and API debug docs in production.
3. Keep the database directory writable only by the application process.
4. Periodically back up SQLite **using SQLite's backup API** or stop the app
   before copying; copying only `.db` while WAL is active can lose recent data.
5. Restrict administrative CSV exports to the server or a protected tunnel.
6. Use a long secret in `STUDY_ADMIN_TOKEN`; leave export disabled otherwise.
7. Collect no names, emails or precise addresses. Keep raw answers out of
   GitHub, shared drives and public charts.
8. Check legal/ethical obligations for minors, local data protection, and
   consent before recruiting publicly.

## Security limitations

Tokens in `localStorage` can be stolen if same-origin JavaScript is compromised;
CSP and dependency review reduce but do not eliminate XSS risk. Cloudflare
helps with internet-origin threats, not malicious code, stolen admin credentials,
local malware, physical device compromise or denial of service against the Pi.
Manual penetration testing and an actual deployment audit are still required.
