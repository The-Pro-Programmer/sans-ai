"""Sanskrit translator with hybrid correction-first + LLM fallback strategy.

Flow for every translate request:
    1. Normalize the input text.
    2. Look up an exact match in the correction store (corrections.json).
       If found -> return it with a perfect confidence score (source='correction').
    3. Otherwise call the LLM (Claude Sonnet 4.5 via Emergent LLM key) with a
       strict JSON contract and return the parsed translation + confidence
       (source='llm').
"""
from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from emergentintegrations.llm.chat import LlmChat, UserMessage

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
CORRECTIONS_FILE = DATA_DIR / "corrections.json"
HISTORY_FILE = DATA_DIR / "history.json"

LANG_NAMES = {
    "marathi": "Marathi (मराठी)",
    "hindi": "Hindi (हिन्दी)",
    "english": "English",
}


# ---------- tiny JSON file store ----------

def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _correction_key(text: str, lang: str) -> str:
    return f"{lang.lower()}::{_normalize(text)}"


# ---------- corrections store ----------

def load_corrections() -> Dict[str, Dict[str, Any]]:
    return _read_json(CORRECTIONS_FILE, {})


def save_correction(sanskrit_text: str, target_lang: str, corrected_text: str) -> None:
    corrections = load_corrections()
    key = _correction_key(sanskrit_text, target_lang)
    corrections[key] = {
        "sanskrit_text": _normalize(sanskrit_text),
        "target_lang": target_lang.lower(),
        "corrected_text": corrected_text.strip(),
    }
    _write_json(CORRECTIONS_FILE, corrections)


def get_correction(sanskrit_text: str, target_lang: str) -> Optional[str]:
    corrections = load_corrections()
    entry = corrections.get(_correction_key(sanskrit_text, target_lang))
    return entry["corrected_text"] if entry else None


# ---------- history store ----------

def load_history(limit: int = 100) -> list:
    history = _read_json(HISTORY_FILE, [])
    return history[:limit]


def append_history(item: Dict[str, Any]) -> None:
    history = _read_json(HISTORY_FILE, [])
    history.insert(0, item)
    # cap history to 200 entries
    _write_json(HISTORY_FILE, history[:200])


def update_history_feedback(item_id: str, feedback: str, correction: Optional[str] = None) -> Optional[Dict[str, Any]]:
    history = _read_json(HISTORY_FILE, [])
    updated = None
    for entry in history:
        if entry.get("id") == item_id:
            entry["feedback"] = feedback
            if correction is not None:
                entry["correction"] = correction
            updated = entry
            break
    if updated is not None:
        _write_json(HISTORY_FILE, history)
    return updated


def clear_history() -> None:
    _write_json(HISTORY_FILE, [])


# ---------- LLM translation ----------

SYSTEM_PROMPT = (
    "You are a scholarly translator specialised in classical Sanskrit "
    "(Devanagari script). Given a Sanskrit source, produce a faithful, "
    "natural translation into the requested target language. "
    "Return ONLY a compact JSON object with keys: "
    "`translation` (string, the translated text, no extra commentary) and "
    "`confidence` (number between 0 and 100 representing how confident you are). "
    "Base confidence on textual clarity, ambiguity, and your familiarity with "
    "the vocabulary. Never include markdown fences or any other keys."
)


def _extract_json(raw: str) -> Dict[str, Any]:
    # strip code fences if present
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    # try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # fallback: find first {...} block
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {"translation": cleaned, "confidence": 50}


async def llm_translate(sanskrit_text: str, target_lang: str) -> Dict[str, Any]:
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise RuntimeError("EMERGENT_LLM_KEY is not configured")

    target_label = LANG_NAMES.get(target_lang.lower(), target_lang)

    chat = (
        LlmChat(
            api_key=api_key,
            session_id=f"sanskrit-translate-{uuid.uuid4()}",
            system_message=SYSTEM_PROMPT,
        )
        .with_model("anthropic", "claude-sonnet-4-5-20250929")
    )

    prompt = (
        f"Sanskrit source:\n{sanskrit_text}\n\n"
        f"Translate into {target_label}. Respond with the JSON object only."
    )
    response = await chat.send_message(UserMessage(text=prompt))
    data = _extract_json(response if isinstance(response, str) else str(response))

    translation = str(data.get("translation", "")).strip()
    try:
        confidence = float(data.get("confidence", 75))
    except (TypeError, ValueError):
        confidence = 75.0
    confidence = max(0.0, min(100.0, confidence))

    return {"translation": translation, "confidence": confidence}


async def translate(sanskrit_text: str, target_lang: str) -> Dict[str, Any]:
    """Hybrid translate: correction override first, LLM fallback."""
    target_lang = target_lang.lower()
    override = get_correction(sanskrit_text, target_lang)
    if override is not None:
        return {
            "translation": override,
            "confidence": 100.0,
            "source": "correction",
        }

    result = await llm_translate(sanskrit_text, target_lang)
    result["source"] = "llm"
    return result
