"use client";

import { useEffect, useRef, useState } from "react";
import {
  explainSelection,
  listHighlights,
  saveHighlight,
  type DocumentDetail,
  type Explanation,
  type Highlight,
} from "@/lib/api";
import type { Selection } from "@/components/PdfPane";
import { Markdown } from "@/components/Markdown";

type Status = "idle" | "loading" | "ready" | "error";
type SaveStatus = "idle" | "saving" | "saved" | "error";

type Props = {
  document: DocumentDetail;
  selection: Selection | null;
  onClear: () => void;
};

/**
 * The annotation margin. Everything the reader adds to the page happens here,
 * bracketed back to the line it came from.
 */
export function ExplainPanel({ document, selection, onClear }: Props) {
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<Explanation | null>(null);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [error, setError] = useState("");
  const [kept, setKept] = useState<Highlight[]>([]);
  const [keptVersion, setKeptVersion] = useState(0);
  const asideRef = useRef<HTMLElement | null>(null);
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  // When the selection changes, bring the new content into view: reset the
  // inner scroller and, below lg, scroll the whole panel up to the reader.
  useEffect(() => {
    if (!selection) return;
    if (scrollerRef.current) scrollerRef.current.scrollTop = 0;

    // On a wide screen the panel is sticky and already in view, so scrolling
    // the window would only throw the reader's place away. Stacked under the
    // content, it genuinely is off-screen and has to come up.
    const stacked = !window.matchMedia("(min-width: 1024px)").matches;
    if (stacked) {
      asideRef.current?.scrollIntoView?.({ behavior: "smooth", block: "nearest" });
    }
  }, [selection]);

  // The margin should not be empty on arrival: what was kept here before
  // belongs in it as much as what is being read now.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const all = await listHighlights();
        if (!cancelled) setKept(all.filter((h) => h.document_id === document.id));
      } catch {
        if (!cancelled) setKept([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [document.id, keptVersion]);

  async function handleExplain() {
    if (!selection) return;
    setStatus("loading");
    setSaveStatus("idle");
    setError("");
    try {
      const explanation = await explainSelection(
        document.id,
        selection.text,
        selection.page || null,
      );
      setResult(explanation);
      setStatus("ready");
    } catch {
      setStatus("error");
      setError("The tutor could not be reached. Is the backend running?");
    }
  }

  async function handleSave() {
    if (!result) return;
    setSaveStatus("saving");
    try {
      await saveHighlight(result.chunk_id, result.selected_text, result.explanation);
      setSaveStatus("saved");
      setKeptVersion((v) => v + 1);
    } catch {
      setSaveStatus("error");
    }
  }

  return (
    <aside
      ref={asideRef}
      className="flex max-h-[45vh] w-full shrink-0 flex-col border-t border-rule bg-paper-lift lg:sticky lg:top-0 lg:h-screen lg:max-h-none lg:w-[22rem] lg:border-t-0 lg:border-l xl:w-[26rem]"
    >
      <div className="border-b border-rule px-6 py-4">
        <h2 className="apparatus text-slate">Annotation</h2>
      </div>

      <div ref={scrollerRef} className="flex-1 overflow-y-auto px-6 py-5">
        {!selection && (
          <p className="text-fine text-slate">
            Drag across any passage to bring it into the margin.
          </p>
        )}

        {!selection && kept.length > 0 && (
          <section className="mt-8 border-t border-rule pt-4">
            <h3 className="apparatus tabular">Kept here · {kept.length}</h3>
            <ul className="mt-3 space-y-4">
              {kept.map((highlight) => (
                <li key={highlight.id}>
                  <p className="bracketed text-fine text-ink italic">
                    {highlight.selected_text}
                  </p>
                  <p className="apparatus tabular mt-1.5">
                    {highlight.page ? `page ${highlight.page}` : "no page"}
                  </p>
                </li>
              ))}
            </ul>
          </section>
        )}

        {selection && (
          <>
            <blockquote className="bracketed text-fine text-slate italic">
              {selection.text}
            </blockquote>
            <div className="mt-4 flex gap-2">
              <button
                onClick={handleExplain}
                disabled={status === "loading"}
                className="detent px-3 py-1.5 text-fine"
              >
                {status === "loading" ? "Reading…" : "Explain this"}
              </button>
              <button
                onClick={() => {
                  onClear();
                  setResult(null);
                  setStatus("idle");
                  setSaveStatus("idle");
                }}
                className="px-2 py-1.5 text-fine text-slate underline decoration-rule hover:text-ink"
              >
                Clear
              </button>
            </div>
          </>
        )}

        {status === "error" && (
          <p className="ruled-block mt-5 border-rubric px-3 py-2 text-fine text-rubric-deep">
            {error}
          </p>
        )}

        {status === "loading" && (
          <div className="mt-6 space-y-2" aria-hidden>
            <span className="block h-3 w-full bg-paper-deep" />
            <span className="block h-3 w-11/12 bg-paper-deep" />
            <span className="block h-3 w-9/12 bg-paper-deep" />
          </div>
        )}

        {status === "ready" && result && (
          <div className="mt-6 border-t border-rule pt-5">
            <div className="text-fine leading-relaxed">
              <Markdown>{result.explanation}</Markdown>
            </div>

            <p className="apparatus tabular mt-4">
              {result.topic}
              {result.page ? ` · page ${result.page}` : ""}
            </p>

            <button
              onClick={handleSave}
              disabled={saveStatus === "saving" || saveStatus === "saved"}
              data-state={saveStatus === "saved" ? "on" : undefined}
              className="detent mt-4 w-full px-3 py-2 text-fine"
            >
              {saveStatus === "saved"
                ? "Kept in your graph"
                : saveStatus === "saving"
                  ? "Keeping…"
                  : "Save as highlight"}
            </button>
            {saveStatus === "error" && (
              <p className="mt-2 text-fine text-rubric-deep">
                Could not save that highlight. Try again.
              </p>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
