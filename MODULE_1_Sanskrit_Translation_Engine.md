# Sanskrit Translation AI - Learning System Architecture & Development Plan

## 1. Problem Statement

Build a local AI system that: - Translates Sanskrit → English / Hindi /
Marathi - Learns from user corrections over time - Works fully offline

------------------------------------------------------------------------

## 2. Core Concept: Human-in-the-Loop Learning

Flow:

    Sanskrit → Model Translation → User Correction → Store → Learn → Improve

------------------------------------------------------------------------

## 3. Updated Architecture

                    ┌──────────────────────┐
                    │   User Interface     │
                    └─────────┬────────────┘
                              │
                    ┌─────────▼────────────┐
                    │  Input Processor     │
                    └─────────┬────────────┘
                              │
                    ┌─────────▼────────────┐
                    │ Translation Engine   │
                    └─────────┬────────────┘
                              │
                    ┌─────────▼────────────┐
                    │  Feedback Engine⭐   │
                    │ (Store corrections)  │
                    └─────────┬────────────┘
                              │
            ┌─────────────────▼─────────────────┐
            │      Learning System              │
            │ 1. Memory (Exact match)           │
            │ 2. Semantic Search (Embeddings)   │
            │ 3. RAG Layer                      │
            │ 4. Fine-tuning (future)           │
            └───────────────────────────────────┘

------------------------------------------------------------------------

## 4. Learning Approaches

### 4.1 Correction Memory (Phase 1)

-   Store corrected translations
-   Use exact + fuzzy matching

Example:

    Input: धर्मो रक्षति रक्षितः
    Correct: Dharma protects those who protect it

------------------------------------------------------------------------

### 4.2 Semantic Search (Phase 2)

-   Use embeddings
-   Find similar sentences

Libraries: - sentence-transformers - FAISS

------------------------------------------------------------------------

### 4.3 RAG (Phase 3)

-   Inject past corrections as context
-   Improves generalization

------------------------------------------------------------------------

### 4.4 Fine-Tuning (Phase 4)

-   Train model on corrected dataset
-   Use LoRA / HuggingFace Trainer

------------------------------------------------------------------------

## 5. Data Storage Design

### Table: corrections

  id   input_text   corrected_translation   embedding
  ---- ------------ ----------------------- -----------

------------------------------------------------------------------------

## 6. Similarity Logic

-   Cosine similarity
-   Thresholds:
    -   0.85 → strong match
    -   0.70 → partial match

------------------------------------------------------------------------

## 7. Enhanced Learning

### Word-Level Memory

    धर्म → Dharma

### Phrase-Level Memory

    रक्षति → protects

### Context Tagging

    domain: spiritual / poetic / legal

------------------------------------------------------------------------

## 8. Development Plan

### Phase 1

-   Basic translator
-   Correction storage (SQLite/JSON)

### Phase 2

-   Embeddings + similarity search

### Phase 3

-   RAG integration
    
    - Instead of only depenging on the model, RAG will retrieve relevant past knowledge (your corrections)
    - Feed it to the model as context
    - Generate a better translation

### Phase 4

-   Fine-tuning

------------------------------------------------------------------------

## 9. Tech Stack

-   Python
-   PyTorch
-   HuggingFace Transformers
-   FAISS
-   SQLite

------------------------------------------------------------------------

## 10. Vision

Build a: **Self-Learning Sanskrit Intelligence Engine** - Translation -
Meaning extraction - Context awareness - Spiritual insights
