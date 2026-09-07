import Link from "next/link";
import { ProgressSummary } from "@/components/ProgressSummary";

const SECTIONS = [
  {
    href: "/viewer",
    label: "Read",
    description: "Open lecture PDFs and labs. Select any passage to get it explained.",
  },
  {
    href: "/graph",
    label: "Graph",
    description: "See how concepts across the course connect, including your own highlights.",
  },
  {
    href: "/chat",
    label: "Tutor",
    description: "Ask questions answered from the course material, not the open internet.",
  },
  {
    href: "/quiz",
    label: "Quiz",
    description: "Generate practice questions from any topic you have covered.",
  },
];

export default function Home() {
  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-16">
      <h1 className="text-2xl font-semibold tracking-tight">CPE393 — Text Analytics</h1>
      <p className="mt-2 text-neutral-600">
        Your course material, made interactive.
      </p>

      <section className="mt-10">
        <h2 className="text-xs font-medium uppercase tracking-wide text-neutral-500">
          Where you stand
        </h2>
        <ProgressSummary />
      </section>

      <ul className="mt-10 grid gap-3 sm:grid-cols-2">
        {SECTIONS.map(({ href, label, description }) => (
          <li key={href}>
            <Link
              href={href}
              className="block h-full rounded-lg border border-neutral-200 bg-white p-5 transition-colors hover:border-neutral-400"
            >
              <span className="text-sm font-medium">{label}</span>
              <span className="mt-1 block text-sm text-neutral-600">{description}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
