import { useEffect, useRef, useState } from "react";
import { streamChat } from "../api";
import type { ChatMessage, DisplayMessage } from "../types";
import { MessageBubble } from "./MessageBubble";

const NEAR_BOTTOM_THRESHOLD = 80;

export function ChatWindow() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [showJump, setShowJump] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const stickToBottomRef = useRef(true);

  function isNearBottom() {
    const el = scrollRef.current;
    if (!el) return true;
    return el.scrollHeight - el.scrollTop - el.clientHeight < NEAR_BOTTOM_THRESHOLD;
  }

  function scrollToBottom(behavior: ScrollBehavior = "smooth") {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior });
    setShowJump(false);
  }

  function handleScroll() {
    stickToBottomRef.current = isNearBottom();
    setShowJump(!stickToBottomRef.current);
  }

  useEffect(() => {
    if (stickToBottomRef.current) {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
    } else {
      setShowJump(true);
    }
  }, [messages]);

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }

  function updateLastMessage(updater: (msg: DisplayMessage) => DisplayMessage) {
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      next[next.length - 1] = updater(last);
      return next;
    });
  }

  function finishSending() {
    setSending(false);
    abortRef.current = null;
    textareaRef.current?.focus();
  }

  async function handleSend() {
    const question = input.trim();
    if (!question || sending) return;

    const history: ChatMessage[] = messages.map(({ role, content }) => ({ role, content }));

    stickToBottomRef.current = true;
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "", streaming: true },
    ]);
    setInput("");
    requestAnimationFrame(autoResize);
    setSending(true);

    const controller = new AbortController();
    abortRef.current = controller;

    await streamChat(
      question,
      history,
      {
        onSources: (sources) => updateLastMessage((msg) => ({ ...msg, sources })),
        onToken: (token) =>
          updateLastMessage((msg) => ({
            ...msg,
            content: msg.content + token,
            liveTokenCount: (msg.liveTokenCount ?? 0) + 1,
          })),
        onUsage: (usage) => updateLastMessage((msg) => ({ ...msg, usage })),
        onDone: () => {
          updateLastMessage((msg) => ({ ...msg, streaming: false }));
          finishSending();
        },
        onError: (err) => {
          updateLastMessage((msg) => ({
            ...msg,
            content: msg.content || `Something went wrong: ${err.message}`,
            streaming: false,
          }));
          finishSending();
        },
      },
      controller.signal,
    );
  }

  function handleStop() {
    abortRef.current?.abort();
    updateLastMessage((msg) => ({ ...msg, streaming: false }));
    finishSending();
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="chat-window">
      <div className="chat-scroll-wrap">
        <div className="chat-scroll" ref={scrollRef} onScroll={handleScroll}>
          {messages.length === 0 && (
            <div className="chat-empty">Upload a document, then ask a question about it.</div>
          )}
          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}
        </div>
        {showJump && (
          <button type="button" className="jump-to-latest" onClick={() => scrollToBottom()}>
            ↓ New content
          </button>
        )}
      </div>

      <div className="chat-input-row">
        <textarea
          ref={textareaRef}
          className="chat-input"
          placeholder="Ask a question about your documents... (Enter to send, Shift+Enter for a new line)"
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            autoResize();
          }}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={sending}
        />
        {sending ? (
          <button type="button" className="send-btn send-btn--stop" onClick={handleStop}>
            Stop
          </button>
        ) : (
          <button
            type="button"
            className="send-btn"
            onClick={handleSend}
            disabled={!input.trim()}
          >
            Send
          </button>
        )}
      </div>
    </div>
  );
}
