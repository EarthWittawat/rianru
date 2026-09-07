"use client";

import ReactMarkdown from "react-markdown";

/** The tutor answers in markdown, so it needs rendering rather than printing. */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="space-y-3 text-sm leading-relaxed text-neutral-800">
      <ReactMarkdown
        components={{
          p: ({ children }) => <p>{children}</p>,
          ul: ({ children }) => (
            <ul className="list-disc space-y-1 pl-5">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal space-y-1 pl-5">{children}</ol>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-neutral-900">{children}</strong>
          ),
          code: ({ children }) => (
            <code className="rounded bg-neutral-100 px-1 py-0.5 font-mono text-[0.85em]">
              {children}
            </code>
          ),
          pre: ({ children }) => (
            <pre className="overflow-x-auto rounded-md bg-neutral-900 p-3 text-xs text-neutral-100">
              {children}
            </pre>
          ),
          h1: ({ children }) => (
            <h3 className="font-semibold text-neutral-900">{children}</h3>
          ),
          h2: ({ children }) => (
            <h3 className="font-semibold text-neutral-900">{children}</h3>
          ),
          h3: ({ children }) => (
            <h3 className="font-semibold text-neutral-900">{children}</h3>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
