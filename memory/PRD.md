# Antarvāṇī – Sanskrit Translator

## Problem statement (verbatim)

Build a full-stack, locally runnable web application that translates Sanskrit
text into Marathi, Hindi, and English, with user feedback-based continuous
learning. Accept Devanagari input, provide translations with confidence score,
thumbs-up/-down + correction capture, translation history, copy-to-clipboard,
dark mode. Hybrid approach: check a local correction store first, fall back to
an LLM. Storage must be local.

## User choices captured (Feb 2026)

- Translation engine: **Hybrid** – correction-first, LLM fallback.
- Local DB: **JSON files** (no MongoDB).
- LLM key: **Emergent Universal LLM key** (Claude Sonnet 4.5).
- Optional features: **All** (history, copy-to-clipboard, dark mode).
- Design: **Modern UI with Indic / Sanskrit aesthetic touches**.

## Architecture

- React 19 frontend (Tailwind + Shadcn UI, lucide-react, sonner).
- FastAPI backend at `/api/*`.
- `backend/translator.py` – JSON correction store + LLM via
  emergentintegrations.
- `backend/data/corrections.json`, `backend/data/history.json` – local stores.

## Personas

- **Sanskrit student / practitioner** – wants accurate Marathi / Hindi /
  English renderings of shlokas and sutras.
- **Pandit / domain expert** – corrects translations, teaching the system
  over time.

## Implemented (2026-02)

- `POST /api/translate` multi-language response with confidence + source
  (`correction` | `llm` | `offline`). Request accepts optional
  `offline_mode: bool` to route through on-device NLLB-200.
- `POST /api/feedback/v2` captures 👍 / 👎 + corrections and persists the
  override.
- `GET/DELETE /api/history` with rich items incl. feedback map.
- `GET /api/corrections` and `GET /api/corrections/check`.
- `POST /api/transcribe` — Whisper-1 speech-to-text (via Emergent LLM key)
  accepting webm/mp3/wav up to 25 MB, Hindi/Devanagari prompt bias.
- `GET /api/offline/status`, `POST /api/offline/warmup` — on-device engine
  status + lazy model loader (first call downloads ~2.4 GB into
  `~/.cache/huggingface`).
- Single-page UI: asymmetric 12-col bento grid, Indic light / jewel dark
  themes, sticky glass header with history drawer + theme toggle.
- Translation cards with confidence progress bar, copy button, thumbs up/down,
  inline correction composer, `learned` / `on-device` source badges.
- **Voice input** (P1): mic button in input panel uses Web Speech API for
  instant browser transcription (Hindi / Devanagari) with automatic fallback
  to Whisper (`/api/transcribe`) when unavailable. Appends to current input.
- **Offline mode** (P2 → moved to P0): switch in input panel toggles between
  cloud (Claude Sonnet 4.5) and on-device (NLLB-200-distilled-600M). First
  enablement warms up the model with a toast; correction-override still wins
  over both modes.
- Google Fonts: Cormorant Garamond (display), Outfit (body), Noto Sans
  Devanagari (Sanskrit/Hindi/Marathi output).
- JSON-file persistence (no DB).

## Backlog

- **P1** Export corrections dataset (CSV/JSON download).
- **P1** Phrase-level / fuzzy matching for corrections (currently exact-match
  only).
- **P2** Progress bar for offline model download (currently a toast).
- **P2** Switch to env-configurable offline model id so upgrades to NLLB-1.3B
  / IndicTrans2-gated (with HF token) are one-line changes.
- **P2** Multi-user profiles.
