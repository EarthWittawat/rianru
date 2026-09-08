import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ChatThread } from "@/components/ChatThread";

const askTutor = vi.fn();
vi.mock("@/lib/api", () => ({
  askTutor: (...args: unknown[]) => askTutor(...args),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

beforeEach(() => {
  askTutor.mockReset();
  Element.prototype.scrollIntoView = vi.fn();
});

describe("ChatThread", () => {
  it("sends the question and renders the grounded answer", async () => {
    askTutor.mockResolvedValue({
      answer: "TF-IDF weights rare terms higher.",
      sources: [
        {
          chunk_id: "c1",
          document_id: "doc-1",
          document_title: "L6",
          topic: "Textual Feature Representation",
          page: 12,
          score: 0.9,
        },
      ],
    });

    render(<ChatThread />);
    await userEvent.type(screen.getByLabelText("Ask the tutor"), "What is TF-IDF?");
    await userEvent.click(screen.getByRole("button", { name: "Ask" }));

    await waitFor(() => {
      expect(screen.getByText("TF-IDF weights rare terms higher.")).toBeInTheDocument();
    });
    expect(screen.getByText("What is TF-IDF?")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /Textual Feature Representation/ }),
    ).toHaveAttribute("href", "/viewer/doc-1");
  });

  it("surfaces a backend failure instead of failing silently", async () => {
    askTutor.mockRejectedValue(new Error("boom"));

    render(<ChatThread />);
    await userEvent.type(screen.getByLabelText("Ask the tutor"), "hello");
    await userEvent.click(screen.getByRole("button", { name: "Ask" }));

    await waitFor(() => {
      expect(screen.getByText(/could not be reached/i)).toBeInTheDocument();
    });
  });

  it("passes prior turns as history on the next question", async () => {
    askTutor.mockResolvedValue({ answer: "First answer.", sources: [] });

    render(<ChatThread />);
    await userEvent.type(screen.getByLabelText("Ask the tutor"), "First question");
    await userEvent.click(screen.getByRole("button", { name: "Ask" }));
    await waitFor(() => expect(screen.getByText("First answer.")).toBeInTheDocument());

    askTutor.mockResolvedValue({ answer: "Second answer.", sources: [] });
    await userEvent.type(screen.getByLabelText("Ask the tutor"), "Second question");
    await userEvent.click(screen.getByRole("button", { name: "Ask" }));

    await waitFor(() => {
      expect(askTutor).toHaveBeenLastCalledWith(
        "Second question",
        [
          { role: "user", content: "First question" },
          { role: "assistant", content: "First answer." },
        ],
        // No class selected outside the provider, so the tutor searches all of them.
        undefined,
      );
    });
  });
});
