"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/viewer", label: "Read", note: "Lectures and labs" },
  { href: "/graph", label: "Graph", note: "How it connects" },
  { href: "/chat", label: "Tutor", note: "Ask the material" },
  { href: "/quiz", label: "Quiz", note: "Practise a topic" },
  { href: "/coach", label: "Coach", note: "What to do next" },
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <header className="border-b border-rule bg-paper">
      <nav className="mx-auto no-scrollbar flex max-w-[1600px] items-stretch gap-4 overflow-x-auto px-4 sm:gap-8 sm:px-6">
        <Link
          href="/"
          className="flex shrink-0 items-center gap-2 py-3 text-lead tracking-tight no-underline"
        >
          <span aria-hidden className="text-rubric">
            &#10010;
          </span>
          rianru
        </Link>

        <ul className="flex items-stretch">
          {LINKS.map(({ href, label, note }, index) => {
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <li key={href} className="flex">
                <Link
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className="group flex items-baseline gap-2 border-l border-rule px-3 py-3 whitespace-nowrap no-underline last:border-r sm:px-4"
                >
                  <span
                    aria-hidden
                    className="apparatus tabular text-ash group-hover:text-slate"
                  >
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="flex flex-col">
                    <span
                      className={
                        active
                          ? "text-rubric underline decoration-rubric underline-offset-4"
                          : "text-ink group-hover:underline"
                      }
                    >
                      {label}
                    </span>
                    <span
                      aria-hidden
                      className="apparatus mt-0.5 hidden text-ash lg:block"
                    >
                      {note}
                    </span>
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </header>
  );
}
