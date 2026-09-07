"use client";

import { useCallback } from "react";
import type { DocumentChunk } from "@/lib/api";
import type { Selection } from "@/components/PdfPane";

type Props = {
  chunks: DocumentChunk[];
  onSelect: (selection: Selection | null) => void;
};

/** Renders notebook and markdown documents, which have no PDF to paginate. */
export function TextPane({ chunks, onSelect }: Props) {
  const handleSelection = useCallback(() => {
    const text = window.getSelection()?.toString().trim() ?? "";
    onSelect(text ? { text, page: 0 } : null);
  }, [onSelect]);

  return (
    <div
      onMouseUp={handleSelection}
      className="flex-1 overflow-y-auto bg-neutral-100 px-4 py-6"
    >
      <div className="mx-auto max-w-3xl space-y-3">
        {chunks.map((chunk) => (
          <article
            key={chunk.id}
            className="rounded-md bg-white p-5 shadow-sm ring-1 ring-neutral-200"
          >
            {chunk.cell_index !== null && (
              <span className="mb-2 block font-mono text-xs text-neutral-400">
                cell {chunk.cell_index}
              </span>
            )}
            <pre className="whitespace-pre-wrap break-words font-mono text-sm leading-relaxed text-neutral-800">
              {chunk.text}
            </pre>
          </article>
        ))}
      </div>
    </div>
  );
}
