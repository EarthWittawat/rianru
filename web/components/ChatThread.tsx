"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { askTutor, type ChatSource, type ChatTurn } from "@/lib/api";
import { Markdown } from "@/components/Markdown";

type Message = ChatTurn & { sources?: ChatSource[] };

const SUGGESTIONS = [
  "What is TF-IDF and why is it used?",
  "How does stemming differ from lemmatization?",
  "What are the steps of text preprocessing?",
];

export function ChatThread() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  async function send(question: string) {
    const trimmed = question.trim();
    if (!trimmed || pending) return;

    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setInput("");
    setPending(true);
    setError("");

    try {
      const reply = await askTutor(trimmed, history);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: reply.answer, sources: reply.sources },
      ]);
    } catch {
      setError("The tutor could not be reached. Is the backend running?");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-6">
      <div className="flex-1 space-y-6 overflow-y-auto py-8">
        {messages.length === 0 && (
          <div>
            <h1 className="text-xl font-semibold tracking-tight">Tutor</h1>
            <p className="mt-1 text-sm text-neutral-600">
              Answers come from your CPE393 material, not the open internet.
            </p>
            <ul className="mt-6 space-y-2">
              {SUGGESTIONS.map((suggestion) => (
                <li key={suggestion}>
                  <button
                    onClick={() => send(suggestion)}
                    className="w-full rounded-lg border border-neutral-200 bg-white px-4 py-2.5 text-left text-sm text-neutral-700 transition-colors hover:border-neutral-400"
                  >
                    {suggestion}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))}

        {pending && (
          <p className="text-sm text-neutral-500">Reading your notes…</p>
        )}
        {error && (
          <p className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
            {error}
          </p>
        )}
        <div ref={endRef} />
      </div>

      <form
        onSubmit={(event) => {
          event.preventDefault();
          send(input);
        }}
        className="sticky bottom-0 flex gap-2 bg-neutral-50 py-4"
      >
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about anything in the course…"
          aria-label="Ask the tutor"
          className="flex-1 rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm outline-none focus:border-neutral-500"
        />
        <button
          type="submit"
          disabled={pending || !input.trim()}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white transition-colors hover:bg-neutral-700 disabled:opacity-40"
        >
          Ask
        </button>
      </form>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-lg bg-neutral-900 px-4 py-2.5 text-sm text-white">
          {message.content}
        </p>
      </div>
    );
  }

  return (
    <div>
      <Markdown>{message.content}</Markdown>
      {message.sources && message.sources.length > 0 && (
        <Sources sources={message.sources} />
      )}
    </div>
  );
}

function Sources({ sources }: { sources: ChatSource[] }) {
  const unique = sources.filter(
    (source, index) =>
      sources.findIndex((s) => s.document_id === source.document_id) === index,
  );

  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {unique.map((source) => (
        <Link
          key={source.document_id}
          href={`/viewer/${encodeURIComponent(source.document_id)}`}
          className="rounded border border-neutral-200 bg-white px-2 py-1 text-xs text-neutral-600 transition-colors hover:border-neutral-400"
        >
          {source.topic}
          {source.page ? ` · p${source.page}` : ""}
        </Link>
      ))}
    </div>
  );
}
