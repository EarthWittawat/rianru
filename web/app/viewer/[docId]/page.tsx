import Link from "next/link";
import { notFound } from "next/navigation";
import { DocumentReader } from "@/components/DocumentReader";
import { getDocument } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DocumentPage({
  params,
}: {
  params: Promise<{ docId: string }>;
}) {
  const { docId } = await params;

  let document;
  try {
    document = await getDocument(decodeURIComponent(docId));
  } catch {
    notFound();
  }

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex items-baseline justify-between gap-6 border-b border-rule px-6 py-3">
        <div className="min-w-0">
          <h1 className="truncate text-lead tracking-tight">{document.title}</h1>
          <p className="apparatus mt-1">{document.topic}</p>
        </div>
        <Link
          href="/viewer"
          className="apparatus shrink-0 text-slate no-underline hover:text-rubric"
        >
          All material
        </Link>
      </div>
      <DocumentReader document={document} />
    </div>
  );
}
