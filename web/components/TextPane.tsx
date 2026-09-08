"use client";

import { useCallback, useEffect } from "react";
import type { DocumentChunk } from "@/lib/api";
import type { Selection } from "@/components/PdfPane";
import { CodeBlock } from "@/components/CodeBlock";
import { Markdown } from "@/components/Markdown";

type Props = {
  chunks: DocumentChunk[];
  onSelect: (selection: Selection | null) => void;
  onKeys?: (keys: string[]) => void;
};

/** Renders notebook and markdown documents, which have no PDF to paginate. */
export function TextPane({ chunks, onSelect, onKeys }: Props) {
  const handleSelection = useCallback(() => {
    const text = window.getSelection()?.toString().trim() ?? "";
    onSelect(text ? { text, page: 0 } : null);
  }, [onSelect]);

  useEffect(() => {
    if (!onKeys) return;
    onKeys(chunks.map((_, index) => String(index + 1)));
  }, [chunks, onKeys]);

  return (
    <div
      onMouseUp={handleSelection}
      className="flex-1 overflow-y-auto bg-paper px-8 py-8"
    >
      <div className="mx-auto max-w-[68ch] space-y-6">
        {chunks.map((chunk, index) => (
          <Cell key={chunk.id} chunk={chunk} index={index} />
        ))}
      </div>
    </div>
  );
}

function Cell({ chunk, index }: { chunk: DocumentChunk; index: number }) {
  const isCode = chunk.cell_type === "code";

  return (
    <article id={`key-${index + 1}`} className="border-t border-rule pt-4">
      {chunk.cell_index !== null && (
        <p className="apparatus tabular mb-2">
          {isCode ? "In" : "Md"} [{chunk.cell_index}]
        </p>
      )}
      {isCode ? (
        <CodeBlock code={chunk.text} showLineNumbers />
      ) : (
        <Markdown>{chunk.text}</Markdown>
      )}
    </article>
  );
}
