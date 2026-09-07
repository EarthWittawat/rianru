import Link from "next/link";
import { listDocuments, type DocumentSummary } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ViewerIndexPage() {
  let documents: DocumentSummary[] = [];
  let error: string | null = null;

  try {
    documents = await listDocuments();
  } catch {
    error = "Could not reach the API. Is the backend running on port 8000?";
  }

  const byTopic = documents.reduce<Record<string, DocumentSummary[]>>((acc, doc) => {
    (acc[doc.topic] ??= []).push(doc);
    return acc;
  }, {});

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-12">
      <h1 className="text-xl font-semibold tracking-tight">Course material</h1>
      <p className="mt-1 text-sm text-neutral-600">
        Open a document, then select any passage to have it explained.
      </p>

      {error && (
        <p className="mt-8 rounded-md border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          {error}
        </p>
      )}

      {!error && documents.length === 0 && (
        <p className="mt-8 rounded-md border border-neutral-200 bg-white p-4 text-sm text-neutral-600">
          Nothing ingested yet. Run{" "}
          <code className="font-mono text-xs">python scripts/ingest.py --class CPE393</code>{" "}
          from the server directory.
        </p>
      )}

      <div className="mt-8 space-y-8">
        {Object.entries(byTopic).map(([topic, docs]) => (
          <section key={topic}>
            <h2 className="text-xs font-medium uppercase tracking-wide text-neutral-500">
              {topic}
            </h2>
            <ul className="mt-2 divide-y divide-neutral-200 overflow-hidden rounded-lg border border-neutral-200 bg-white">
              {docs.map((doc) => (
                <li key={doc.id}>
                  <Link
                    href={`/viewer/${encodeURIComponent(doc.id)}`}
                    className="flex items-baseline justify-between gap-4 px-4 py-3 transition-colors hover:bg-neutral-50"
                  >
                    <span className="text-sm">{doc.title}</span>
                    <span className="shrink-0 text-xs text-neutral-500">
                      {doc.file_type} · {doc.chunk_count} chunks
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
