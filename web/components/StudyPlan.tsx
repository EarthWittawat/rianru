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
    <div className="mx-auto w-full max-w-3xl px-6 py-10">
      <h1 className="text-xl font-semibold tracking-tight">Coach</h1>
      <p className="mt-1 text-sm text-neutral-600">
        Built from what you actually got wrong, pointed at the pages that cover it.
      </p>

      <button
        onClick={generate}
        disabled={pending}
        className="mt-6 rounded-md bg-neutral-900 px-4 py-2 text-sm text-white transition-colors hover:bg-neutral-700 disabled:opacity-50"
      >
        {pending ? "Working through your results…" : "Plan my study"}
      </button>

      {pending && (
        <p className="mt-3 text-xs text-neutral-500">
          The coach checks your scores, then finds the right pages. Takes up to a
          minute or so.
        </p>
      )}

      {error && (
        <p className="mt-6 rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          {error}
        </p>
      )}

      {plan && plan.tasks.length > 0 && (
        <ol className="mt-8 space-y-3">
          {plan.tasks.map((task) => (
            <TaskRow key={task.id} task={task} onToggle={() => toggle(task)} />
          ))}
        </ol>
      )}

      {!plan && !pending && !error && (
        <p className="mt-8 text-sm text-neutral-500">
          No plan yet. Answer a few quiz questions, then ask for one.
        </p>
      )}
    </div>
  );
}

function TaskRow({ task, onToggle }: { task: StudyTask; onToggle: () => void }) {
  return (
    <li className="rounded-lg border border-neutral-200 bg-white p-4">
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={task.done}
          onChange={onToggle}
          aria-label={`Mark done: ${task.action}`}
          className="mt-0.5 h-4 w-4 shrink-0 accent-neutral-900"
        />
        <div className="min-w-0 flex-1">
          <p
            className={`text-sm ${task.done ? "text-neutral-400 line-through" : "text-neutral-900"}`}
          >
            {task.action}
          </p>
          <p className="mt-1 flex flex-wrap items-center gap-x-2 text-xs text-neutral-500">
            <span>{task.topic}</span>
            {task.est_minutes && <span>· {task.est_minutes} min</span>}
            {task.source && (
              <span>
                · {task.source.document_title}
                {task.source.page ? `, p${task.source.page}` : ""}
              </span>
            )}
          </p>
          {task.why && (
            <p className="mt-2 border-l-2 border-neutral-200 pl-2 text-xs text-neutral-600">
              {task.why}
            </p>
          )}
        </div>
      </div>
    </li>
  );
}
