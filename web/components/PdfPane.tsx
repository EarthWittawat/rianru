"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

export type Selection = { text: string; page: number };

type Props = {
  fileUrl: string;
  onSelect: (selection: Selection | null) => void;
};

export function PdfPane({ fileUrl, onSelect }: Props) {
  const [pageCount, setPageCount] = useState(0);
  const [width, setWidth] = useState(760);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => {
      setWidth(Math.min(entry.contentRect.width - 32, 900));
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const handleSelection = useCallback(() => {
    const selection = window.getSelection();
    const text = selection?.toString().trim() ?? "";
    if (!text) {
      onSelect(null);
      return;
    }
    const node = selection?.anchorNode;
    const pageElement =
      node instanceof Element
        ? node.closest("[data-page-number]")
        : node?.parentElement?.closest("[data-page-number]");
    const page = Number(pageElement?.getAttribute("data-page-number") ?? 1);
    onSelect({ text, page });
  }, [onSelect]);

  return (
    <div
      ref={containerRef}
      onMouseUp={handleSelection}
      className="flex-1 overflow-y-auto bg-neutral-100 px-4 py-6"
    >
      <Document
        file={fileUrl}
        onLoadSuccess={({ numPages }) => setPageCount(numPages)}
        loading={<PaneMessage>Loading document…</PaneMessage>}
        error={<PaneMessage>Could not load this PDF.</PaneMessage>}
        className="flex flex-col items-center gap-4"
      >
        {Array.from({ length: pageCount }, (_, index) => (
          <div
            key={index}
            data-page-number={index + 1}
            className="overflow-hidden rounded-md bg-white shadow-sm ring-1 ring-neutral-200"
          >
            <Page
              pageNumber={index + 1}
              width={width}
              renderTextLayer
              renderAnnotationLayer={false}
            />
          </div>
        ))}
      </Document>
    </div>
  );
}

function PaneMessage({ children }: { children: React.ReactNode }) {
  return <p className="py-16 text-center text-sm text-neutral-500">{children}</p>;
}
