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
  cell_type: "code" | "markdown" | null;
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

export type StudyTask = {
  id: string;
  action: string;
  topic: string;
  source: { document_title: string; page: number | null } | null;
  why: string | null;
  est_minutes: number | null;
  done: boolean;
};

export type StudyPlan = { id: string; created_at: string; tasks: StudyTask[] };

export function generatePlan() {
  return post<StudyPlan>("/coach/plan", {});
}

export function getLatestPlan() {
  return get<StudyPlan>("/coach/plan/latest");
}

export async function setTaskDone(taskId: string, done: boolean) {
  const response = await fetch(`${API_BASE}/coach/tasks/${taskId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ done }),
  });
  if (!response.ok) throw new Error(`failed: ${response.status}`);
  return response.json();
}

export type TopicStat = {
  topic: string;
  attempted: number;
  correct: number;
  accuracy: number;
  last_attempt_at: string;
};

export function recordAttempt(
  questionId: string,
  grade: { chosen_answer: string } | { self_grade: boolean },
) {
  return post<{ is_correct: boolean; correct_answer: string; graded_by: string }>(
    "/progress/attempts",
    { question_id: questionId, ...grade },
  );
}

export function getTopicStats() {
  return get<TopicStat[]>("/progress/topics");
}

export function getWeakTopics(limit = 5) {
  return get<TopicStat[]>(`/progress/weak?limit=${limit}`);
}

export type QuizQuestion = {
  id: string;
  format: "multiple_choice" | "short_answer";
  question: string;
  options: string[];
  answer: string;
  explanation: string;
  topic?: string;
};

export function generateQuiz(topic: string, count = 6) {
  return post<{ topic: string; questions: QuizQuestion[] }>("/quiz/generate", {
    topic,
    count,
  });
}

export function getStoredQuiz(topic: string) {
  return get<{ questions: QuizQuestion[] }>(
    `/quiz?topic=${encodeURIComponent(topic)}`,
  );
}

export type ChatSource = {
  chunk_id: string;
  document_id: string;
  document_title: string;
  topic: string;
  page: number | null;
  score: number;
};

export type ChatTurn = { role: "user" | "assistant"; content: string };

export function askTutor(message: string, history: ChatTurn[]) {
  return post<{ answer: string; sources: ChatSource[] }>("/chat", {
    message,
    history,
  });
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

export type Highlight = {
  id: string;
  selected_text: string;
  explanation: string;
  page: number | null;
  chunk_id: string;
  document_id: string;
  document_title: string;
  topic: string;
};

export function listHighlights() {
  return get<Highlight[]>("/highlights");
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

export type PathConcept = {
  name: string;
  type: string;
  mentions: number;
  depth: number;
  explained: boolean;
};

export type PathStage = {
  topic: string;
  position: number;
  concepts: PathConcept[];
};

export type PathEdge = {
  source: string;
  target: string;
  reason: string;
  origin: "timeline" | "model";
};

export type LearningPath = { stages: PathStage[]; edges: PathEdge[] };

export function getLearningPath(minMentions = 2) {
  return get<LearningPath>(`/path?min_mentions=${minMentions}`);
}

export type ConceptDetail = {
  name: string;
  type: string;
  summary: string | null;
  example: string | null;
  requires: { name: string; reason: string; origin: string }[];
  sources: {
    document_id: string;
    document_title: string;
    topic: string;
    page: number | null;
  }[];
};

export function getConcept(name: string) {
  return get<ConceptDetail>(`/concepts/${encodeURIComponent(name)}`);
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
