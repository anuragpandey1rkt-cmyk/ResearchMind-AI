"use client";

import { useEffect, useState } from "react";
import { Clock3, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchHistory } from "@/lib/api";

type HistoryRow = Awaited<ReturnType<typeof fetchHistory>>[number];

export default function HistoryPage() {
  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHistory()
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load history."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">History</h1>
        <p className="mt-1 text-muted-foreground">Previous research sessions and their completion state.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Research Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading history
            </div>
          ) : error ? (
            <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>
          ) : rows.length === 0 ? (
            <p className="text-sm text-muted-foreground">No research sessions yet.</p>
          ) : (
            <div className="divide-y">
              {rows.map((row) => (
                <div key={row.id} className="flex flex-col gap-2 py-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Clock3 className="h-4 w-4 text-primary" />
                      <h3 className="font-medium">{row.query}</h3>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {new Date(row.created_at).toLocaleString()} - {row.source_count} sources
                    </p>
                  </div>
                  <span className="w-fit rounded-md bg-muted px-2 py-1 text-xs">{row.status}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
