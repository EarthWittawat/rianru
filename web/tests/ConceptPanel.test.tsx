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

function setViewport(wide: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: wide,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

describe("ConceptPanel", () => {
  beforeEach(() => {
    // The panel only leaves its loading state when the answer matches the
    // concept it asked for, so the mock has to echo the name back.
    vi.mocked(getConcept).mockImplementation((name: string) =>
      Promise.resolve({ ...CONCEPT, name }),
    );
    vi.mocked(Element.prototype.scrollIntoView).mockClear();
    setViewport(true);
  });

  it("stays put on a wide screen, where it is already beside the content", async () => {
    const { rerender } = render(<ConceptPanel name={null} onSelect={() => {}} />);

    rerender(<ConceptPanel name="backreference" onSelect={() => {}} />);

    await waitFor(() => screen.getByText(CONCEPT.summary));
    expect(Element.prototype.scrollIntoView).not.toHaveBeenCalled();
  });

  it("brings itself up when stacked under the content", async () => {
    setViewport(false);

    const { rerender } = render(<ConceptPanel name={null} onSelect={() => {}} />);
    rerender(<ConceptPanel name="backreference" onSelect={() => {}} />);

    await waitFor(() => expect(Element.prototype.scrollIntoView).toHaveBeenCalled());
  });

  it("starts the new concept at the top rather than where the last one was left", async () => {
    const { container, rerender } = render(
      <ConceptPanel name="regex" onSelect={() => {}} />,
    );
    await waitFor(() => screen.getByText(CONCEPT.summary));

    const scroller = container.querySelector(".overflow-y-auto") as HTMLElement;
    scroller.scrollTop = 400;

    rerender(<ConceptPanel name="backreference" onSelect={() => {}} />);

    await waitFor(() => expect(scroller.scrollTop).toBe(0));
  });

  it("does nothing at all while nothing is selected", () => {
    setViewport(false);

    render(<ConceptPanel name={null} onSelect={() => {}} />);

    expect(Element.prototype.scrollIntoView).not.toHaveBeenCalled();
  });
});
