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
      <p className="mt-3 text-fine text-rubric-deep">
        Progress is unavailable — the backend is not responding.
      </p>
    );
  }
  if (stats === null) {
    return <p className="apparatus mt-3">Reading your record…</p>;
  }

  if (stats.length === 0) {
    return (
      <p className="mt-3 text-fine text-slate">
        Answer some quiz questions and your weakest topics will show up here.
      </p>
    );
  }

  // Weakest first — the whole point is to show what needs work.
  const ranked = [...stats].sort((a, b) => a.accuracy - b.accuracy);

  return (
    <ul className="mt-4">
      {ranked.map((stat) => {
        const weak = stat.accuracy < 0.5;
        return (
          <li
            key={stat.topic}
            className="flex items-center gap-4 border-b border-rule py-2"
          >
            <span
              className={`w-64 shrink-0 truncate text-fine ${
                weak ? "text-ink" : "text-slate"
              }`}
            >
              {stat.topic}
            </span>
            <span
              className="h-2 flex-1 border-b border-rule-strong"
              role="img"
              aria-label={`${Math.round(stat.accuracy * 100)} percent correct`}
            >
              <span
                className={`block h-2 ${weak ? "bg-rubric" : "bg-slate"}`}
                style={{ width: `${Math.max(stat.accuracy * 100, 2)}%` }}
              />
            </span>
            <span className="apparatus tabular w-16 shrink-0 text-right">
              {stat.correct}/{stat.attempted}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
