import logging

from app.config import settings
from models.schemas import SourceChunk
from rag.vectorstore import vector_store

logger = logging.getLogger(__name__)


def retrieve(question: str, top_k: int | None = None) -> list[SourceChunk]:
    k = top_k or settings.retrieval_top_k

    logger.info("Calling S3 Vectors: querying top %d chunks for question %r...", k, question[:80])
    results = vector_store.similarity_search_with_score(question, k=k)
    logger.info("S3 Vectors query succeeded: %d results", len(results))

    sources = [
        SourceChunk(
            doc_id=doc.metadata.get("doc_id", ""),
            filename=doc.metadata.get("filename", ""),
            text=doc.page_content,
            score=score,
        )
        for doc, score in results
    ]

    logger.info("Retrieved %d chunks for question: %r", len(sources), question[:80])

    return sources
