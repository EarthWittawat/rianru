import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { TextPane } from "@/components/TextPane";
import type { DocumentChunk } from "@/lib/api";

function chunk(overrides: Partial<DocumentChunk>): DocumentChunk {
  return {
    id: "c",
    text: "",
    page: null,
    cell_index: 0,
    cell_type: null,
    index: 0,
    ...overrides,
  };
}

describe("TextPane", () => {
  it("highlights code cells rather than printing them flat", () => {
    render(
      <TextPane
        chunks={[
          chunk({
            id: "c1",
            cell_type: "code",
            text: "import re\nmatch = re.search(r'\\d+', text)",
          }),
        ]}
        onSelect={vi.fn()}
      />,
    );

    // The highlighter splits keywords into their own spans; flat text would not.
    expect(screen.getByText("import")).toBeInTheDocument();
    expect(screen.getByText("In [0]")).toBeInTheDocument();
  });

  it("renders markdown cells as markdown, not raw syntax", () => {
    render(
      <TextPane
        chunks={[
          chunk({
            id: "c2",
            cell_index: 1,
            cell_type: "markdown",
            text: "# Loading data\n\nUse **pandas** to read the file.",
          }),
        ]}
        onSelect={vi.fn()}
      />,
    );

    expect(screen.getByText("Loading data")).toBeInTheDocument();
    expect(screen.getByText("pandas").tagName).toBe("STRONG");
    expect(screen.queryByText(/\*\*pandas\*\*/)).not.toBeInTheDocument();
    expect(screen.getByText("Md [1]")).toBeInTheDocument();
  });
});
