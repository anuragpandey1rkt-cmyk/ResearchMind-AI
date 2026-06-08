"use client";

import { useState } from "react";
import { Download, FileText, Loader2, Network, Sparkles, Upload, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { MarkdownReport } from "@/components/research/markdown-report";
import { KnowledgeGraphView } from "@/components/research/knowledge-graph";
import { analyzeGaps, gapReportPdfUrl, uploadGapPapers, type GapDetectionResponse } from "@/lib/api";

const scoreLabels: Record<string, string> = {
  novelty_score: "Novelty",
  research_saturation_score: "Saturation",
  impact_score: "Impact",
  focus_score: "Focus",
  commercialization_potential_score: "Commercial"
};

export function GapDetectorWorkspace() {
  const [files, setFiles] = useState<File[]>([]);
  const [domain, setDomain] = useState("Agentic AI research systems");
  const [documentIds, setDocumentIds] = useState<string[]>([]);
  const [uploadedDocs, setUploadedDocs] = useState<Array<{ document_id: string; filename: string; chunks_count: number }>>([]);
  const [result, setResult] = useState<GapDetectionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  async function upload() {
    if (files.length === 0) return;
    setLoading(true);
    setError(null);
    setStatus("Uploading and indexing papers...");
    try {
      const response = await uploadGapPapers(files);
      const newDocs = response.documents.map((doc) => ({
        document_id: doc.document_id,
        filename: doc.filename,
        chunks_count: doc.chunks_count,
      }));

      setUploadedDocs((prev) => {
        const existingIds = new Set(prev.map(d => d.document_id));
        const filteredNew = newDocs.filter(d => !existingIds.has(d.document_id));
        const updated = [...prev, ...filteredNew];
        setDocumentIds(updated.map((doc) => doc.document_id));
        return updated;
      });

      setFiles([]);
      const fileInput = document.getElementById("papers") as HTMLInputElement;
      if (fileInput) fileInput.value = "";

      setStatus(`Successfully uploaded and indexed ${newDocs.length} paper(s).`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  async function analyze() {
    if (documentIds.length < 2) {
      setError("Please upload at least two papers for gap analysis.");
      return;
    }
    setLoading(true);
    setError(null);
    setStatus("Running paper analysis, synthesis, contradiction, gap, and innovation agents...");
    try {
      const response = await analyzeGaps(documentIds, domain);
      setResult(response);
      setStatus("Research gap report generated successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gap analysis failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Research Gap Detector</h1>
          <p className="mt-2 max-w-3xl text-muted-foreground">
            Upload multiple papers, synthesize their claims, surface contradictions, and convert gaps into research and product opportunities.
          </p>
        </div>
        {result ? (
          <Button asChild variant="secondary">
            <a href={gapReportPdfUrl(result.analysis_id)}>
              <Download className="h-4 w-4" />
              Export PDF
            </a>
          </Button>
        ) : null}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Paper Collection</CardTitle>
          <CardDescription>Use at least two PDF papers for cross-paper comparison.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-[1fr_220px_220px]">
            <div className="space-y-2">
              <Label htmlFor="domain">Research domain</Label>
              <Input id="domain" value={domain} onChange={(event) => setDomain(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="papers">PDF papers</Label>
              <Input
                id="papers"
                type="file"
                accept="application/pdf"
                multiple
                onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
              />
            </div>
            <div className="flex items-end gap-2">
              <Button onClick={upload} disabled={loading || files.length === 0} className="flex-1">
                {loading && files.length > 0 ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                Upload
              </Button>
              <Button onClick={analyze} disabled={loading || documentIds.length < 2} className="flex-1" variant="secondary">
                {loading && documentIds.length > 0 ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                Analyze
              </Button>
            </div>
          </div>

          {uploadedDocs.length > 0 ? (
            <div className="border-t pt-4">
              <Label className="text-sm font-semibold">Active Paper Collection ({uploadedDocs.length})</Label>
              <div className="mt-2 grid gap-2">
                {uploadedDocs.map((doc) => (
                  <div key={doc.document_id} className="flex items-center justify-between rounded-lg border bg-card p-3 shadow-sm">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-primary shrink-0" />
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-foreground line-clamp-1 max-w-[250px] sm:max-w-[400px] md:max-w-[600px]">
                          {doc.filename}
                        </span>
                        <span className="text-xs text-muted-foreground">{doc.chunks_count} text chunks indexed</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        setUploadedDocs((prev) => {
                          const updated = prev.filter((d) => d.document_id !== doc.document_id);
                          setDocumentIds(updated.map((d) => d.document_id));
                          return updated;
                        });
                      }}
                      className="h-8 w-8 text-destructive hover:bg-destructive/10 hover:text-destructive shrink-0"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {status ? <div className="rounded-lg border bg-muted p-3 text-sm">{status}</div> : null}
      {error ? <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div> : null}

      {result ? (
        <>
          <div className="grid gap-4 md:grid-cols-5">
            {Object.entries(result.scores).map(([key, value]) => (
              <Card key={key}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">{scoreLabels[key] ?? key}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-semibold">{value}</div>
                  <div className="mt-3 h-2 rounded-full bg-muted">
                    <div className="h-2 rounded-full bg-primary" style={{ width: `${value}%` }} />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
            <section className="space-y-5">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Network className="h-5 w-5 text-primary" />
                    Knowledge Graph
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <KnowledgeGraphView graph={result.knowledge_graph} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Research Gap Report</CardTitle>
                </CardHeader>
                <CardContent>
                  <MarkdownReport markdown={result.report_markdown} />
                </CardContent>
              </Card>
            </section>

            <aside className="space-y-5">
              <Card>
                <CardHeader>
                  <CardTitle>Theme Clusters</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {result.theme_clusters.map((cluster) => (
                    <div key={cluster.name} className="rounded-lg border p-3">
                      <div className="flex items-center justify-between gap-3">
                        <h3 className="text-sm font-medium">{cluster.name}</h3>
                        <span className="text-xs text-muted-foreground">{cluster.saturation_score}%</span>
                      </div>
                      <p className="mt-2 text-xs text-muted-foreground">{cluster.papers.length} papers - {cluster.concepts.join(", ")}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Gap Heatmap</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {result.visualizations.gap_heatmap.map((item) => (
                    <div key={item.category}>
                      <div className="flex justify-between text-sm">
                        <span>{item.category}</span>
                        <span>{item.count}</span>
                      </div>
                      <div className="mt-1 h-2 rounded-full bg-muted">
                        <div className="h-2 rounded-full bg-accent" style={{ width: `${Math.min(100, item.count * 18)}%` }} />
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Opportunity Matrix</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {result.visualizations.opportunity_matrix.slice(0, 8).map((item) => (
                    <div key={item.title} className="rounded-lg border p-3">
                      <h3 className="text-sm font-medium">{item.title}</h3>
                      <p className="mt-2 text-xs text-muted-foreground">
                        Impact {item.impact} - Feasibility {item.feasibility} - Commercial {item.commercialization}
                      </p>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Papers Reviewed</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {result.papers.map((paper) => (
                    <div key={paper.document_id} className="rounded-lg border p-3">
                      <FileText className="mb-2 h-4 w-4 text-primary" />
                      <h3 className="text-sm font-medium">{paper.title}</h3>
                      <p className="mt-1 line-clamp-3 text-xs text-muted-foreground">{paper.abstract}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </aside>
          </div>
        </>
      ) : null}
    </div>
  );
}
