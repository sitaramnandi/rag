from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class SourceChunk(BaseModel):
    doc_id: str
    filename: str
    text: str
    score: float


class DocumentInfo(BaseModel):
    doc_id: str
    filename: str
    chunk_count: int
    uploaded_at: str


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    chunk_count: int
