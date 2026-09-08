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
      <div className="flex-1 space-y-8 overflow-y-auto py-12">
        {messages.length === 0 && (
          <div>
            <h1 className="text-display tracking-tight">Tutor</h1>
            <p className="mt-2 max-w-[58ch] text-slate">
              Answers are read out of your own course material, and say which
              document and page they came from.
            </p>
            <ul className="mt-8">
              {SUGGESTIONS.map((suggestion) => (
                <li key={suggestion} className="border-b border-rule first:border-t">
                  <button
                    onClick={() => send(suggestion)}
                    className="group flex w-full items-baseline gap-4 py-3 text-left"
                  >
                    <span className="apparatus text-ash">Ask</span>
                    <span className="text-fine group-hover:text-rubric group-hover:underline">
                      {suggestion}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {messages.map((message, index) => (
          <MessageTurn key={index} message={message} />
        ))}

        {pending && (
          <p className="apparatus animate-pulse">Reading your material…</p>
        )}
        {error && (
          <p className="ruled-block border-rubric px-4 py-3 text-fine text-rubric-deep">
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
        className="sticky bottom-0 flex gap-2 border-t border-rule bg-paper py-4"
      >
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about anything in the course…"
          aria-label="Ask the tutor"
          className="flex-1 border border-rule bg-paper px-3 py-2 text-fine outline-none placeholder:text-ash focus:border-rubric"
        />
        <button
          type="submit"
          disabled={pending || !input.trim()}
          className="detent px-5 py-2 text-fine"
        >
          Ask
        </button>
      </form>
    </div>
  );
}

function MessageTurn({ message }: { message: Message }) {
  if (message.role === "user") {
    return (
      <p className="bracketed max-w-[62ch] text-lead">{message.content}</p>
    );
  }

  return (
    <div className="max-w-[68ch]">
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
    <div className="mt-4 flex flex-wrap items-baseline gap-x-4 gap-y-1 border-t border-rule pt-2">
      <span className="apparatus">Read in</span>
      {unique.map((source) => (
        <Link
          key={source.document_id}
          href={`/viewer/${encodeURIComponent(source.document_id)}`}
          className="apparatus tabular text-ink no-underline hover:text-rubric hover:underline"
        >
          {source.topic}
          {source.page ? ` · p${source.page}` : ""}
        </Link>
      ))}
    </div>
  );
}
