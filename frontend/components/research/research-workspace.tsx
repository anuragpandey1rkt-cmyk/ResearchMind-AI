"use client";

import { useMemo, useState } from "react";
import { Download, Loader2, Send, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { CitationPanel } from "@/components/research/citation-panel";
import { MarkdownReport } from "@/components/research/markdown-report";
import { SourcePanel } from "@/components/research/source-panel";
import { reportPdfUrl, runResearch, type ResearchResponse } from "@/lib/api";

const starter = "How are agentic AI systems changing enterprise research workflows, and what are the risks?";

export function ResearchWorkspace() {
  const [query, setQuery] = useState(starter);
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setLoading(true);
    setError(null);
    try {
      const data = await runResearch(query, result?.session_id);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Research failed.");
    } finally {
      setLoading(false);
    }
  }

  const citations = useMemo(() => result?.report?.citations ?? [], [result]);

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="space-y-5">
        <div>
          <h1 className="text-3xl font-semibold tracking-normal">ResearchMind</h1>
          <p className="mt-2 max-w-3xl text-muted-foreground">
            Plan, search, retrieve, cite, and produce structured research reports from public sources and uploaded PDFs.
          </p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Research Question</CardTitle>
            <CardDescription>Ask a question that benefits from structured evidence and citations.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea value={query} onChange={(event) => setQuery(event.target.value)} />
            <div className="flex flex-wrap items-center gap-3">
              <Button onClick={submit} disabled={loading || query.trim().length < 8}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Run Research
              </Button>
              <Button asChild variant="outline">
                <a href="/upload">
                  <Upload className="h-4 w-4" />
                  Upload PDFs
                </a>
              </Button>
              {result?.report?.id ? (
                <Button asChild variant="secondary">
                  <a href={reportPdfUrl(result.report.id)}>
                    <Download className="h-4 w-4" />
                    Export PDF
                  </a>
                </Button>
              ) : null}
            </div>
            {error ? <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div> : null}
          </CardContent>
        </Card>

        {loading ? (
          <Card>
            <CardContent className="flex items-center gap-3 p-5 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Research agents are planning, searching, retrieving, and drafting.
            </CardContent>
          </Card>
        ) : null}

        {result?.plan ? (
          <Card>
            <CardHeader>
              <CardTitle>Research Plan</CardTitle>
              <CardDescription>{result.plan.objective}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              {result.plan.tasks.map((task) => (
                <div key={task.title} className="rounded-lg border p-3">
                  <h3 className="text-sm font-medium">{task.title}</h3>
                  <p className="mt-1 text-xs text-muted-foreground">{task.objective}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        ) : null}

        {result?.report?.markdown ? (
          <Card>
            <CardHeader>
              <CardTitle>{result.report.title}</CardTitle>
              <CardDescription>Structured report with citation grounding.</CardDescription>
            </CardHeader>
            <CardContent>
              <MarkdownReport markdown={result.report.markdown} />
            </CardContent>
          </Card>
        ) : null}
      </section>

      <aside className="space-y-5">
        <Card>
          <CardHeader>
            <CardTitle>Timeline</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {["Plan", "Search", "Retrieve", "Cite", "Write"].map((step, index) => (
              <div key={step} className="flex items-center gap-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                  {index + 1}
                </span>
                <span>{step}</span>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <SourcePanel sources={result?.sources ?? []} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Citations</CardTitle>
          </CardHeader>
          <CardContent>
            <CitationPanel citations={citations} />
          </CardContent>
        </Card>
      </aside>
    </div>
  );
}
