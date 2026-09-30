import logging
import time
from collections.abc import Iterator

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.config import settings
from models.schemas import ChatMessage, SourceChunk
from rag.retriever import retrieve

logger = logging.getLogger(__name__)

_llm = ChatOpenAI(
    model=settings.openai_chat_model,
    api_key=settings.openai_api_key,
    temperature=0,
    stream_usage=True,
    timeout=30,
    max_retries=2,
)

_SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using ONLY the "
    "context provided below. If the answer isn't contained in the context, "
    "say you don't know rather than guessing.\n\n"
    "Grounding rules:\n"
    "- Stay as close as possible to the wording of the source text. Do not "
    "paraphrase loosely, add outside knowledge, or infer anything beyond "
    "what the context states.\n"
    "- After every sentence or claim, cite the source it came from using "
    "its bracketed label, e.g. [Source 1]. If a sentence draws on multiple "
    "sources, cite all of them, e.g. [Source 1][Source 2].\n"
    "- If different sources conflict, point out the conflict rather than "
    "silently picking one.\n\n"
    "Context:\n{context}"
)

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_PROMPT),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ]
)

_chain = _prompt | _llm


def _build_context(sources: list[SourceChunk]) -> str:
    if not sources:
        return "(no relevant context found)"
    return "\n\n".join(
        f"[Source {i + 1} - {s.filename}]\n{s.text}" for i, s in enumerate(sources)
    )


def _history_messages(history: list[ChatMessage]) -> list[BaseMessage]:
    return [
        HumanMessage(content=m.content) if m.role == "user" else AIMessage(content=m.content)
        for m in history
    ]


def _prepare(question: str, history: list[ChatMessage]) -> tuple[list[SourceChunk], dict]:
    sources = retrieve(question)
    inputs = {
        "context": _build_context(sources),
        "history": _history_messages(history),
        "question": question,
    }
    return sources, inputs


def stream_answer(question: str, history: list[ChatMessage]) -> Iterator[dict]:
    """Yields dict events: {"type": "sources", ...} once, then {"type": "token", ...}
    per chunk of the answer, then always ends with {"type": "done"} — even on
    failure, so the frontend's read loop always has a clear terminal signal
    instead of the connection just dying mid-stream."""
    try:
        t0 = time.monotonic()
        sources, inputs = _prepare(question, history)
        retrieval_ms = (time.monotonic() - t0) * 1000
        logger.info("[timing] retrieval took %.0fms (%d sources)", retrieval_ms, len(sources))

        yield {"type": "sources", "sources": [s.model_dump() for s in sources]}

        logger.info(
            "Streaming OpenAI chat model %s (%d source chunks, %d history messages)...",
            settings.openai_chat_model,
            len(sources),
            len(history),
        )
        t1 = time.monotonic()
        first_token_ms = None
        chars = 0
        usage = None
        for chunk in _chain.stream(inputs):
            if chunk.content:
                if first_token_ms is None:
                    first_token_ms = (time.monotonic() - t1) * 1000
                    logger.info("[timing] time to first token: %.0fms", first_token_ms)
                chars += len(chunk.content)
                yield {"type": "token", "content": chunk.content}
            if chunk.usage_metadata:
                usage = chunk.usage_metadata

        total_ms = (time.monotonic() - t1) * 1000
        logger.info(
            "[timing] generation total %.0fms (%d chars, usage=%s) | end-to-end %.0fms",
            total_ms,
            chars,
            usage,
            (time.monotonic() - t0) * 1000,
        )

        if usage:
            yield {
                "type": "usage",
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "total_tokens": usage["total_tokens"],
            }
    except Exception as exc:
        logger.exception("stream_answer failed")
        yield {
            "type": "error",
            "message": "Something went wrong generating a response. Please try again.",
            "detail": f"{type(exc).__name__}: {exc}",
        }

    yield {"type": "done"}
