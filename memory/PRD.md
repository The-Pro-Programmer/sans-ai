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

- `POST /api/translate` multi-language response with confidence + source.
- `POST /api/feedback/v2` captures 👍 / 👎 + corrections and persists the
  override.
- `GET/DELETE /api/history` with rich items incl. feedback map.
- `GET /api/corrections` and `GET /api/corrections/check`.
- Single-page UI: asymmetric 12-col bento grid, Indic light / jewel dark
  themes, sticky glass header with history drawer + theme toggle.
- Translation cards with confidence progress bar, copy button, thumbs up/down,
  inline correction composer.
- Google Fonts: Cormorant Garamond (display), Outfit (body), Noto Sans
  Devanagari (Sanskrit/Hindi/Marathi output).
- JSON-file persistence (no DB).

## Backlog

- **P1** Voice/audio input for Sanskrit (future scope).
- **P1** Export corrections dataset (CSV/JSON download).
- **P2** Phrase-level incremental fine-tuning (currently only exact-match
  overrides).
- **P2** Multi-user profiles.
- **P2** Offline/on-device inference (fully offline mode).
