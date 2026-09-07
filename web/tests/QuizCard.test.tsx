import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { QuizCard } from "@/components/QuizCard";
import type { QuizQuestion } from "@/lib/api";

const MULTIPLE_CHOICE: QuizQuestion = {
  id: "q1",
  format: "multiple_choice",
  question: "What does IDF down-weight?",
  options: ["Rare terms", "Common terms"],
  answer: "Common terms",
  explanation: "IDF penalises terms appearing in many documents.",
};

const SHORT_ANSWER: QuizQuestion = {
  id: "q2",
  format: "short_answer",
  question: "Name the two factors in TF-IDF.",
  options: [],
  answer: "Term frequency and inverse document frequency.",
  explanation: "TF multiplied by IDF.",
};

describe("QuizCard", () => {
  it("hides the answer until an option is picked", async () => {
    render(<QuizCard question={MULTIPLE_CHOICE} index={0} />);

    expect(screen.queryByText(MULTIPLE_CHOICE.explanation)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Rare terms" }));

    expect(screen.getByText(MULTIPLE_CHOICE.explanation)).toBeInTheDocument();
  });

  it("locks the options once one is chosen", async () => {
    render(<QuizCard question={MULTIPLE_CHOICE} index={0} />);

    await userEvent.click(screen.getByRole("button", { name: "Rare terms" }));

    expect(screen.getByRole("button", { name: "Common terms" })).toBeDisabled();
  });

  it("reveals a short answer on demand", async () => {
    render(<QuizCard question={SHORT_ANSWER} index={0} />);

    expect(screen.queryByText(SHORT_ANSWER.answer)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Show answer" }));

    expect(screen.getByText(SHORT_ANSWER.answer)).toBeInTheDocument();
    expect(screen.getByText(SHORT_ANSWER.explanation)).toBeInTheDocument();
  });
});
