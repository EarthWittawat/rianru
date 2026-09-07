"use client";

import { useState } from "react";
import {
  explainSelection,
  saveHighlight,
  type DocumentDetail,
  type Explanation,
} from "@/lib/api";
import type { Selection } from "@/components/PdfPane";

type Status = "idle" | "loading" | "ready" | "error";
type SaveStatus = "idle" | "saving" | "saved" | "error";

type Props = {
  document: DocumentDetail;
  selection: Selection | null;
  onClear: () => void;
};

export function ExplainPanel({ document, selection, onClear }: Props) {
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<Explanation | null>(null);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [error, setError] = useState("");

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
    } catch {
      setSaveStatus("error");
    }
  }

  return (
    <aside className="flex w-96 shrink-0 flex-col border-l border-neutral-200 bg-white">
      <div className="border-b border-neutral-200 px-5 py-4">
        <h2 className="text-sm font-medium">Explain</h2>
        <p className="mt-1 text-xs text-neutral-500">
          Select any passage in the document, then ask for an explanation.
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        {!selection && (
          <p className="text-sm text-neutral-500">Nothing selected yet.</p>
        )}

        {selection && (
          <>
            <blockquote className="border-l-2 border-neutral-300 pl-3 text-sm text-neutral-700">
              {selection.text}
            </blockquote>
            <div className="mt-3 flex gap-2">
              <button
                onClick={handleExplain}
                disabled={status === "loading"}
                className="rounded-md bg-neutral-900 px-3 py-1.5 text-sm text-white transition-colors hover:bg-neutral-700 disabled:opacity-50"
              >
                {status === "loading" ? "Thinking…" : "Explain this"}
              </button>
              <button
                onClick={() => {
                  onClear();
                  setResult(null);
                  setStatus("idle");
                  setSaveStatus("idle");
                }}
                className="rounded-md px-3 py-1.5 text-sm text-neutral-600 transition-colors hover:bg-neutral-100"
              >
                Clear
              </button>
            </div>
          </>
        )}

        {status === "error" && (
          <p className="mt-4 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
            {error}
          </p>
        )}

        {status === "ready" && result && (
          <div className="mt-6">
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-800">
              {result.explanation}
            </p>
            <p className="mt-3 text-xs text-neutral-500">
              From {result.topic}
              {result.page ? ` · page ${result.page}` : ""}
            </p>

            <button
              onClick={handleSave}
              disabled={saveStatus === "saving" || saveStatus === "saved"}
              className="mt-4 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm transition-colors hover:bg-neutral-50 disabled:opacity-60"
            >
              {saveStatus === "saved"
                ? "Saved to your graph"
                : saveStatus === "saving"
                  ? "Saving…"
                  : "Save as highlight"}
            </button>
            {saveStatus === "error" && (
              <p className="mt-2 text-xs text-red-600">
                Could not save that highlight. Try again.
              </p>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
