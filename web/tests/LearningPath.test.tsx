import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", () => ({
  getLearningPath: vi.fn(),
  getConcept: vi.fn(),
}));

import { getConcept, getLearningPath } from "@/lib/api";
import { LearningPath } from "@/components/LearningPath";

const PATH = {
  stages: [
    {
      topic: "Pattern Matching",
      position: 1,
      concepts: [
        { name: "regex", type: "concept", mentions: 9, depth: 0, explained: true },
        { name: "backreference", type: "concept", mentions: 3, depth: 1, explained: false },
      ],
    },
  ],
  edges: [
    {
      source: "backreference",
      target: "regex",
      reason: "A backreference refers to a group a regex already matched.",
      origin: "timeline" as const,
    },
  ],
};

const CONCEPT = {
  name: "backreference",
  type: "concept",
  summary: "A backreference reuses an earlier capture group.",
  example: "The pattern (ab)+ then a backreference matches ababab.",
  requires: [
    {
      name: "regex",
      reason: "A backreference refers to a group a regex already matched.",
      origin: "timeline",
    },
  ],
  sources: [
    {
      document_id: "L2",
      document_title: "Pattern Matching — L2.pdf",
      topic: "Pattern Matching",
      page: 7,
    },
    {
      document_id: "L2",
      document_title: "Pattern Matching — L2.pdf",
      topic: "Pattern Matching",
      page: 9,
    },
  ],
};

describe("LearningPath", () => {
  beforeEach(() => {
    vi.mocked(getLearningPath).mockResolvedValue(PATH);
    vi.mocked(getConcept).mockResolvedValue(CONCEPT);
  });

  it("lists stages with their concepts", async () => {
    render(<LearningPath />);

    await waitFor(() => expect(screen.getByText("Pattern Matching")).toBeInTheDocument());
    expect(screen.getByText("regex")).toBeInTheDocument();
    expect(screen.getByText("backreference")).toBeInTheDocument();
  });

  it("says how many prerequisites a concept has", async () => {
    render(<LearningPath />);

    await waitFor(() => expect(screen.getByText("needs 1")).toBeInTheDocument());
  });

  it("explains a concept when it is picked, with its example and prerequisite", async () => {
    render(<LearningPath />);
    await waitFor(() => screen.getByText("backreference"));

    await userEvent.click(screen.getByText("backreference"));

    await waitFor(() =>
      expect(
        screen.getByText("A backreference reuses an earlier capture group."),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText("The pattern (ab)+ then a backreference matches ababab.")).toBeInTheDocument();
    expect(
      screen.getByText("A backreference refers to a group a regex already matched."),
    ).toBeInTheDocument();
    // One row for the document, its pages gathered onto it.
    expect(screen.getByText("Pattern Matching — L2.pdf")).toBeInTheDocument();
    expect(screen.getByText("pages 7, 9")).toBeInTheDocument();
  });

  it("says it is working while the path loads", async () => {
    let release: (value: typeof PATH) => void = () => {};
    vi.mocked(getLearningPath).mockReturnValue(
      new Promise((resolve) => (release = resolve)),
    );

    render(<LearningPath />);

    expect(screen.getByText(/laying out the course/i)).toBeInTheDocument();

    release(PATH);
    await waitFor(() =>
      expect(screen.queryByText(/laying out the course/i)).not.toBeInTheDocument(),
    );
  });

  it("reports a failure instead of rendering an empty path", async () => {
    vi.mocked(getLearningPath).mockRejectedValue(new Error("offline"));

    render(<LearningPath />);

    await waitFor(() =>
      expect(screen.getByText(/could not load the path/i)).toBeInTheDocument(),
    );
  });
});
