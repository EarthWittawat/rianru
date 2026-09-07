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
      <div className="flex items-baseline justify-between gap-4 border-b border-neutral-200 bg-white px-6 py-3">
        <div className="min-w-0">
          <h1 className="truncate text-sm font-medium">{document.title}</h1>
          <p className="text-xs text-neutral-500">{document.topic}</p>
        </div>
        <Link
          href="/viewer"
          className="shrink-0 text-xs text-neutral-600 hover:text-neutral-900"
        >
          All material
        </Link>
      </div>
      <DocumentReader document={document} />
    </div>
  );
}
