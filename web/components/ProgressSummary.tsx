"use client";

import { useEffect, useState } from "react";
import { getTopicStats, type TopicStat } from "@/lib/api";

export function ProgressSummary() {
  const [stats, setStats] = useState<TopicStat[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await getTopicStats();
        if (!cancelled) setStats(data);
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (failed) {
    return (
      <p className="mt-3 text-sm text-neutral-500">
        Progress is unavailable — the backend is not responding.
      </p>
    );
  }
  if (stats === null) return null;

  if (stats.length === 0) {
    return (
      <p className="mt-3 text-sm text-neutral-500">
        Answer some quiz questions and your weakest topics will show up here.
      </p>
    );
  }

  // Weakest first — the whole point is to show what needs work.
  const ranked = [...stats].sort((a, b) => a.accuracy - b.accuracy);

  return (
    <ul className="mt-4 space-y-2">
      {ranked.map((stat) => (
        <li key={stat.topic} className="flex items-center gap-3">
          <span className="w-56 shrink-0 truncate text-sm text-neutral-700">
            {stat.topic}
          </span>
          <span
            className="h-1.5 flex-1 overflow-hidden rounded-full bg-neutral-200"
            role="img"
            aria-label={`${Math.round(stat.accuracy * 100)} percent correct`}
          >
            <span
              className={`block h-full rounded-full ${barColor(stat.accuracy)}`}
              style={{ width: `${Math.max(stat.accuracy * 100, 2)}%` }}
            />
          </span>
          <span className="w-20 shrink-0 text-right text-xs text-neutral-500">
            {stat.correct}/{stat.attempted}
          </span>
        </li>
      ))}
    </ul>
  );
}

function barColor(accuracy: number) {
  if (accuracy < 0.5) return "bg-red-500";
  if (accuracy < 0.8) return "bg-amber-500";
  return "bg-emerald-500";
}
