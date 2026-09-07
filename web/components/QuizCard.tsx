"use client";

import { useState } from "react";
import type { QuizQuestion } from "@/lib/api";
import { Markdown } from "@/components/Markdown";

export function QuizCard({
  question,
  index,
}: {
  question: QuizQuestion;
  index: number;
}) {
  const [choice, setChoice] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(false);

  const isMultipleChoice = question.format === "multiple_choice";
  const checked = revealed || (isMultipleChoice && choice !== null);

  return (
    <li className="rounded-lg border border-neutral-200 bg-white p-5">
      <div className="flex gap-3">
        <span className="shrink-0 text-xs text-neutral-400">{index + 1}</span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-neutral-900">{question.question}</p>

          {isMultipleChoice ? (
            <ul className="mt-3 space-y-1.5">
              {question.options.map((option) => {
                const isAnswer = option === question.answer;
                const isPicked = option === choice;
                return (
                  <li key={option}>
                    <button
                      onClick={() => setChoice(option)}
                      disabled={choice !== null}
                      className={`w-full rounded-md border px-3 py-2 text-left text-sm transition-colors ${optionStyle(
                        { checked, isAnswer, isPicked },
                      )}`}
                    >
                      {option}
                    </button>
                  </li>
                );
              })}
            </ul>
          ) : (
            <div className="mt-3">
              {!revealed ? (
                <button
                  onClick={() => setRevealed(true)}
                  className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm transition-colors hover:bg-neutral-50"
                >
                  Show answer
                </button>
              ) : (
                <p className="rounded-md bg-neutral-50 p-3 text-sm text-neutral-800">
                  {question.answer}
                </p>
              )}
            </div>
          )}

          {checked && question.explanation && (
            <div className="mt-3 border-l-2 border-neutral-200 pl-3">
              <Markdown>{question.explanation}</Markdown>
            </div>
          )}
        </div>
      </div>
    </li>
  );
}

function optionStyle({
  checked,
  isAnswer,
  isPicked,
}: {
  checked: boolean;
  isAnswer: boolean;
  isPicked: boolean;
}) {
  if (!checked) return "border-neutral-200 hover:border-neutral-400";
  if (isAnswer) return "border-emerald-500 bg-emerald-50 text-emerald-900";
  if (isPicked) return "border-red-400 bg-red-50 text-red-900";
  return "border-neutral-200 text-neutral-500";
}
