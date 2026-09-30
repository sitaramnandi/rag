import io
import logging
import uuid
from datetime import datetime, timezone

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config import settings
from models.schemas import UploadResponse
from rag import manifest
from rag.vectorstore import vector_store

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = (".txt", ".md", ".pdf")


def extract_text(filename: str, content: bytes) -> str:
    lower = filename.lower()

    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)

    if lower.endswith((".txt", ".md")):
        return content.decode("utf-8")

    raise ValueError(
        f"Unsupported file type for '{filename}'. Supported: {_SUPPORTED_EXTENSIONS}"
    )


def ingest_document(filename: str, content: bytes) -> UploadResponse:
    doc_id = str(uuid.uuid4())
    logger.info("[%s] Starting ingestion: %s (%d bytes)", doc_id, filename, len(content))

    text = extract_text(filename, content)
    logger.info("[%s] Extracted %d characters of text", doc_id, len(text))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = [c for c in splitter.split_text(text) if c.strip()]
    logger.info(
        "[%s] Chunking done: %d chunks (chunk_size=%d, overlap=%d)",
        doc_id,
        len(chunks),
        settings.chunk_size,
        settings.chunk_overlap,
    )

    if not chunks:
        logger.error("[%s] No extractable text found, aborting ingestion", doc_id)
        raise ValueError(f"No extractable text found in '{filename}'")

    ids = [f"{doc_id}::{i}" for i in range(len(chunks))]
    metadatas = [
        {"doc_id": doc_id, "filename": filename, "chunk_index": i}
        for i in range(len(chunks))
    ]

    logger.info(
        "[%s] Calling S3 Vectors: embedding + storing %d chunks (bucket=%s, index=%s)...",
        doc_id,
        len(chunks),
        settings.s3_vector_bucket,
        settings.s3_vector_index,
    )
    vector_store.add_texts(texts=chunks, metadatas=metadatas, ids=ids)
    logger.info("[%s] S3 Vectors upsert succeeded", doc_id)

    uploaded_at = datetime.now(timezone.utc).isoformat()
    manifest.add_document(
        doc_id=doc_id,
        filename=filename,
        chunk_count=len(chunks),
        uploaded_at=uploaded_at,
    )

    logger.info("[%s] Ingestion complete: %s (%d chunks)", doc_id, filename, len(chunks))

    return UploadResponse(doc_id=doc_id, filename=filename, chunk_count=len(chunks))
