"use client";

import { useEffect, useState } from "react";
import {
  generatePlan,
  getLatestPlan,
  setTaskDone,
  type StudyPlan as Plan,
  type StudyTask,
} from "@/lib/api";

export function StudyPlan() {
  const [plan, setPlan] = useState<Plan | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const latest = await getLatestPlan();
        if (!cancelled) setPlan(latest);
      } catch {
        // No plan yet is the normal first-run state, not an error.
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function generate() {
    setPending(true);
    setError("");
    try {
      setPlan(await generatePlan());
    } catch {
      setError(
        "The coach could not build a plan. It needs some answered quiz questions to work from.",
      );
    } finally {
      setPending(false);
    }
  }

  async function toggle(task: StudyTask) {
    const next = !task.done;
    setPlan((current) =>
      current
        ? {
            ...current,
            tasks: current.tasks.map((t) =>
              t.id === task.id ? { ...t, done: next } : t,
            ),
          }
        : current,
    );
    try {
      await setTaskDone(task.id, next);
    } catch {
      // Put it back rather than showing a tick that was never saved.
      setPlan((current) =>
        current
          ? {
              ...current,
              tasks: current.tasks.map((t) =>
                t.id === task.id ? { ...t, done: !next } : t,
              ),
            }
          : current,
      );
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-14">
      <h1 className="text-display tracking-tight">Coach</h1>
      <p className="mt-2 max-w-[58ch] text-slate">
        Built from what you actually got wrong, pointed at the pages that cover
        it.
      </p>

      <div className="mt-8 border-y border-rule py-3">
        <button
          onClick={generate}
          disabled={pending}
          className="detent px-4 py-1.5 text-fine"
        >
          {pending ? "Working through your results…" : "Plan my study"}
        </button>

        {pending && (
          <p className="mt-3 max-w-[58ch] text-fine text-slate">
            The coach reads your scores, then goes looking for the right pages.
            That is several agents in a row, so it usually takes minutes rather
            than seconds. Leave this open — the plan appears here when it lands.
          </p>
        )}
      </div>

      {error && (
        <p className="ruled-block mt-6 border-rubric px-4 py-3 text-fine text-rubric-deep">
          {error}
        </p>
      )}

      {plan && plan.tasks.length > 0 && (
        <ol className="mt-2">
          {plan.tasks.map((task, index) => (
            <TaskRow
              key={task.id}
              task={task}
              index={index}
              onToggle={() => toggle(task)}
            />
          ))}
        </ol>
      )}

      {!plan && !pending && !error && (
        <p className="mt-8 text-fine text-slate">
          No plan yet. Answer a few quiz questions, then ask for one.
        </p>
      )}
    </div>
  );
}

function TaskRow({
  task,
  index,
  onToggle,
}: {
  task: StudyTask;
  index: number;
  onToggle: () => void;
}) {
  return (
    <li className="border-b border-rule py-4">
      <div className="flex items-start gap-4">
        <span className="apparatus tabular w-6 shrink-0 pt-1 text-ash">
          {String(index + 1).padStart(2, "0")}
        </span>
        <input
          type="checkbox"
          checked={task.done}
          onChange={onToggle}
          aria-label={`Mark done: ${task.action}`}
          className="mt-1.5 h-3.5 w-3.5 shrink-0 accent-[#c23a2a]"
        />
        <div className="min-w-0 flex-1">
          <p
            className={
              task.done
                ? "text-fine text-ash line-through decoration-rubric"
                : "text-fine text-ink"
            }
          >
            {task.action}
          </p>
          <p className="apparatus tabular mt-1.5 flex flex-wrap items-baseline gap-x-3">
            <span>{task.topic}</span>
            {task.est_minutes && <span>{task.est_minutes} min</span>}
            {task.source && (
              <span>
                {task.source.document_title}
                {task.source.page ? `, p${task.source.page}` : ""}
              </span>
            )}
          </p>
          {task.why && (
            <p className="bracketed mt-3 max-w-[62ch] text-fine text-slate">
              {task.why}
            </p>
          )}
        </div>
      </div>
    </li>
  );
}
