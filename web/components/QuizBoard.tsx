"use client";

import { useEffect, useState } from "react";
import {
  generateQuiz,
  getStoredQuiz,
  getTopics,
  type QuizQuestion,
} from "@/lib/api";
import { QuizCard } from "@/components/QuizCard";
import { useCourse } from "@/lib/course";

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
  const { course } = useCourse();
  const questions = loaded.topic === topic ? loaded.questions : [];

  useEffect(() => {
    getTopics(course)
      .then((list) => {
        setTopics(list);
        // The previous class's topic means nothing here, so take the first.
        setTopic((current) => (list.includes(current) ? current : list[0] || ""));
      })
      .catch(() => setError("Could not reach the API. Is the backend running?"));
  }, [course]);

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
    <div className="mx-auto w-full max-w-3xl px-6 py-14">
      <h1 className="text-display tracking-tight">Quiz</h1>
      <p className="mt-2 max-w-[58ch] text-slate">
        Questions written from the lecture you pick. Every answer is recorded,
        which is what the coach reads.
      </p>

      <div className="mt-8 flex flex-wrap items-center gap-3 border-y border-rule py-3">
        <label htmlFor="quiz-topic" className="apparatus">
          Topic
        </label>
        <select
          id="quiz-topic"
          value={topic}
          onChange={(event) => setTopic(event.target.value)}
          aria-label="Topic"
          className="min-w-0 flex-1 border border-rule bg-paper px-3 py-1.5 text-fine"
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
          className="detent px-4 py-1.5 text-fine"
        >
          {pending ? "Writing questions…" : "Generate questions"}
        </button>
      </div>

      {error && (
        <p className="ruled-block mt-6 border-rubric px-4 py-3 text-fine text-rubric-deep">
          {error}
        </p>
      )}

      {questions.length === 0 && !pending && !error && (
        <p className="mt-10 text-fine text-slate">
          No questions for this topic yet. Generate a set to start.
        </p>
      )}

      <ul className="mt-4">
        {questions.map((question, index) => (
          <QuizCard key={question.id} question={question} index={index} />
        ))}
      </ul>
    </div>
  );
}
