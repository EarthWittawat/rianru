"use client";

import { useEffect, useState } from "react";
import {
  generateQuiz,
  getStoredQuiz,
  getTopics,
  type QuizQuestion,
} from "@/lib/api";
import { QuizCard } from "@/components/QuizCard";

export function QuizBoard() {
  const [topics, setTopics] = useState<string[]>([]);
  const [topic, setTopic] = useState("");
  // Questions carry the topic they belong to, so switching topics shows the
  // right set without a separate reset.
  const [loaded, setLoaded] = useState<{ topic: string; questions: QuizQuestion[] }>({
    topic: "",
    questions: [],
  });
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const questions = loaded.topic === topic ? loaded.questions : [];

  useEffect(() => {
    getTopics()
      .then((list) => {
        setTopics(list);
        setTopic((current) => current || list[0] || "");
      })
      .catch(() => setError("Could not reach the API. Is the backend running?"));
  }, []);

  useEffect(() => {
    if (!topic) return;
    getStoredQuiz(topic)
      .then((data) => setLoaded({ topic, questions: data.questions }))
      .catch(() => setLoaded({ topic, questions: [] }));
  }, [topic]);

  async function handleGenerate() {
    if (!topic || pending) return;
    setPending(true);
    setError("");
    try {
      const result = await generateQuiz(topic);
      if (result.questions.length === 0) {
        setError("The model did not return usable questions. Try generating again.");
      }
      setLoaded((prev) => ({
        topic,
        questions: [
          ...result.questions,
          ...(prev.topic === topic ? prev.questions : []),
        ],
      }));
    } catch {
      setError("Could not generate questions. Is the backend running?");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-10">
      <h1 className="text-xl font-semibold tracking-tight">Quiz</h1>
      <p className="mt-1 text-sm text-neutral-600">
        Practice questions written from the lecture you pick.
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-2">
        <select
          value={topic}
          onChange={(event) => setTopic(event.target.value)}
          aria-label="Topic"
          className="rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm"
        >
          {topics.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <button
          onClick={handleGenerate}
          disabled={pending || !topic}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white transition-colors hover:bg-neutral-700 disabled:opacity-40"
        >
          {pending ? "Writing questions…" : "Generate questions"}
        </button>
      </div>

      {error && (
        <p className="mt-6 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          {error}
        </p>
      )}

      {questions.length === 0 && !pending && !error && (
        <p className="mt-10 text-sm text-neutral-500">
          No questions for this topic yet. Generate a set to start.
        </p>
      )}

      <ul className="mt-6 space-y-3">
        {questions.map((question, index) => (
          <QuizCard key={question.id} question={question} index={index} />
        ))}
      </ul>
    </div>
  );
}
