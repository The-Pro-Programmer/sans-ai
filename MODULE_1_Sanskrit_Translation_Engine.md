# MODULE 1: Sanskrit Translation Engine

## 🎯 Objective

Convert Sanskrit text → English / Hindi / Marathi

## 📥 Inputs
- Sanskrit text (Unicode, Devanagari)
- Target language (EN / HI / MR)

## ⚙️ Functional Requirements

- System shall accept user input in Sanskrit text form.
- System shall normalize text:
  - Remove extra spaces
  - Handle Sandhi splitting (basic level)
- System shall translate text using:
  - Pre-trained LLM (offline/local if possible)
  - Or API (initial phase)
- System shall support:
  - Word-by-word meaning (optional toggle)
  - Full sentence translation

## 📤 Outputs

- Translated sentence
- Optional:
  - Word meanings
  - Grammar breakdown

## 💡 Future Enhancement

- Context-aware translation (scriptures vs modern Sanskrit)
