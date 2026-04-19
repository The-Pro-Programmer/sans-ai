from fastapi import APIRouter
from models.request_models import IngestRequest
from services.rag_service import ingest_text

router = APIRouter()

@router.post("/ingest")
def ingest(req: IngestRequest):
    return ingest_text(req.text, req.book, req.chapter)