import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

/**
 * jsdom has no layout, so it implements neither of these. Components that ask
 * whether they are on a wide screen, or that scroll themselves into view, would
 * otherwise throw before their behaviour could be asserted.
 *
 * The default answer is "wide screen", matching the desktop layout. A test that
 * cares about the stacked layout overrides matchMedia itself.
 */
window.matchMedia = vi.fn().mockImplementation((query: string) => ({
  matches: true,
  media: query,
  onchange: null,
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  addListener: vi.fn(),
  removeListener: vi.fn(),
  dispatchEvent: vi.fn(),
}));

Element.prototype.scrollIntoView = vi.fn();
