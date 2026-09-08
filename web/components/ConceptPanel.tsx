"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { getConcept, type ConceptDetail } from "@/lib/api";
import { Markdown } from "@/components/Markdown";

type Status = "idle" | "loading" | "ready" | "error";

/**
 * The margin of the path. A concept is not a dot: it is a thing you can be
 * told what it is, shown an example of, and pointed at the pages that teach it.
 */
export function ConceptPanel({
  name,
  onSelect,
}: {
  name: string | null;
  onSelect: (name: string) => void;
}) {
  const [concept, setConcept] = useState<ConceptDetail | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  const asideRef = useRef<HTMLElement | null>(null);
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  // When the concept changes, bring the new content into view: reset the
  // inner scroller and, below lg, scroll the whole panel up to the reader.
  useEffect(() => {
    if (!name) return;
    if (scrollerRef.current) scrollerRef.current.scrollTop = 0;

    // On a wide screen the panel is sticky and already in view, so scrolling
    // the window would only throw the reader's place away. Stacked under the
    // content, it genuinely is off-screen and has to come up.
    const stacked = !window.matchMedia("(min-width: 1024px)").matches;
    if (stacked) {
      asideRef.current?.scrollIntoView?.({ behavior: "smooth", block: "nearest" });
    }
  }, [name]);

  useEffect(() => {
    if (!name) return;

    let cancelled = false;
    (async () => {
      try {
        const data = await getConcept(name);
        if (!cancelled) setConcept(data);
      } catch {
        if (!cancelled) setFailed(name);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [name]);

  // Derived rather than stored: state that only restates the props is state
  // that can disagree with them.
  const status: Status = !name
    ? "idle"
    : failed === name
      ? "error"
      : concept?.name === name
        ? "ready"
        : "loading";

  return (
    <aside
      ref={asideRef}
      className="flex max-h-[45vh] w-full shrink-0 flex-col border-t border-rule bg-paper-lift lg:sticky lg:top-0 lg:h-screen lg:max-h-none lg:w-[24rem] lg:border-t-0 lg:border-l xl:w-[28rem]"
    >
      <div className="border-b border-rule px-6 py-4">
        <h2 className="apparatus">Concept</h2>
      </div>

      <div ref={scrollerRef} className="flex-1 overflow-y-auto px-6 py-5">
        {!name && (
          <p className="text-fine text-slate">
            Pick anything on the path to see what it is, an example of it, and
            what it stands on.
          </p>
        )}

        {status === "loading" && (
          <>
            <p className="text-lead">{name}</p>
            <p className="apparatus mt-3 animate-pulse">
              Reading the pages that teach it…
            </p>
          </>
        )}

        {status === "error" && (
          <p className="ruled-block border-rubric px-3 py-2 text-fine text-rubric-deep">
            Could not explain {name}. The tutor may be unreachable, or the
            material may not cover it in enough depth.
          </p>
        )}

        {status === "ready" && concept && (
          <>
            <p className="text-lead">{concept.name}</p>
            <p className="apparatus mt-1">{concept.type}</p>

            {concept.summary && (
              <div className="mt-5 text-fine leading-relaxed">
                <Markdown>{concept.summary}</Markdown>
              </div>
            )}

            {concept.example && (
              <section className="mt-6 border-t border-rule pt-4">
                <h3 className="apparatus">Example</h3>
                <div className="mt-2 text-fine leading-relaxed">
                  <Markdown>{concept.example}</Markdown>
                </div>
              </section>
            )}

            {concept.requires.length > 0 && (
              <section className="mt-6 border-t border-rule pt-4">
                <h3 className="apparatus">Learn first</h3>
                <ul className="mt-3 space-y-3">
                  {concept.requires.map((requirement) => (
                    <li key={requirement.name}>
                      <button
                        onClick={() => onSelect(requirement.name)}
                        className="text-fine text-ink underline decoration-rule hover:text-rubric"
                      >
                        {requirement.name}
                      </button>
                      <p className="bracketed mt-1 text-fine text-slate">
                        {requirement.reason}
                      </p>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {concept.sources.length > 0 && (
              <section className="mt-6 border-t border-rule pt-4">
                <h3 className="apparatus">Covered in</h3>
                <ul className="mt-2">
                  {groupByDocument(concept.sources).map((source) => (
                    <li
                      key={source.document_id}
                      className="border-b border-rule py-2 last:border-b-0"
                    >
                      <Link
                        href={`/viewer/${encodeURIComponent(source.document_id)}${
                          source.pages[0] ? `#key-${source.pages[0]}` : ""
                        }`}
                        className="block text-fine text-ink no-underline hover:text-rubric hover:underline"
                      >
                        {source.document_title}
                      </Link>
                      {source.pages.length > 0 && (
                        <p className="apparatus tabular mt-0.5">
                          {source.pages.length === 1 ? "page" : "pages"}{" "}
                          {source.pages.join(", ")}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </>
        )}
      </div>
    </aside>
  );
}

/** One row per document, its pages gathered — the same lecture four times is a list, not four sources. */
function groupByDocument(sources: ConceptDetail["sources"]) {
  const grouped = new Map<
    string,
    { document_id: string; document_title: string; pages: number[] }
  >();

  for (const source of sources) {
    const existing = grouped.get(source.document_id) ?? {
      document_id: source.document_id,
      document_title: source.document_title,
      pages: [],
    };
    if (source.page && !existing.pages.includes(source.page)) {
      existing.pages.push(source.page);
    }
    grouped.set(source.document_id, existing);
  }

  for (const entry of grouped.values()) entry.pages.sort((a, b) => a - b);
  return [...grouped.values()];
}
