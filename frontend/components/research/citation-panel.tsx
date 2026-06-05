import type { Citation } from "@/lib/api";

export function CitationPanel({ citations }: { citations: Citation[] }) {
  return (
    <div className="space-y-3">
      {citations.length === 0 ? (
        <p className="text-sm text-muted-foreground">Verified references will appear here.</p>
      ) : (
        citations.map((citation, index) => (
          <div key={`${citation.title}-${index}`} className="rounded-lg border p-3">
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs font-semibold text-primary">[{index + 1}] {citation.source_type.toUpperCase()}</span>
              <span className="text-xs text-muted-foreground">{citation.confidence}%</span>
            </div>
            <h4 className="mt-2 text-sm font-medium">{citation.title}</h4>
            {citation.url ? (
              <a className="mt-1 block truncate text-xs text-primary underline-offset-4 hover:underline" href={citation.url}>
                {citation.url}
              </a>
            ) : null}
            {citation.snippet ? <p className="mt-2 line-clamp-3 text-xs text-muted-foreground">{citation.snippet}</p> : null}
          </div>
        ))
      )}
    </div>
  );
}
