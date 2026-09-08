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
  onKeys?: (keys: string[]) => void;
  onActiveKey?: (key: string) => void;
};

export function PdfPane({ fileUrl, onSelect, onKeys, onActiveKey }: Props) {
  const [pageCount, setPageCount] = useState(0);
  const [width, setWidth] = useState(760);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;
    const observer = new ResizeObserver(([entry]) => {
      setWidth(Math.min(entry.contentRect.width - 96, 880));
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!pageCount || !onKeys) return;
    onKeys(Array.from({ length: pageCount }, (_, i) => String(i + 1)));
  }, [pageCount, onKeys]);

  // The rail marks where the reader is, so it has to follow the scroll.
  useEffect(() => {
    if (!pageCount || !onActiveKey) return;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        const key = visible?.target.getAttribute("data-page-number");
        if (key) onActiveKey(key);
      },
      { root: containerRef.current, threshold: [0.1, 0.5, 0.9] },
    );
    containerRef.current
      ?.querySelectorAll("[data-page-number]")
      .forEach((node) => observer.observe(node));
    return () => observer.disconnect();
  }, [pageCount, onActiveKey]);

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
      className="flex-1 overflow-y-auto bg-paper px-12 py-8"
    >
      <Document
        file={fileUrl}
        onLoadSuccess={({ numPages }) => setPageCount(numPages)}
        loading={<PaneMessage>Opening the document…</PaneMessage>}
        error={<PaneMessage>Could not open this PDF.</PaneMessage>}
        className="flex flex-col items-center gap-10"
      >
        {Array.from({ length: pageCount }, (_, index) => (
          <figure key={index} className="flex flex-col items-center gap-2">
            <div
              id={`key-${index + 1}`}
              data-page-number={index + 1}
              className="border border-rule bg-white"
            >
              <Page
                pageNumber={index + 1}
                width={width}
                renderTextLayer
                renderAnnotationLayer={false}
              />
            </div>
            <figcaption className="apparatus tabular">
              page {index + 1}
            </figcaption>
          </figure>
        ))}
      </Document>
    </div>
  );
}

function PaneMessage({ children }: { children: React.ReactNode }) {
  return <p className="py-16 text-center text-fine text-slate">{children}</p>;
}
