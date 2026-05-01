"""FastAPI backend for the Sanskrit -> Marathi / Hindi / English translator.

Storage is JSON-file based (per user choice): corrections.json + history.json.
All routes are mounted under /api.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from translator import (  # noqa: E402  (load env first)
    append_history,
    clear_history,
    get_correction,
    load_corrections,
    load_history,
    save_correction,
    translate,
)

app = FastAPI(title="Sanskrit Translator API", version="1.0.0")
api_router = APIRouter(prefix="/api")

Language = Literal["marathi", "hindi", "english"]
SUPPORTED_LANGS: List[Language] = ["marathi", "hindi", "english"]


# ---------- models ----------

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    target_langs: Optional[List[Language]] = None  # default: all three


class TranslationResult(BaseModel):
    language: Language
    translation: str
    confidence: float
    source: Literal["correction", "llm"]


class HistoryItem(BaseModel):
    id: str
    sanskrit_text: str
    results: List[TranslationResult]
    feedback: dict = Field(default_factory=dict)  # lang -> "up" | "down"
    corrections: dict = Field(default_factory=dict)  # lang -> corrected string
    timestamp: str


class TranslateResponse(BaseModel):
    id: str
    sanskrit_text: str
    results: List[TranslationResult]
    timestamp: str


class FeedbackRequest(BaseModel):
    item_id: str
    language: Language
    is_correct: bool
    correction: Optional[str] = None


# ---------- routes ----------

@api_router.get("/")
async def root():
    return {"message": "Sanskrit Translator API", "status": "ok"}


@api_router.get("/health")
async def health():
    key_present = bool(os.environ.get("EMERGENT_LLM_KEY"))
    return {"status": "ok", "llm_configured": key_present}


@api_router.post("/translate", response_model=TranslateResponse)
async def api_translate(req: TranslateRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Sanskrit text is required")

    langs: List[Language] = req.target_langs or list(SUPPORTED_LANGS)
    # dedupe while preserving order
    seen = set()
    langs = [lang for lang in langs if not (lang in seen or seen.add(lang))]

    results: List[TranslationResult] = []
    for lang in langs:
        try:
            out = await translate(text, lang)
        except Exception as e:  # surface a per-language error as low-confidence
            logging.exception("translation failed for %s", lang)
            results.append(TranslationResult(
                language=lang,
                translation=f"[Translation failed: {e}]",
                confidence=0.0,
                source="llm",
            ))
            continue
        results.append(TranslationResult(
            language=lang,
            translation=out["translation"],
            confidence=round(float(out["confidence"]), 1),
            source=out["source"],
        ))

    item = {
        "id": str(uuid.uuid4()),
        "sanskrit_text": text,
        "results": [r.model_dump() for r in results],
        "feedback": {},
        "corrections": {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    append_history(item)

    return TranslateResponse(
        id=item["id"],
        sanskrit_text=item["sanskrit_text"],
        results=results,
        timestamp=item["timestamp"],
    )


from translator import _read_json, _write_json, HISTORY_FILE  # noqa: E402


def _persist_feedback(item_id: str, language: str, vote: str, correction: Optional[str]) -> Optional[dict]:
    history = _read_json(HISTORY_FILE, [])
    updated = None
    for entry in history:
        if entry.get("id") == item_id:
            entry.setdefault("feedback", {})[language] = vote
            if correction is not None:
                entry.setdefault("corrections", {})[language] = correction
            updated = entry
            break
    if updated is not None:
        _write_json(HISTORY_FILE, history)
    return updated


# Re-bind the richer feedback route (keeps the top-level model contract intact)
@api_router.post("/feedback")
async def api_feedback(req: FeedbackRequest):
    history = load_history(limit=500)
    match = next((h for h in history if h.get("id") == req.item_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="Translation not found")

    if req.is_correct:
        item = _persist_feedback(req.item_id, req.language, "up", None)
        return {"ok": True, "stored_correction": False, "item": item}

    if not req.correction or not req.correction.strip():
        raise HTTPException(status_code=400, detail="Correction text required for negative feedback")

    save_correction(match["sanskrit_text"], req.language, req.correction.strip())
    item = _persist_feedback(req.item_id, req.language, "down", req.correction.strip())
    return {"ok": True, "stored_correction": True, "item": item}


# Alias kept for the frontend which calls /feedback/v2
@api_router.post("/feedback/v2")
async def api_feedback_v2(req: FeedbackRequest):
    return await api_feedback(req)


@api_router.get("/history")
async def api_history(limit: int = 50):
    return {"items": load_history(limit=limit)}


@api_router.delete("/history")
async def api_clear_history():
    clear_history()
    return {"ok": True}


@api_router.get("/corrections")
async def api_corrections():
    corrections = load_corrections()
    return {"count": len(corrections), "items": list(corrections.values())}


@api_router.get("/corrections/check")
async def api_corrections_check(text: str, language: Language):
    value = get_correction(text, language)
    return {"has_override": value is not None, "correction": value}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
