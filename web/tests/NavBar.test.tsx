import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { NavBar } from "@/components/NavBar";

const mockPathname = vi.fn(() => "/");
vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname(),
}));

describe("NavBar", () => {
  it("links to every section", () => {
    render(<NavBar />);
    for (const label of ["Read", "Path", "Tutor", "Quiz", "Coach"]) {
      expect(screen.getByRole("link", { name: label })).toBeInTheDocument();
    }
  });

  it("marks the active section for a nested route", () => {
    mockPathname.mockReturnValue("/viewer/some-doc-id");
    render(<NavBar />);
    expect(screen.getByRole("link", { name: "Read" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Path" })).not.toHaveAttribute(
      "aria-current",
    );
  });
});
