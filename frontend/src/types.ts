export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface SourceChunk {
  doc_id: string;
  filename: string;
  text: string;
  score: number;
}

export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface DisplayMessage extends ChatMessage {
  sources?: SourceChunk[];
  streaming?: boolean;
  liveTokenCount?: number;
  usage?: TokenUsage;
}

export interface DocumentInfo {
  doc_id: string;
  filename: string;
  chunk_count: number;
  uploaded_at: string;
}

export interface UploadResponse {
  doc_id: string;
  filename: string;
  chunk_count: number;
}
