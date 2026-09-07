"use client";

import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import bash from "react-syntax-highlighter/dist/esm/languages/prism/bash";
import json from "react-syntax-highlighter/dist/esm/languages/prism/json";
import markup from "react-syntax-highlighter/dist/esm/languages/prism/markup";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";

SyntaxHighlighter.registerLanguage("python", python);
SyntaxHighlighter.registerLanguage("bash", bash);
SyntaxHighlighter.registerLanguage("json", json);
SyntaxHighlighter.registerLanguage("markup", markup);

export function CodeBlock({
  code,
  language = "python",
  showLineNumbers = false,
}: {
  code: string;
  language?: string;
  showLineNumbers?: boolean;
}) {
  return (
    <SyntaxHighlighter
      language={language}
      style={oneLight}
      showLineNumbers={showLineNumbers}
      customStyle={{
        margin: 0,
        borderRadius: "0.375rem",
        fontSize: "0.8125rem",
        lineHeight: 1.6,
        background: "#fafafa",
        border: "1px solid #e5e5e5",
        padding: "0.75rem 0.875rem",
      }}
      codeTagProps={{ style: { fontFamily: "var(--font-geist-mono), monospace" } }}
    >
      {code.replace(/\n$/, "")}
    </SyntaxHighlighter>
  );
}
