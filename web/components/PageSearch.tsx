"use client";

import Link from "next/link";
import { useState } from "react";
import { searchPages, type PageHit } from "@/lib/api";
import { useCourse } from "@/lib/course";

type Status = "idle" | "searching" | "ready" | "unindexed" | "error";

/**
 * Search the material by what a page looks like. A slide whose meaning is a
 * chart carries almost no extractable text, so the words-only search that runs
 * everywhere else in the app cannot find it at all.
 */
export function PageSearch() {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<PageHit[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const { course } = useCourse();

  async function run(event: React.FormEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (trimmed.length < 2) return;

    setStatus("searching");
    try {
      const result = await searchPages(trimmed, course);
      setHits(result.hits);
      setStatus(result.indexed ? "ready" : "unindexed");
    } catch {
      setStatus("error");
    }
  }

  return (
    <section className="mt-10 border-y border-rule py-4">
      <form onSubmit={run} className="flex flex-wrap items-center gap-3">
        <label htmlFor="page-search" className="apparatus">
          Find a page
        </label>
        <input
          id="page-search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="a chart of word frequencies, a confusion matrix…"
          className="min-w-0 flex-1 border border-rule bg-paper px-3 py-1.5 text-fine outline-none placeholder:text-ash focus:border-rubric"
        />
        <button
          type="submit"
          disabled={status === "searching" || query.trim().length < 2}
          className="detent px-4 py-1.5 text-fine"
        >
          {status === "searching" ? "Looking…" : "Search pages"}
        </button>
      </form>

      {status === "searching" && (
        <p className="apparatus mt-3">
          Reading the pages. The first search of a session loads the vision
          model, which takes about half a minute; the rest are instant.
        </p>
      )}

      {status === "unindexed" && (
        <p className="mt-3 text-fine text-slate">
          This class has no page index yet. From the server directory, run{" "}
          <code className="font-mono">
            python scripts/build_colpali.py --class {course ?? "YOUR_COURSE"}
          </code>
          .
        </p>
      )}

      {status === "error" && (
        <p className="mt-3 text-fine text-rubric-deep">
          Page search is unavailable. Is the backend running?
        </p>
      )}

      {status === "ready" && hits.length === 0 && (
        <p className="mt-3 text-fine text-slate">
          Nothing in this class looks like that.
        </p>
      )}

      {status === "ready" && hits.length > 0 && (
        <ul className="mt-3">
          {groupHits(hits).map((group) => (
            <li key={group.document_id} className="border-b border-rule py-2">
              <Link
                href={`/viewer/${encodeURIComponent(group.document_id)}#key-${group.pages[0]}`}
                className="group flex items-baseline justify-between gap-4 no-underline"
              >
                <span className="text-fine group-hover:text-rubric group-hover:underline">
                  {group.document_title}
                </span>
                <span className="apparatus tabular shrink-0">page {group.pages[0]}</span>
              </Link>
              {group.pages.length > 1 && (
                <p className="apparatus tabular mt-1">
                  also{" "}
                  {group.pages.slice(1).map((page, index) => (
                    <span key={page}>
                      {index > 0 && ", "}
                      <Link
                        href={`/viewer/${encodeURIComponent(group.document_id)}#key-${page}`}
                        className="text-ink no-underline hover:text-rubric hover:underline"
                      >
                        {page}
                      </Link>
                    </span>
                  ))}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/**
 * One row per document, its matching pages behind it. A lecture whose every
 * chart matches would otherwise fill the list with its own title.
 * Rank order is kept: documents appear in the order their best page scored.
 */
function groupHits(hits: PageHit[]) {
  const grouped: { document_id: string; document_title: string; pages: number[] }[] = [];

  for (const hit of hits) {
    const existing = grouped.find((group) => group.document_id === hit.document_id);
    if (existing) {
      existing.pages.push(hit.page);
    } else {
      grouped.push({
        document_id: hit.document_id,
        document_title: hit.document_title,
        pages: [hit.page],
      });
    }
  }

  return grouped;
}
