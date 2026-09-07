export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type DocumentSummary = {
  id: string;
  title: string;
  topic: string;
  course: string;
  activity_type: string;
  file_path: string;
  file_type: string;
  chunk_count: number;
};

export type DocumentChunk = {
  id: string;
  text: string;
  page: number | null;
  cell_index: number | null;
  index: number;
};

export type DocumentDetail = Omit<DocumentSummary, "chunk_count"> & {
  chunks: DocumentChunk[];
};

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function listDocuments() {
  return get<DocumentSummary[]>("/documents");
}

export function getDocument(id: string) {
  return get<DocumentDetail>(`/documents/${encodeURIComponent(id)}`);
}

export function documentFileUrl(id: string) {
  return `${API_BASE}/documents/${encodeURIComponent(id)}/file`;
}

export type GraphNode = {
  id: string;
  label: string;
  type: "Document" | "Entity" | "Highlight";
  topic?: string;
  entity_type?: string;
  explanation?: string;
};

export type GraphEdge = { source: string; target: string; label: string };

export function getGraph(topic?: string) {
  const query = topic ? `?topic=${encodeURIComponent(topic)}` : "";
  return get<{ nodes: GraphNode[]; edges: GraphEdge[] }>(`/graph${query}`);
}

export function getTopics() {
  return get<string[]>("/graph/topics");
}

export type Explanation = {
  explanation: string;
  selected_text: string;
  chunk_id: string;
  document_title: string;
  topic: string;
  page: number | null;
};

export function explainSelection(
  documentId: string,
  selectedText: string,
  page: number | null,
) {
  return post<Explanation>("/explain", {
    document_id: documentId,
    selected_text: selectedText,
    page,
  });
}

export function saveHighlight(
  chunkId: string,
  selectedText: string,
  explanation: string,
) {
  return post<{ id: string }>("/highlights", {
    chunk_id: chunkId,
    selected_text: selectedText,
    explanation,
  });
}

export async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`${path} failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}
