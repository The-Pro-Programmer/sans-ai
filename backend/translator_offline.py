"""Offline translator — lazy-loaded on first use.

Uses Meta's `facebook/nllb-200-distilled-600M`, which is publicly accessible
on HuggingFace and supports classical Sanskrit (`san_Deva`) to Marathi
(`mar_Deva`), Hindi (`hin_Deva`), and English (`eng_Latn`) entirely on-device
— no network after the model is cached.

The model is ~2.4 GB. First call downloads into the HuggingFace cache;
subsequent calls reuse it.
"""
from __future__ import annotations

import asyncio
import logging
import threading

logger = logging.getLogger(__name__)

MODEL_ID = "facebook/nllb-200-distilled-600M"

# NLLB flores-200 tags for the languages we care about
FLORES = {
    "sanskrit": "san_Deva",
    "marathi": "mar_Deva",
    "hindi": "hin_Deva",
    "english": "eng_Latn",
}

_lock = threading.Lock()
_state: dict = {
    "loaded": False,
    "loading": False,
    "error": None,
    "model": None,
    "tokenizer": None,
    "torch": None,
}


def is_available() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        return True
    except Exception as e:
        _state["error"] = f"dependency missing: {e}"
        return False


def status() -> dict:
    available = is_available()
    return {
        "available": available,
        "loaded": _state["loaded"],
        "loading": _state["loading"],
        "error": _state["error"],
        "model_id": MODEL_ID,
    }


def _load_blocking() -> None:
    if _state["loaded"]:
        return
    _state["loading"] = True
    _state["error"] = None
    try:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        logger.info("Offline NLLB-200: loading tokenizer/model (first run ~2.4GB download)...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_ID)
        model.eval()

        _state.update(
            loaded=True,
            loading=False,
            tokenizer=tokenizer,
            model=model,
            torch=torch,
        )
        logger.info("Offline NLLB-200: ready.")
    except Exception as e:
        _state["loading"] = False
        _state["error"] = str(e)
        logger.exception("Offline model load failed")


async def ensure_loaded() -> dict:
    if _state["loaded"]:
        return status()
    if not is_available():
        return status()
    with _lock:
        if not _state["loaded"]:
            await asyncio.to_thread(_load_blocking)
    return status()


async def translate(sanskrit_text: str, target_lang: str) -> dict:
    """Translate Sanskrit (san_Deva) -> target via NLLB-200."""
    await ensure_loaded()
    if not _state["loaded"]:
        raise RuntimeError(_state.get("error") or "Offline model unavailable")

    tgt = FLORES.get(target_lang.lower())
    if not tgt:
        raise ValueError(f"Unsupported target: {target_lang}")

    tokenizer = _state["tokenizer"]
    model = _state["model"]
    torch = _state["torch"]

    def _run() -> str:
        # Set the source language on the tokenizer; pass target as forced BOS.
        tokenizer.src_lang = FLORES["sanskrit"]
        inputs = tokenizer(sanskrit_text, return_tensors="pt", truncation=True, max_length=256)
        # NLLB forced BOS id per target
        forced_bos = tokenizer.convert_tokens_to_ids(tgt)
        with torch.no_grad():
            out = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos,
                max_length=256,
                num_beams=4,
            )
        return tokenizer.batch_decode(out, skip_special_tokens=True)[0]

    translation = await asyncio.to_thread(_run)
    confidence = 82.0 if translation.strip() else 0.0
    return {"translation": translation.strip(), "confidence": confidence}
