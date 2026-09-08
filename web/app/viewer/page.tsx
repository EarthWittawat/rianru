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
    <div className="mx-auto w-full max-w-4xl px-6 py-14">
      <h1 className="text-display tracking-tight">Course material</h1>
      <p className="mt-2 max-w-[60ch] text-slate">
        Open a document, then drag across any passage to have it explained in
        the margin.
      </p>

      {error && (
        <p className="ruled-block mt-10 border-rubric px-4 py-3 text-fine text-rubric-deep">
          {error}
        </p>
      )}

      {!error && documents.length === 0 && (
        <div className="ruled-block mt-10 px-5 py-4">
          <p className="text-fine text-slate">
            Nothing ingested yet. From the server directory, run
          </p>
          <code className="mt-2 block font-mono text-fine text-ink">
            python scripts/ingest.py --class YOUR_COURSE
          </code>
        </div>
      )}

      <div className="mt-12 space-y-10">
        {Object.entries(byTopic).map(([topic, docs], index) => (
          <section key={topic}>
            <div className="flex items-baseline gap-3 border-b border-rule pb-1.5">
              <span className="apparatus tabular text-ash">
                {String(index + 1).padStart(2, "0")}
              </span>
              <h2 className="apparatus text-ink">{topic}</h2>
            </div>
            <ul>
              {docs.map((doc) => (
                <li key={doc.id} className="border-b border-rule">
                  <Link
                    href={`/viewer/${encodeURIComponent(doc.id)}`}
                    className="group flex items-baseline justify-between gap-6 py-2.5 no-underline"
                  >
                    <span className="group-hover:text-rubric group-hover:underline">
                      {doc.title}
                    </span>
                    <span className="apparatus tabular shrink-0">
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
