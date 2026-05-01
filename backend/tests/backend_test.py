"""Backend API tests for the Sanskrit translator.

Covers /api/health, /api/translate, /api/feedback, /api/feedback/v2,
/api/history, /api/corrections, /api/corrections/check.
"""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback to frontend/.env
    try:
        with open("/app/frontend/.env", "r") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                    break
    except Exception:
        pass

API = f"{BASE_URL}/api"

# unique sanskrit text per run to avoid collision with prior stored corrections
UNIQUE_SUFFIX = uuid.uuid4().hex[:6]
TEST_TEXT = f"सत्यमेव जयते {UNIQUE_SUFFIX}"
CORRECTION_TEXT = "सत्य की ही विजय होती है (TEST)"


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def created_item_id(session):
    """Clear history, then translate once for test reuse."""
    session.delete(f"{API}/history", timeout=30)
    r = session.post(
        f"{API}/translate",
        json={"text": TEST_TEXT, "target_langs": ["hindi"]},
        timeout=90,
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


# ---------- health ----------

class TestHealth:
    def test_health(self, session):
        r = session.get(f"{API}/health", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["llm_configured"] is True


# ---------- translate ----------

class TestTranslate:
    def test_translate_single_language(self, session, created_item_id):
        r = session.get(f"{API}/history?limit=10", timeout=15)
        data = r.json()
        item = next((h for h in data["items"] if h["id"] == created_item_id), None)
        assert item is not None
        assert item["sanskrit_text"] == TEST_TEXT
        assert len(item["results"]) == 1
        res = item["results"][0]
        assert res["language"] == "hindi"
        assert res["source"] == "llm"
        assert isinstance(res["translation"], str) and res["translation"]
        assert 0 <= res["confidence"] <= 100

    def test_translate_all_languages_default(self, session):
        text = f"विद्या ददाति विनयम् {uuid.uuid4().hex[:6]}"
        r = session.post(f"{API}/translate", json={"text": text}, timeout=120)
        assert r.status_code == 200, r.text
        data = r.json()
        langs = sorted([x["language"] for x in data["results"]])
        assert langs == ["english", "hindi", "marathi"]
        assert data["sanskrit_text"] == text
        assert data["id"]
        assert data["timestamp"]

    def test_translate_empty_text_returns_400(self, session):
        # Pydantic min_length=1 -> 422; whitespace-only -> 400
        r = session.post(f"{API}/translate", json={"text": "   "}, timeout=15)
        assert r.status_code in (400, 422), r.text

    def test_translate_missing_text_returns_422(self, session):
        r = session.post(f"{API}/translate", json={}, timeout=15)
        assert r.status_code == 422


# ---------- history ----------

class TestHistory:
    def test_history_contains_recent(self, session, created_item_id):
        r = session.get(f"{API}/history", timeout=15)
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) >= 1
        # created_item_id should be somewhere near top; index 0 if no other translations after it
        ids = [i["id"] for i in items]
        assert created_item_id in ids


# ---------- feedback ----------

class TestFeedback:
    def test_feedback_thumbs_up(self, session, created_item_id):
        r = session.post(
            f"{API}/feedback",
            json={"item_id": created_item_id, "language": "hindi", "is_correct": True},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["ok"] is True
        assert data["stored_correction"] is False
        # Verify in history
        h = session.get(f"{API}/history", timeout=15).json()["items"]
        item = next((x for x in h if x["id"] == created_item_id), None)
        assert item is not None
        assert item.get("feedback", {}).get("hindi") == "up"

    def test_feedback_negative_without_correction_returns_400(self, session, created_item_id):
        r = session.post(
            f"{API}/feedback",
            json={
                "item_id": created_item_id,
                "language": "hindi",
                "is_correct": False,
            },
            timeout=15,
        )
        assert r.status_code == 400

    def test_feedback_nonexistent_item_returns_404(self, session):
        r = session.post(
            f"{API}/feedback",
            json={
                "item_id": "nonexistent-" + uuid.uuid4().hex,
                "language": "hindi",
                "is_correct": True,
            },
            timeout=15,
        )
        assert r.status_code == 404

    def test_feedback_v2_alias(self, session):
        # make a new translation first (distinct text)
        text = f"अहिंसा परमो धर्मः {uuid.uuid4().hex[:6]}"
        tr = session.post(
            f"{API}/translate", json={"text": text, "target_langs": ["english"]}, timeout=120
        )
        assert tr.status_code == 200
        iid = tr.json()["id"]

        r = session.post(
            f"{API}/feedback/v2",
            json={"item_id": iid, "language": "english", "is_correct": True},
            timeout=15,
        )
        assert r.status_code == 200
        assert r.json()["ok"] is True


# ---------- corrections (learning loop) ----------

class TestCorrectionsLearning:
    def test_negative_feedback_saves_correction_and_reapplies(self, session):
        # new translation
        text = f"कर्म एव धर्मः {uuid.uuid4().hex[:6]}"
        tr = session.post(
            f"{API}/translate",
            json={"text": text, "target_langs": ["hindi"]},
            timeout=120,
        )
        assert tr.status_code == 200
        iid = tr.json()["id"]
        first_source = tr.json()["results"][0]["source"]
        assert first_source == "llm"

        corrected = "कर्म ही धर्म है (CORRECTED)"
        fb = session.post(
            f"{API}/feedback",
            json={
                "item_id": iid,
                "language": "hindi",
                "is_correct": False,
                "correction": corrected,
            },
            timeout=15,
        )
        assert fb.status_code == 200, fb.text
        assert fb.json()["stored_correction"] is True

        # check via /corrections/check
        chk = session.get(
            f"{API}/corrections/check",
            params={"text": text, "language": "hindi"},
            timeout=15,
        )
        assert chk.status_code == 200
        cd = chk.json()
        assert cd["has_override"] is True
        assert cd["correction"] == corrected

        # translate again -> should come back as correction with confidence 100
        tr2 = session.post(
            f"{API}/translate",
            json={"text": text, "target_langs": ["hindi"]},
            timeout=60,
        )
        assert tr2.status_code == 200
        res2 = tr2.json()["results"][0]
        assert res2["source"] == "correction"
        assert res2["confidence"] == 100
        assert res2["translation"] == corrected

        # /corrections list should include this key
        corr_list = session.get(f"{API}/corrections", timeout=15).json()
        assert corr_list["count"] >= 1
        found = any(
            c.get("corrected_text") == corrected
            and c.get("target_lang") == "hindi"
            for c in corr_list["items"]
        )
        assert found


# ---------- voice input (/api/transcribe) ----------

class TestTranscribe:
    def test_transcribe_missing_audio_returns_422(self, session):
        # No file attached -> FastAPI 422 (field required)
        r = requests.post(f"{API}/transcribe", timeout=15)
        assert r.status_code == 422

    def test_transcribe_empty_audio_returns_400(self):
        # Zero-byte audio file — handler checks `if not data` -> 400
        files = {"audio": ("empty.webm", b"", "audio/webm")}
        r = requests.post(f"{API}/transcribe", files=files, timeout=15)
        assert r.status_code == 400, r.text
        assert "Empty" in r.json().get("detail", "") or "empty" in r.json().get("detail", "").lower()


# ---------- offline mode (NLLB-200) ----------

class TestOfflineMode:
    def test_offline_status(self, session):
        # Ensure model is loaded (idempotent — already loaded returns immediately)
        session.post(f"{API}/offline/warmup", json={}, timeout=600)
        r = session.get(f"{API}/offline/status", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["available"] is True
        assert d["loaded"] is True
        assert d["error"] is None
        assert d["model_id"] == "facebook/nllb-200-distilled-600M"

    def test_offline_warmup_idempotent(self, session):
        t0 = time.time()
        r = session.post(f"{API}/offline/warmup", json={}, timeout=60)
        dt = time.time() - t0
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["loaded"] is True
        # Already loaded -> should return quickly
        assert dt < 15, f"warmup took {dt:.1f}s, expected <15s when loaded"

    def test_offline_translate_english(self, session):
        text = f"सत्यमेव जयते {uuid.uuid4().hex[:6]}"
        r = session.post(
            f"{API}/translate",
            json={"text": text, "target_langs": ["english"], "offline_mode": True},
            timeout=120,
        )
        assert r.status_code == 200, r.text
        res = r.json()["results"]
        assert len(res) == 1
        assert res[0]["language"] == "english"
        assert res[0]["source"] == "offline"
        assert isinstance(res[0]["translation"], str) and res[0]["translation"].strip()
        assert res[0]["confidence"] > 0

    def test_offline_translate_all_three_langs(self, session):
        text = f"विद्या ददाति विनयम् {uuid.uuid4().hex[:6]}"
        r = session.post(
            f"{API}/translate",
            json={"text": text, "offline_mode": True},
            timeout=300,
        )
        assert r.status_code == 200, r.text
        results = r.json()["results"]
        langs = sorted(x["language"] for x in results)
        assert langs == ["english", "hindi", "marathi"]
        for res in results:
            assert res["source"] == "offline", f"{res['language']} source was {res['source']}"
            assert res["translation"].strip()
            assert res["confidence"] > 0

    def test_offline_correction_overrides_offline(self, session):
        # Seed correction via negative feedback in LLM mode, then verify
        # offline_mode=True still returns source='correction' for identical text.
        text = f"धर्मो रक्षति रक्षितः {uuid.uuid4().hex[:6]}"
        tr = session.post(
            f"{API}/translate",
            json={"text": text, "target_langs": ["english"]},
            timeout=120,
        )
        assert tr.status_code == 200
        iid = tr.json()["id"]

        corrected = "Dharma protects those who protect it (TEST_OFFLINE_OVERRIDE)"
        fb = session.post(
            f"{API}/feedback",
            json={
                "item_id": iid,
                "language": "english",
                "is_correct": False,
                "correction": corrected,
            },
            timeout=15,
        )
        assert fb.status_code == 200

        # Now translate with offline_mode=True -> correction should win
        tr2 = session.post(
            f"{API}/translate",
            json={"text": text, "target_langs": ["english"], "offline_mode": True},
            timeout=60,
        )
        assert tr2.status_code == 200
        res = tr2.json()["results"][0]
        assert res["source"] == "correction"
        assert res["translation"] == corrected
        assert res["confidence"] == 100

    def test_default_mode_uses_llm_not_offline(self, session):
        text = f"अहं पश्यामि {uuid.uuid4().hex[:6]}"
        r = session.post(
            f"{API}/translate",
            json={"text": text, "target_langs": ["english"]},
            timeout=120,
        )
        assert r.status_code == 200
        res = r.json()["results"][0]
        assert res["source"] in ("llm", "correction")
        assert res["source"] != "offline"


# ---------- clear history ----------

class TestClearHistory:
    def test_clear_history(self, session):
        # ensure at least one entry
        session.post(
            f"{API}/translate",
            json={"text": f"नमस्ते {uuid.uuid4().hex[:6]}", "target_langs": ["english"]},
            timeout=120,
        )
        r = session.delete(f"{API}/history", timeout=15)
        assert r.status_code == 200
        assert r.json()["ok"] is True
        items = session.get(f"{API}/history", timeout=15).json()["items"]
        assert items == []
