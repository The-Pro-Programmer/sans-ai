from fastapi import APIRouter
from models.request_models import TranslationRequest
from services.translation_service import translate_text

router = APIRouter()

@router.post("/translate")
def translate(req: TranslationRequest):
    return translate_text(req.text, req.target_lang)