import Link from "next/link";
import { ProgressSummary } from "@/components/ProgressSummary";

const SECTIONS = [
  {
    href: "/viewer",
    label: "Read",
    description: "Open a lecture or lab. Any passage you drag over gets explained in the margin.",
  },
  {
    href: "/graph",
    label: "Graph",
    description: "Every concept the material mentions, and the highlights you kept, as one map.",
  },
  {
    href: "/chat",
    label: "Tutor",
    description: "Ask a question. The answer comes from your documents and says which page.",
  },
  {
    href: "/quiz",
    label: "Quiz",
    description: "Practise a topic. Every answer is recorded, which is what the coach reads.",
  },
  {
    href: "/coach",
    label: "Coach",
    description: "A plan built from what you actually got wrong, pointed at the pages that fix it.",
  },
];

export default function Home() {
  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-16">
      <h1 className="text-display tracking-tight">
        Your course material, read properly.
      </h1>
      <p className="mt-3 max-w-[58ch] text-lead text-slate">
        Lectures, labs and notebooks in one place — annotated, questioned, and
        turned into a plan.
      </p>

      <section className="mt-14">
        <h2 className="apparatus border-b border-rule pb-1.5">Where you stand</h2>
        <ProgressSummary />
      </section>

      <section className="mt-14">
        <h2 className="apparatus border-b border-rule pb-1.5">Contents</h2>
        <ul>
          {SECTIONS.map(({ href, label, description }, index) => (
            <li key={href} className="border-b border-rule">
              <Link
                href={href}
                className="group flex items-baseline gap-5 py-4 no-underline"
              >
                <span className="apparatus tabular w-6 shrink-0 text-ash">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="w-24 shrink-0 group-hover:text-rubric group-hover:underline">
                  {label}
                </span>
                <span className="text-fine text-slate">{description}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
