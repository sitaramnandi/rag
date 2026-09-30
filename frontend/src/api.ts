import type { ChatMessage, DocumentInfo, SourceChunk, TokenUsage, UploadResponse } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function listDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_URL}/documents`);
  if (!res.ok) throw new Error(`Failed to list documents (${res.status})`);
  return res.json();
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/documents/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Upload failed (${res.status})`);
  }
  return res.json();
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`${API_URL}/documents/${docId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Delete failed (${res.status})`);
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

type StreamEvent =
  | { type: "sources"; sources: SourceChunk[] }
  | { type: "token"; content: string }
  | { type: "usage"; input_tokens: number; output_tokens: number; total_tokens: number }
  | { type: "error"; message: string; detail?: string }
  | { type: "done" };

export interface StreamChatCallbacks {
  onSources: (sources: SourceChunk[]) => void;
  onToken: (token: string) => void;
  onUsage: (usage: TokenUsage) => void;
  onDone: () => void;
  onError: (error: Error) => void;
}

export async function streamChat(
  message: string,
  history: ChatMessage[],
  callbacks: StreamChatCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  try {
    const res = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
      signal,
    });

    if (!res.ok || !res.body) {
      throw new Error(`Chat request failed (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let sawDone = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;

        const event = JSON.parse(line.slice(5).trim()) as StreamEvent;
        if (event.type === "sources") callbacks.onSources(event.sources);
        else if (event.type === "token") callbacks.onToken(event.content);
        else if (event.type === "usage") {
          callbacks.onUsage({
            input_tokens: event.input_tokens,
            output_tokens: event.output_tokens,
            total_tokens: event.total_tokens,
          });
        } else if (event.type === "error") {
          callbacks.onError(new Error(event.message));
        } else if (event.type === "done") {
          sawDone = true;
          callbacks.onDone();
        }
      }
    }

    // The connection closed without ever sending a "done" event — the server
    // process likely crashed or the connection dropped mid-stream, rather
    // than finishing cleanly. Surface it instead of leaving the UI stuck.
    if (!sawDone) {
      callbacks.onError(new Error("Connection closed unexpectedly before the response finished."));
    }
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") return;
    callbacks.onError(err instanceof Error ? err : new Error(String(err)));
  }
}
