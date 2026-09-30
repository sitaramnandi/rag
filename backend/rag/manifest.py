import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "data" / "documents.json"


def _load() -> list[dict]:
    if not _MANIFEST_PATH.exists():
        return []
    return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))


def _save(entries: list[dict]) -> None:
    _MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    _MANIFEST_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def list_documents() -> list[dict]:
    return _load()


def add_document(doc_id: str, filename: str, chunk_count: int, uploaded_at: str) -> None:
    entries = _load()
    entries.append(
        {
            "doc_id": doc_id,
            "filename": filename,
            "chunk_count": chunk_count,
            "uploaded_at": uploaded_at,
        }
    )
    _save(entries)
    logger.info("Manifest: added document %s (%s, %d chunks)", doc_id, filename, chunk_count)


def remove_document(doc_id: str) -> dict | None:
    entries = _load()
    match = next((e for e in entries if e["doc_id"] == doc_id), None)
    if match is None:
        logger.warning("Manifest: remove_document called for unknown doc_id %s", doc_id)
        return None
    _save([e for e in entries if e["doc_id"] != doc_id])
    logger.info("Manifest: removed document %s (%s)", doc_id, match.get("filename"))
    return match
