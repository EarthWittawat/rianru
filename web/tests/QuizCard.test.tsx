import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { QuizCard } from "@/components/QuizCard";
import type { QuizQuestion } from "@/lib/api";

const recordAttempt = vi.fn();
vi.mock("@/lib/api", () => ({
  recordAttempt: (...args: unknown[]) => recordAttempt(...args),
}));

beforeEach(() => {
  recordAttempt.mockReset();
  recordAttempt.mockResolvedValue({
    is_correct: true,
    correct_answer: "Common terms",
    graded_by: "auto",
  });
});

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

  it("records the picked option so it counts towards weak areas", async () => {
    render(<QuizCard question={MULTIPLE_CHOICE} index={0} />);

    await userEvent.click(screen.getByRole("button", { name: "Rare terms" }));

    await waitFor(() =>
      expect(recordAttempt).toHaveBeenCalledWith("q1", { chosen_answer: "Rare terms" }),
    );
  });

  it("says so when an answer could not be saved", async () => {
    recordAttempt.mockRejectedValue(new Error("offline"));
    render(<QuizCard question={MULTIPLE_CHOICE} index={0} />);

    await userEvent.click(screen.getByRole("button", { name: "Rare terms" }));

    await waitFor(() =>
      expect(screen.getByText(/could not save that answer/i)).toBeInTheDocument(),
    );
  });

  it("reveals a short answer on demand", async () => {
    render(<QuizCard question={SHORT_ANSWER} index={0} />);

    expect(screen.queryByText(SHORT_ANSWER.answer)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Show answer" }));

    expect(screen.getByText(SHORT_ANSWER.answer)).toBeInTheDocument();
    expect(screen.getByText(SHORT_ANSWER.explanation)).toBeInTheDocument();
  });

  it("records a self-grade for a short answer", async () => {
    render(<QuizCard question={SHORT_ANSWER} index={0} />);

    await userEvent.click(screen.getByRole("button", { name: "Show answer" }));
    await userEvent.click(screen.getByRole("button", { name: "I missed it" }));

    await waitFor(() =>
      expect(recordAttempt).toHaveBeenCalledWith("q2", { self_grade: false }),
    );
    expect(screen.getByText("Marked as missed")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "I got it" })).not.toBeInTheDocument();
  });

  it("does not offer self-grading before the answer is revealed", () => {
    render(<QuizCard question={SHORT_ANSWER} index={0} />);

    expect(screen.queryByRole("button", { name: "I got it" })).not.toBeInTheDocument();
  });
});
