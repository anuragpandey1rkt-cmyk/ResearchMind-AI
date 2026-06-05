"use client";

import { useState } from "react";
import { FileUp, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { uploadPdf } from "@/lib/api";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const result = await uploadPdf(file);
      setMessage(`${result.filename} ingested into ChromaDB with ${result.chunks_count} chunks.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Upload Documents</h1>
        <p className="mt-1 text-muted-foreground">PDFs are parsed, chunked, embedded locally, and stored in ChromaDB.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>PDF Ingestion</CardTitle>
          <CardDescription>Maximum 25 MB by default.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="pdf">PDF file</Label>
            <Input id="pdf" type="file" accept="application/pdf" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
          </div>
          <Button onClick={submit} disabled={!file || loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
            Ingest PDF
          </Button>
          {message ? <div className="rounded-md border border-primary/30 bg-primary/10 p-3 text-sm">{message}</div> : null}
          {error ? <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div> : null}
        </CardContent>
      </Card>
    </div>
  );
}
