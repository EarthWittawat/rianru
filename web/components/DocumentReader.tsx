"use client";

import dynamic from "next/dynamic";
import { useCallback, useState } from "react";
import { documentFileUrl, type DocumentDetail } from "@/lib/api";
import type { Selection } from "@/components/PdfPane";
import { TextPane } from "@/components/TextPane";
import { ExplainPanel } from "@/components/ExplainPanel";

const PdfPane = dynamic(
  () => import("@/components/PdfPane").then((m) => m.PdfPane),
  {
    ssr: false,
    loading: () => (
      <div className="flex-1 bg-neutral-100 py-16 text-center text-sm text-neutral-500">
        Loading viewer…
      </div>
    ),
  },
);

export function DocumentReader({ document }: { document: DocumentDetail }) {
  const [selection, setSelection] = useState<Selection | null>(null);

  const handleSelect = useCallback((next: Selection | null) => {
    if (next) setSelection(next);
  }, []);

  return (
    <div className="flex flex-1 overflow-hidden">
      {document.file_type === "pdf" ? (
        <PdfPane fileUrl={documentFileUrl(document.id)} onSelect={handleSelect} />
      ) : (
        <TextPane chunks={document.chunks} onSelect={handleSelect} />
      )}
      <ExplainPanel
        document={document}
        selection={selection}
        onClear={() => setSelection(null)}
      />
    </div>
  );
}
