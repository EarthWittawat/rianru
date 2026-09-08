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
      <div className="flex-1 bg-paper py-16 text-center text-fine text-slate">
        Opening the document…
      </div>
    ),
  },
);

export function DocumentReader({ document }: { document: DocumentDetail }) {
  const [selection, setSelection] = useState<Selection | null>(null);
  const [keys, setKeys] = useState<string[]>([]);
  const [activeKey, setActiveKey] = useState("1");

  const handleSelect = useCallback((next: Selection | null) => {
    if (next) setSelection(next);
  }, []);

  const handleKeys = useCallback((next: string[]) => setKeys(next), []);
  const handleActiveKey = useCallback((next: string) => setActiveKey(next), []);

  return (
    <div className="flex flex-1 flex-col overflow-hidden lg:flex-row">
      {document.file_type === "pdf" ? (
        <PdfPane
          fileUrl={documentFileUrl(document.id)}
          onSelect={handleSelect}
          onKeys={handleKeys}
          onActiveKey={handleActiveKey}
        />
      ) : (
        <TextPane
          chunks={document.chunks}
          onSelect={handleSelect}
          onKeys={handleKeys}
        />
      )}
      <KeyRail keys={keys} activeKey={activeKey} />
      <ExplainPanel
        document={document}
        selection={selection}
        onClear={() => setSelection(null)}
      />
    </div>
  );
}

/**
 * The centre rail: one key per page or cell, marking where the reader is and
 * carrying them anywhere in the document without leaving it.
 */
function KeyRail({ keys, activeKey }: { keys: string[]; activeKey: string }) {
  if (keys.length < 2) return null;

  return (
    <nav
      aria-label="Pages"
      className="hidden w-12 shrink-0 overflow-y-auto border-l border-rule bg-paper py-6 md:block"
    >
      <ul className="flex flex-col items-center gap-1">
        {keys.map((key) => {
          const active = key === activeKey;
          return (
            <li key={key}>
              <a
                href={`#key-${key}`}
                aria-current={active ? "true" : undefined}
                className={`apparatus tabular block px-2 py-0.5 no-underline transition-colors ${
                  active
                    ? "bg-rubric text-paper"
                    : "text-ash hover:text-ink"
                }`}
              >
                {key}
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
