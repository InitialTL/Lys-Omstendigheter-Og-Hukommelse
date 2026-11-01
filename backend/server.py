"""Hukommelse LM – React client and FastAPI study server."""
from __future__ import annotations
import csv
import json
import ipaddress
import io
import os
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.routing import APIRoute
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, ConfigDict

import database
import words

app = FastAPI(title="Hukommelse LM API", version="2.5.0", docs_url=None, redoc_url=None)

# A publicly reachable origin must be placed behind HTTPS and a firewall or
# Cloudflare Tunnel. Never accept arbitrary Host headers on the origin.
_hosts = [host.strip() for host in os.getenv(
    "STUDY_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver,::1"
).split(",") if host.strip()]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_hosts)

# API requests only contain tiny JSON payloads. Reject oversized bodies at
# the origin as well as at the reverse proxy (see deployment guide).
MAX_API_BODY = 8192


class LimitedJSONRoute(APIRoute):
    """Bound actual streamed bytes, including chunked requests with no length."""

    def get_route_handler(self):
        original = super().get_route_handler()

        async def bounded(request: Request):
            if request.url.path.startswith('/api/') and request.method not in ('GET', 'HEAD'):
                chunks = []
                total = 0
                async for chunk in request.stream():
                    total += len(chunk)
                    if total > MAX_API_BODY:
                        raise HTTPException(status_code=413, detail='Request is too large')
                    chunks.append(chunk)
                # Starlette/FastAPI reads request.body() during validation; after
                # consuming the bounded stream, supply the same bytes from RAM.
                request._body = b''.join(chunks)
            return await original(request)

        return bounded


app.router.route_class = LimitedJSONRoute
_dev_origins = {"http://localhost:5173", "http://127.0.0.1:5173",
                "http://localhost:8000", "http://127.0.0.1:8000"}
_allowed_origins = _dev_origins | {
    origin.strip().rstrip("/") for origin in os.getenv("STUDY_ALLOWED_ORIGINS", "").split(",") if origin.strip()
}


# Lightweight per-process guard against bulk account creation. In a public
# deployment, additionally enforce rate limits at the reverse proxy.
_registration_times: dict[str, deque[float]] = defaultdict(deque)

@app.middleware("http")
async def safe_response_headers(request: Request, call_next):
    from fastapi.responses import JSONResponse
    path = request.url.path
    if path.startswith('/api/'):
        if request.method not in ('GET', 'HEAD', 'OPTIONS'):
            origin = request.headers.get('origin')
            # Browsers supply Origin for writes; non-browser clients may omit it.
            # Authenticated actions still require the independent bearer token.
            # On a single-origin deployment, a trusted Host plus matching
            # Origin is sufficient; the port is allowed to vary between
            # local test instances. Cross-origin development needs an explicit
            # allowlist entry. TrustedHostMiddleware validates this Host.
            same_origin_host = request.headers.get('host', '')
            same_site = origin in (f'http://{same_origin_host}', f'https://{same_origin_host}')
            if origin and not same_site and origin.rstrip('/') not in _allowed_origins:
                return JSONResponse({'detail':'Origin not allowed'}, status_code=403)
        raw_length = request.headers.get('content-length')
        if raw_length:
            try:
                if int(raw_length) > MAX_API_BODY:
                    return JSONResponse({'detail':'Request is too large'}, status_code=413)
            except ValueError:
                return JSONResponse({'detail':'Invalid Content-Length'}, status_code=400)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    # Vite's development server requires an HMR-specific CSP; restrict only
    # static production responses served by FastAPI here.
    elif DIST.exists():
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        )
    return response

database.init_db()


class Registration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: Literal["nb", "en", "sv", "de", "fr", "es", "it", "pt", "nl", "da", "pl", "ro"]
    age_band: Literal["16_17", "18_24", "25_44", "45_plus", "prefer_not"]
    gender: Literal["woman", "man", "nonbinary", "other", "prefer_not"]
    consent: Literal[True]


class Submission(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answers: list[str] = Field(min_length=8, max_length=8)
    hidden_count: int = Field(default=0, ge=0, le=10000)
    math_attempts: int = Field(default=0, ge=0, le=100)
    math_correct: int = Field(default=0, ge=0, le=100)


def authorize(participant_id: str, token: str | None) -> None:
    if not database.verify_token(participant_id, token):
        # Identical error for missing IDs, stale protocol and invalid secrets.
        raise HTTPException(status_code=401, detail="Invalid or expired participant session")


def build_state(participant_id: str) -> dict:
    data = database.get_next(participant_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Unknown participant")
    # The shuffles are server-side, persisted, and hidden from unrelated phases.
    learning_order = data.pop("learning_order", None)
    recall_order = data.pop("recall_order", None)
    if data["finished"]:
        # Review is released ONLY after all three rounds are submitted.
        # This prevents knowledge of correct answers contaminating later rounds.
        rounds = database.completed_rounds(participant_id)
        if rounds:
            data['review'] = [
                {
                    'round_index': r['round_index'],
                    'condition': r['condition'],
                    'score': r['score'],
                    'max_score': r['max_score'],
                    'math_attempts': r['math_attempts'],
                    'math_correct': r['math_correct'],
                    'items': words.answer_review(r['list_id'], r['language'],
                            json.loads(r['answers']),
                            json.loads(r['recall_order'])),
                } for r in rounds
            ]
    else:
        data["words"] = words.recall_words(data["list_id"], recall_order) if data["phase"] == "recall" else []
        if data["phase"] == "learning":
            data["pairs"] = words.learning_pairs(data["list_id"], data["language"], learning_order)
    return data


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.5.0"}


@app.get("/api/config")
def config():
    return {
        "conditions": {
            "ORANGE": {"hex": "#F0A34B", "label": "orange"},
            "BLUE": {"hex": "#8AB7EA", "label": "blue"},
            "NEUTRAL": {"hex": "#B3B3B3", "label": "neutral gray"},
        },
        "learning_seconds": database.LEARN_SECONDS,
        "distraction_seconds": database.DISTRACT_SECONDS,
        "recall_seconds": database.RECALL_SECONDS,
        "acclimation_seconds": database.ACCLIMATION_SECONDS,
        "words_per_round": database.WORDS_PER_ROUND,
        "rounds": 3,
        "measurement": "Backgrounds matched approximately for calculated sRGB relative luminance (~0.45); not physically calibrated, nor matched for perceived brightness, Kelvin or lux",
    }


@app.post("/api/participants", status_code=201)
def register(payload: Registration, request: Request):
    # IPs are held in RAM for at most ten minutes, never written to the DB.
    ip = request.client.host if request.client else "unknown"
    # Only accept Cloudflare's client IP when explicitly enabled AND the origin
    # is accessible solely via a local Cloudflare Tunnel / trusted proxy.
    # Never trust this header when the origin can be reached directly.
    if (os.getenv("STUDY_TRUST_CLOUDFLARE") == "1" and ip in ("127.0.0.1", "::1")):
        claimed = request.headers.get("CF-Connecting-IP", "")
        try:
            ip = str(ipaddress.ip_address(claimed))
        except ValueError:
            ip = "unknown"
    now = time.monotonic()
    times = _registration_times[ip]
    while times and times[0] < now - 600:
        times.popleft()
    if len(times) >= 30:
        raise HTTPException(status_code=429, detail="Too many registrations; please try again later")
    times.append(now)
    if len(_registration_times) > 4000:
        for key in list(_registration_times):
            if not _registration_times[key] or _registration_times[key][-1] < now - 600:
                del _registration_times[key]
    return database.create_participant(payload.language, payload.age_band, payload.gender)


@app.get("/api/participants/{participant_id}/next")
def next_round(participant_id: str, x_participant_token: str | None = Header(default=None)):
    authorize(participant_id, x_participant_token)
    return build_state(participant_id)


@app.post("/api/participants/{participant_id}/rounds/start")
def start_round(participant_id: str, x_participant_token: str | None = Header(default=None)):
    authorize(participant_id, x_participant_token)
    state = database.start_round(participant_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Unknown participant")
    if state["finished"]:
        raise HTTPException(status_code=409, detail="Study completed")
    return build_state(participant_id)


@app.post("/api/participants/{participant_id}/rounds/{round_index}/submit")
def submit(participant_id: str, round_index: int, submission: Submission,
           x_participant_token: str | None = Header(default=None)):
    authorize(participant_id, x_participant_token)
    if not 0 <= round_index < 3:
        raise HTTPException(status_code=404, detail="Unknown round")
    if any(len(answer) > 80 for answer in submission.answers):
        raise HTTPException(status_code=422, detail="Answers must be at most 80 characters")
    state = database.get_next(participant_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Unknown participant")
    if state["finished"] or state["round_index"] != round_index:
        raise HTTPException(status_code=409, detail="Round already completed or out of order")
    # Check phase again on the server, never trust timers sent from the browser.
    if state["phase"] != "recall":
        raise HTTPException(status_code=409, detail="Recall has not started")
    language = state["language"]
    if submission.math_correct > submission.math_attempts:
        raise HTTPException(status_code=422, detail="Impossible arithmetic totals")
    score, _ = words.grade(state["list_id"], language, submission.answers, state["recall_order"])
    try:
        return database.save_result(participant_id, round_index, submission.answers,
                                    submission.hidden_count, score,
                                    submission.math_attempts, submission.math_correct)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=f"Cannot submit round: {exc}") from exc


@app.delete("/api/participants/{participant_id}", status_code=204)
def withdraw(participant_id: str, x_participant_token: str | None = Header(default=None)):
    authorize(participant_id, x_participant_token)
    if not database.delete_participant(participant_id):
        raise HTTPException(status_code=404, detail="Unknown participant")
    return Response(status_code=204)


@app.get("/api/admin/export.csv")
def admin_export(x_admin_token: str | None = Header(default=None)):
    expected = os.getenv("STUDY_ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Admin export is not configured")
    if not x_admin_token or not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=403, detail="Forbidden")
    fields = ["participant_id", "language", "age_band", "gender", "protocol_version", "group_name", "list_order",
              "created_at", "round_index", "condition", "list_id", "answers", "score",
              "max_score", "recall_seconds", "hidden_count", "submitted_late", "math_attempts", "math_correct", "completed_at"]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    writer.writerows(database.export_rows())
    return Response(out.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=study_results.csv",
                             "Cache-Control": "no-store"})


# After `npm run build`, FastAPI can also serve the frontend from one origin.
DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if DIST.exists():
    assets = DIST / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/")
    def index():
        return FileResponse(DIST / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        target = DIST / full_path
        if target.is_file() and DIST.resolve() in target.resolve().parents:
            return FileResponse(target)
        return FileResponse(DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
