"use client";

import { useCallback } from "react";
import type { DocumentChunk } from "@/lib/api";
import type { Selection } from "@/components/PdfPane";
import { CodeBlock } from "@/components/CodeBlock";
import { Markdown } from "@/components/Markdown";

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
          <Cell key={chunk.id} chunk={chunk} />
        ))}
      </div>
    </div>
  );
}

function Cell({ chunk }: { chunk: DocumentChunk }) {
  const isCode = chunk.cell_type === "code";

  return (
    <article className="overflow-hidden rounded-md bg-white shadow-sm ring-1 ring-neutral-200">
      {chunk.cell_index !== null && (
        <div className="flex items-center gap-2 border-b border-neutral-100 px-4 py-1.5">
          <span className="font-mono text-[11px] text-neutral-400">
            {isCode ? "In" : "Md"} [{chunk.cell_index}]
          </span>
        </div>
      )}
      <div className={isCode ? "p-3" : "px-5 py-4"}>
        {isCode ? (
          <CodeBlock code={chunk.text} showLineNumbers />
        ) : (
          <Markdown>{chunk.text}</Markdown>
        )}
      </div>
    </article>
  );
}
