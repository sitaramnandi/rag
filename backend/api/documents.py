import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from models.schemas import DocumentInfo, UploadResponse
from rag import ingest, manifest, vectorstore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    content = file.file.read()
    try:
        return ingest.ingest_document(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[DocumentInfo])
def list_documents() -> list[DocumentInfo]:
    return [DocumentInfo(**doc) for doc in manifest.list_documents()]


@router.delete("/{doc_id}")
def delete_document(doc_id: str) -> dict:
    entry = manifest.remove_document(doc_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")

    keys = [f"{doc_id}::{i}" for i in range(entry["chunk_count"])]
    vectorstore.delete_by_keys(keys)

    return {"deleted": doc_id}
