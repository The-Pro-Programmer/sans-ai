"""Whisper-based speech-to-text wrapper.

Uses OpenAI Whisper via the Emergent universal key (emergentintegrations).
The frontend sends short audio clips (webm / mp3 / wav) — we transcribe them
as Hindi/Devanagari because Whisper doesn't list classical Sanskrit; Hindi
produces the closest Devanagari output for chanted shlokas.
"""
from __future__ import annotations

import io
import os
from typing import BinaryIO

from emergentintegrations.llm.openai import OpenAISpeechToText


_stt: OpenAISpeechToText | None = None


def _client() -> OpenAISpeechToText:
    global _stt
    if _stt is None:
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise RuntimeError("EMERGENT_LLM_KEY is not configured")
        _stt = OpenAISpeechToText(api_key=api_key)
    return _stt


async def transcribe_bytes(
    audio_bytes: bytes,
    filename: str = "audio.webm",
    language: str = "hi",
) -> str:
    """Transcribe a raw audio blob and return the Devanagari text."""
    buf = io.BytesIO(audio_bytes)
    buf.name = filename  # the SDK uses this to infer content-type
    response = await _client().transcribe(
        file=buf,
        model="whisper-1",
        response_format="json",
        language=language,
        prompt="संस्कृत श्लोकः। देवनागरी लिपौ।",  # guides toward Devanagari output
        temperature=0.0,
    )
    text = getattr(response, "text", None) or (
        response.get("text") if isinstance(response, dict) else ""
    )
    return (text or "").strip()
