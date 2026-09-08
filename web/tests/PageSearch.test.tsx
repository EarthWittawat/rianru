import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api", () => ({ searchPages: vi.fn() }));

import { searchPages } from "@/lib/api";
import { PageSearch } from "@/components/PageSearch";

const HIT = {
  document_id: "CPE393::11005576::L3.pdf",
  document_title: "Textual Data Visualization — L3.pdf",
  page: 21,
  score: 13.5,
};

describe("PageSearch", () => {
  beforeEach(() => {
    vi.mocked(searchPages).mockResolvedValue({ indexed: true, hits: [HIT] });
  });

  it("links a hit to that page of the document", async () => {
    render(<PageSearch />);

    await userEvent.type(
      screen.getByLabelText("Find a page"),
      "a bar chart of word frequencies",
    );
    await userEvent.click(screen.getByRole("button", { name: /search pages/i }));

    await waitFor(() =>
      expect(
        screen.getByRole("link", { name: /Textual Data Visualization/ }),
      ).toHaveAttribute(
        "href",
        `/viewer/${encodeURIComponent(HIT.document_id)}#key-21`,
      ),
    );
    expect(screen.getByText("page 21")).toBeInTheDocument();
  });

  it("groups repeated hits from one document behind its best page", async () => {
    vi.mocked(searchPages).mockResolvedValue({
      indexed: true,
      hits: [HIT, { ...HIT, page: 20, score: 13.2 }, { ...HIT, page: 23, score: 12.8 }],
    });

    render(<PageSearch />);
    await userEvent.type(screen.getByLabelText("Find a page"), "a chart");
    await userEvent.click(screen.getByRole("button", { name: /search pages/i }));

    await waitFor(() => expect(screen.getByText("page 21")).toBeInTheDocument());
    expect(
      screen.getAllByRole("link", { name: /Textual Data Visualization/ }),
    ).toHaveLength(1);
    expect(screen.getByRole("link", { name: "20" })).toHaveAttribute(
      "href",
      `/viewer/${encodeURIComponent(HIT.document_id)}#key-20`,
    );
  });

  it("tells you how to build the index when the class has none", async () => {
    vi.mocked(searchPages).mockResolvedValue({ indexed: false, hits: [] });

    render(<PageSearch />);
    await userEvent.type(screen.getByLabelText("Find a page"), "a chart");
    await userEvent.click(screen.getByRole("button", { name: /search pages/i }));

    await waitFor(() =>
      expect(screen.getByText(/build_colpali\.py/)).toBeInTheDocument(),
    );
  });

  it("says nothing matched rather than showing an empty list", async () => {
    vi.mocked(searchPages).mockResolvedValue({ indexed: true, hits: [] });

    render(<PageSearch />);
    await userEvent.type(screen.getByLabelText("Find a page"), "a unicorn");
    await userEvent.click(screen.getByRole("button", { name: /search pages/i }));

    await waitFor(() =>
      expect(screen.getByText(/nothing in this class looks like that/i)).toBeInTheDocument(),
    );
  });

  it("reports a failure instead of pretending there were no results", async () => {
    vi.mocked(searchPages).mockRejectedValue(new Error("offline"));

    render(<PageSearch />);
    await userEvent.type(screen.getByLabelText("Find a page"), "a chart");
    await userEvent.click(screen.getByRole("button", { name: /search pages/i }));

    await waitFor(() =>
      expect(screen.getByText(/page search is unavailable/i)).toBeInTheDocument(),
    );
  });
});
