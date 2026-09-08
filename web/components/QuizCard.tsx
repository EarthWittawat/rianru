"use client";

import { useState } from "react";
import { recordAttempt, type QuizQuestion } from "@/lib/api";
import { Markdown } from "@/components/Markdown";

export function QuizCard({
  question,
  index,
  onRecorded,
}: {
  question: QuizQuestion;
  index: number;
  onRecorded?: () => void;
}) {
  const [choice, setChoice] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [selfGraded, setSelfGraded] = useState<boolean | null>(null);
  const [saveFailed, setSaveFailed] = useState(false);

  const isMultipleChoice = question.format === "multiple_choice";
  const checked = revealed || (isMultipleChoice && choice !== null);

  async function report(grade: { chosen_answer: string } | { self_grade: boolean }) {
    setSaveFailed(false);
    try {
      await recordAttempt(question.id, grade);
      onRecorded?.();
    } catch {
      // The answer still shows, but it will not count towards weak areas.
      setSaveFailed(true);
    }
  }

  function pick(option: string) {
    setChoice(option);
    report({ chosen_answer: option });
  }

  function selfGrade(gotIt: boolean) {
    setSelfGraded(gotIt);
    report({ self_grade: gotIt });
  }

  return (
    <li className="border-t border-rule py-6">
      <div className="flex gap-5">
        <span className="apparatus tabular w-6 shrink-0 pt-1 text-ash">
          {String(index + 1).padStart(2, "0")}
        </span>
        <div className="min-w-0 flex-1">
          <p className="max-w-[62ch]">{question.question}</p>

          {isMultipleChoice ? (
            <ul className="mt-4 space-y-1.5">
              {question.options.map((option) => {
                const isAnswer = option === question.answer;
                const isPicked = option === choice;
                return (
                  <li key={option}>
                    <button
                      onClick={() => pick(option)}
                      disabled={choice !== null}
                      className={`w-full border px-3 py-2 text-left text-fine transition-colors ${optionStyle(
                        { checked, isAnswer, isPicked },
                      )}`}
                    >
                      <span className="flex items-baseline gap-3">
                        <span aria-hidden className="apparatus w-4 shrink-0">
                          {checked && isAnswer ? "✓" : checked && isPicked ? "✗" : ""}
                        </span>
                        {option}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          ) : (
            <div className="mt-4">
              {!revealed ? (
                <button
                  onClick={() => setRevealed(true)}
                  className="detent px-3 py-1.5 text-fine"
                >
                  Show answer
                </button>
              ) : (
                <>
                  <p className="bracketed max-w-[62ch] text-fine">
                    {question.answer}
                  </p>
                  <div className="mt-4 flex items-center gap-3">
                    {selfGraded === null ? (
                      <>
                        <span className="apparatus">Did you get it?</span>
                        <button
                          onClick={() => selfGrade(true)}
                          className="detent px-2.5 py-1 text-fine"
                        >
                          I got it
                        </button>
                        <button
                          onClick={() => selfGrade(false)}
                          className="detent px-2.5 py-1 text-fine"
                        >
                          I missed it
                        </button>
                      </>
                    ) : (
                      <span
                        className={`apparatus ${selfGraded ? "text-slate" : "text-rubric"}`}
                      >
                        {selfGraded ? "Marked as correct" : "Marked as missed"}
                      </span>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {saveFailed && (
            <p className="mt-3 text-fine text-rubric-deep">
              Could not save that answer, so it will not count towards your weak areas.
            </p>
          )}

          {checked && question.explanation && (
            <div className="bracketed mt-4 max-w-[62ch] text-fine text-slate">
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
  if (!checked) return "border-rule hover:border-ink";
  if (isAnswer) return "border-ink bg-paper-lift text-ink";
  if (isPicked) return "border-rubric text-rubric-deep";
  return "border-rule text-ash";
}
