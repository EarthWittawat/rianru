import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", () => ({ getConcept: vi.fn() }));

import { getConcept } from "@/lib/api";
import { ConceptPanel } from "@/components/ConceptPanel";

const CONCEPT = {
  name: "backreference",
  type: "concept",
  summary: "A backreference reuses an earlier capture group.",
  example: "The pattern (ab)+ then a backreference matches ababab.",
  requires: [],
  sources: [],
};

describe("ConceptPanel", () => {
  beforeEach(() => {
    // The panel only leaves its loading state when the answer matches the
    // concept it asked for, so the mock has to echo the name back.
    vi.mocked(getConcept).mockImplementation((name: string) =>
      Promise.resolve({ ...CONCEPT, name }),
    );
  });

  it("brings itself into view when a concept is picked", async () => {
    const scrollIntoView = vi.fn();
    // jsdom implements neither, so both are installed for the assertion.
    Element.prototype.scrollIntoView = scrollIntoView;

    const { rerender } = render(<ConceptPanel name={null} onSelect={() => {}} />);
    expect(scrollIntoView).not.toHaveBeenCalled();

    rerender(<ConceptPanel name="backreference" onSelect={() => {}} />);

    await waitFor(() => expect(scrollIntoView).toHaveBeenCalled());
  });

  it("starts the new concept at the top rather than where the last one was left", async () => {
    Element.prototype.scrollIntoView = vi.fn();

    const { container, rerender } = render(
      <ConceptPanel name="regex" onSelect={() => {}} />,
    );
    await waitFor(() => screen.getByText(CONCEPT.summary));

    const scroller = container.querySelector(".overflow-y-auto") as HTMLElement;
    scroller.scrollTop = 400;

    rerender(<ConceptPanel name="backreference" onSelect={() => {}} />);

    await waitFor(() => expect(scroller.scrollTop).toBe(0));
  });

  it("stays put while nothing is selected", () => {
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;

    render(<ConceptPanel name={null} onSelect={() => {}} />);

    expect(scrollIntoView).not.toHaveBeenCalled();
  });
});
