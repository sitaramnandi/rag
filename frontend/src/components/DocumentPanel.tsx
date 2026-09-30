import { useEffect, useRef, useState } from "react";
import { deleteDocument, listDocuments, uploadDocument } from "../api";
import type { DocumentInfo } from "../types";

export function DocumentPanel() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function refresh() {
    try {
      setDocuments(await listDocuments());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      await uploadDocument(file);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDelete(docId: string) {
    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.doc_id !== docId));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  return (
    <div className="doc-panel">
      <h2 className="panel-title">Documents</h2>

      <label className={`upload-btn ${uploading ? "upload-btn--busy" : ""}`}>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md"
          onChange={handleFileChange}
          disabled={uploading}
          hidden
        />
        {uploading ? "Uploading..." : "Upload document"}
      </label>

      {error && <div className="panel-error">{error}</div>}

      <ul className="doc-list">
        {documents.length === 0 && !uploading && (
          <li className="doc-empty">No documents yet.</li>
        )}
        {documents.map((doc) => (
          <li key={doc.doc_id} className="doc-item">
            <div className="doc-item-info">
              <span className="doc-filename">{doc.filename}</span>
              <span className="doc-meta">{doc.chunk_count} chunks</span>
            </div>
            <button
              type="button"
              className="doc-delete"
              onClick={() => handleDelete(doc.doc_id)}
              aria-label={`Delete ${doc.filename}`}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
