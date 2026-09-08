"use client";

import { useEffect, useState } from "react";
import {
  getLearningPath,
  type LearningPath as Path,
  type PathConcept,
  type PathEdge,
} from "@/lib/api";
import { ConceptPanel } from "@/components/ConceptPanel";
import { useCourse } from "@/lib/course";

/**
 * The course as a path rather than a cloud: stages in the order they are
 * taught, and inside each stage the concepts you can start on before the ones
 * built on top of them.
 */
export function LearningPath() {
  const [path, setPath] = useState<Path | null>(null);
  const [failed, setFailed] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const { course } = useCourse();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await getLearningPath(course);
        if (!cancelled) setPath(data);
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [course]);

  const prerequisitesOf = (name: string) =>
    (path?.edges ?? []).filter((edge) => edge.source === name);

  return (
    <div className="flex flex-1 flex-col overflow-hidden lg:flex-row">
      <div className="flex-1 overflow-y-auto px-6 py-12">
        <div className="mx-auto max-w-3xl">
          <h1 className="text-display tracking-tight">The path</h1>
          <p className="mt-2 max-w-[58ch] text-slate">
            Your course in the order it teaches. Inside each stage, what you can
            start on comes before what is built on top of it.
          </p>

          {!path && !failed && (
            <p className="apparatus mt-10 animate-pulse">Laying out the course…</p>
          )}

          {failed && (
            <p className="ruled-block mt-10 border-rubric px-4 py-3 text-fine text-rubric-deep">
              Could not load the path. Is the backend running?
            </p>
          )}

          {path && path.stages.length === 0 && !failed && (
            <div className="ruled-block mt-10 px-5 py-4">
              <p className="text-fine text-slate">
                No path yet. From the server directory, run
              </p>
              <code className="mt-2 block font-mono text-fine text-ink">
                python scripts/set_positions.py --class YOUR_COURSE
              </code>
              <code className="mt-1 block font-mono text-fine text-ink">
                python scripts/build_path.py --class YOUR_COURSE --refine
              </code>
            </div>
          )}

          {path?.stages.map((stage, index) => (
            <section key={stage.topic} className="mt-12">
              <div className="flex items-baseline gap-3 border-b border-rule pb-1.5">
                <span className="apparatus tabular text-ash">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h2 className="apparatus text-ink">{stage.topic}</h2>
                <span className="apparatus tabular ml-auto">
                  {stage.concepts.length} concepts
                </span>
              </div>

              <ul className="mt-3">
                {stage.concepts.map((concept) => (
                  <ConceptRow
                    key={concept.name}
                    concept={concept}
                    prerequisites={prerequisitesOf(concept.name)}
                    selected={selected === concept.name}
                    onSelect={() => setSelected(concept.name)}
                  />
                ))}
              </ul>
            </section>
          ))}
        </div>
      </div>

      <ConceptPanel name={selected} onSelect={setSelected} />
    </div>
  );
}

function ConceptRow({
  concept,
  prerequisites,
  selected,
  onSelect,
}: {
  concept: PathConcept;
  prerequisites: PathEdge[];
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <li className="border-b border-rule">
      <button
        onClick={onSelect}
        aria-current={selected ? "true" : undefined}
        className="group flex w-full items-baseline gap-4 py-2.5 text-left"
      >
        {/* Depth as an indent: one step right for each layer of prerequisites. */}
        <span
          aria-hidden
          className="shrink-0"
          style={{ width: `${concept.depth * 1.25}rem` }}
        />
        <span
          className={
            selected
              ? "text-rubric underline decoration-rubric underline-offset-4"
              : "group-hover:text-rubric group-hover:underline"
          }
        >
          {concept.name}
        </span>
        <span className="apparatus tabular ml-auto shrink-0 text-right">
          {prerequisites.length > 0 && (
            <span className="mr-3">needs {prerequisites.length}</span>
          )}
          {concept.mentions}×
        </span>
      </button>
    </li>
  );
}
