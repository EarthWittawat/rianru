import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { StudyPlan } from "@/components/StudyPlan";

const { generatePlan, getLatestPlan, setTaskDone } = vi.hoisted(() => ({
  generatePlan: vi.fn(),
  getLatestPlan: vi.fn(),
  setTaskDone: vi.fn(),
}));
vi.mock("@/lib/api", () => ({ generatePlan, getLatestPlan, setTaskDone }));

const PLAN = {
  id: "p1",
  created_at: "2026-09-08T00:00:00Z",
  tasks: [
    {
      id: "t1",
      action: "Redo the TF-IDF worked example",
      topic: "Textual Feature Representation",
      source: { document_title: "L6 - Text Feature Representation.pdf", page: 19 },
      why: "you scored 2/7 here",
      est_minutes: 25,
      done: false,
    },
  ],
};

beforeEach(() => {
  generatePlan.mockReset();
  getLatestPlan.mockReset();
  setTaskDone.mockReset();
  getLatestPlan.mockResolvedValue(PLAN);
  setTaskDone.mockResolvedValue({ id: "t1", done: true });
});

describe("StudyPlan", () => {
  it("shows the existing plan with its source and reasoning", async () => {
    render(<StudyPlan />);

    await waitFor(() =>
      expect(screen.getByText("Redo the TF-IDF worked example")).toBeInTheDocument(),
    );
    expect(screen.getByText(/L6 - Text Feature Representation\.pdf, p19/)).toBeInTheDocument();
    expect(screen.getByText("you scored 2/7 here")).toBeInTheDocument();
  });

  it("shows a pending state while the coach works", async () => {
    let release: (value: typeof PLAN) => void = () => {};
    generatePlan.mockReturnValue(new Promise((resolve) => (release = resolve)));

    render(<StudyPlan />);
    await userEvent.click(screen.getByRole("button", { name: /plan my study/i }));

    expect(screen.getByText(/working through your results/i)).toBeInTheDocument();
    expect(screen.getByText(/takes up to a minute/i)).toBeInTheDocument();

    release(PLAN);
    await waitFor(() =>
      expect(screen.queryByText(/working through your results/i)).not.toBeInTheDocument(),
    );
  });

  it("ticks a task off and persists it", async () => {
    render(<StudyPlan />);
    await waitFor(() => screen.getByRole("checkbox"));

    await userEvent.click(screen.getByRole("checkbox"));

    await waitFor(() => expect(setTaskDone).toHaveBeenCalledWith("t1", true));
    expect(screen.getByRole("checkbox")).toBeChecked();
  });

  it("un-ticks a task if saving it failed", async () => {
    setTaskDone.mockImplementation(async () => {
      throw new Error("offline");
    });
    render(<StudyPlan />);
    await waitFor(() => screen.getByRole("checkbox"));

    await userEvent.click(screen.getByRole("checkbox"));

    // A tick that was never saved would be a lie about your own progress.
    await waitFor(() => expect(screen.getByRole("checkbox")).not.toBeChecked());
  });
});
