"""Hukommelse LM – React client and FastAPI study server."""
from __future__ import annotations
import csv
import io
import os
import secrets
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import database
import words

app = FastAPI(title="Hukommelse LM API", version="2.0.0", docs_url=None, redoc_url=None)
database.init_db()


class Registration(BaseModel):
    language: Literal["nb", "en"]
    age_band: Literal["16_17", "18_24", "25_44", "45_plus", "prefer_not"]
    gender: Literal["woman", "man", "nonbinary", "other", "prefer_not"]
    consent: Literal[True]


class Submission(BaseModel):
    answers: list[str] = Field(min_length=10, max_length=10)
    hidden_count: int = Field(default=0, ge=0, le=10000)


def build_state(participant_id: str) -> dict:
    data = database.get_next(participant_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Unknown participant")
    if not data["finished"]:
        data["words"] = words.recall_words(data["list_id"]) if data["phase"] == "recall" else []
        # Correct answers are NEVER included in recall/setup responses.
        if data["phase"] == "learning":
            data["pairs"] = words.learning_pairs(data["list_id"], data["language"])
    return data


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/api/config")
def config():
    return {
        "conditions": {
            "WARM": {"hex": "#D9AA91", "label": "warm"},
            "COOL": {"hex": "#9BB6E4", "label": "cool"},
            "DARK": {"hex": "#080B11", "label": "dark"},
        },
        "learning_seconds": database.LEARN_SECONDS,
        "distraction_seconds": database.DISTRACT_SECONDS,
        "recall_seconds": database.RECALL_SECONDS,
        "acclimation_seconds": database.ACCLIMATION_SECONDS,
        "words_per_round": 10,
        "rounds": 3,
        "measurement": "Screen background sRGB values; not calibrated Kelvin or lux",
    }


@app.post("/api/participants", status_code=201)
def register(payload: Registration):
    return database.create_participant(payload.language, payload.age_band, payload.gender)


@app.get("/api/participants/{participant_id}/next")
def next_round(participant_id: str):
    return build_state(participant_id)


@app.post("/api/participants/{participant_id}/rounds/start")
def start_round(participant_id: str):
    state = database.start_round(participant_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Unknown participant")
    if state["finished"]:
        raise HTTPException(status_code=409, detail="Study completed")
    return build_state(participant_id)


@app.post("/api/participants/{participant_id}/rounds/{round_index}/submit")
def submit(participant_id: str, round_index: int, submission: Submission):
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
    score, _ = words.grade(state["list_id"], language, submission.answers)
    try:
        return database.save_result(participant_id, round_index, submission.answers,
                                    submission.hidden_count, score)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=f"Cannot submit round: {exc}") from exc


@app.delete("/api/participants/{participant_id}", status_code=204)
def withdraw(participant_id: str):
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
    fields = ["participant_id", "language", "age_band", "gender", "group_name", "list_order",
              "created_at", "round_index", "condition", "list_id", "answers", "score",
              "max_score", "recall_seconds", "hidden_count", "submitted_late", "completed_at"]
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
