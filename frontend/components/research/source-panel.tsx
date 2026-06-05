import { ExternalLink } from "lucide-react";
import type { Source } from "@/lib/api";

export function SourcePanel({ sources }: { sources: Source[] }) {
  return (
    <div className="space-y-3">
      {sources.length === 0 ? (
        <p className="text-sm text-muted-foreground">Sources will appear after research completes.</p>
      ) : (
        sources.map((source) => (
          <a
            key={source.url}
            href={source.url}
            target="_blank"
            rel="noreferrer"
            className="block rounded-lg border p-3 transition-colors hover:bg-muted"
          >
            <div className="flex items-start justify-between gap-3">
              <h4 className="text-sm font-medium leading-5">{source.title}</h4>
              <ExternalLink className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            </div>
            <p className="mt-2 line-clamp-3 text-xs text-muted-foreground">{source.snippet}</p>
          </a>
        ))
      )}
    </div>
  );
}
