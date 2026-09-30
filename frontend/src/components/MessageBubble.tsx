import { useState } from "react";
import type { DisplayMessage } from "../types";

export function MessageBubble({ message }: { message: DisplayMessage }) {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const isUser = message.role === "user";
  const hasSources = !!message.sources && message.sources.length > 0;

  return (
    <div className={`bubble-row ${isUser ? "bubble-row--user" : "bubble-row--assistant"}`}>
      <div className={`bubble ${isUser ? "bubble--user" : "bubble--assistant"}`}>
        {message.content.length === 0 && message.streaming ? (
          <span className="typing-dots" aria-label="Thinking">
            <span />
            <span />
            <span />
          </span>
        ) : (
          <span>{message.content}</span>
        )}

        {hasSources && (
          <div className="sources">
            <button
              type="button"
              className="sources-toggle"
              onClick={() => setSourcesOpen((v) => !v)}
              aria-expanded={sourcesOpen}
            >
              {sourcesOpen ? "Hide" : "Show"} sources ({message.sources!.length})
            </button>
            {sourcesOpen && (
              <ul className="sources-list">
                {message.sources!.map((s, i) => (
                  <li key={`${s.doc_id}-${i}`} className="source-item">
                    <div className="source-item-head">
                      <span className="source-filename">{s.filename}</span>
                      <span className="source-score">score {s.score.toFixed(3)}</span>
                    </div>
                    <p className="source-text">{s.text}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {!isUser && (message.streaming || message.usage) && (
          <div className="token-meter">
            {message.usage ? (
              <span title="Exact counts reported by OpenAI once generation finished">
                {message.usage.input_tokens} in · {message.usage.output_tokens} out ·{" "}
                {message.usage.total_tokens} total tokens
              </span>
            ) : (
              message.streaming &&
              !!message.liveTokenCount && (
                <span title="Live estimate: one streamed chunk counted per token">
                  ~{message.liveTokenCount} tokens
                </span>
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
}
