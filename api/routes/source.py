from fastapi import APIRouter
from pydantic import BaseModel
from services.source_service import find_source

router = APIRouter()

class SourceRequest(BaseModel):
    text: str

@router.post("/source")
def source(req: SourceRequest):
    return find_source(req.text)