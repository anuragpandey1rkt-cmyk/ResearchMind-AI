export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export type Citation = {
  id?: string;
  title: string;
  url?: string | null;
  authors?: string | null;
  source_type: string;
  snippet?: string | null;
  confidence: number;
};

export type Source = {
  title: string;
  url: string;
  snippet: string;
  rank: number;
};

export type ResearchResponse = {
  session_id: string;
  status: string;
  plan?: {
    objective: string;
    subtopics: string[];
    tasks: Array<{ title: string; objective: string; search_queries: string[] }>;
  };
  sources: Source[];
  context: Array<{ text: string; metadata: Record<string, string>; rerank_score: number }>;
  report?: {
    id?: string;
    session_id: string;
    title: string;
    markdown: string;
    citations: Citation[];
    created_at?: string;
  };
};

export type GapPaper = {
  document_id: string;
  filename: string;
  title: string;
  authors: string[];
  abstract: string;
  methodology: string;
  results: string;
  limitations: string[];
  future_work: string[];
  key_findings: string[];
  methods: string[];
  datasets: string[];
  metrics: string[];
  research_areas: string[];
};

export type KnowledgeGraph = {
  nodes: Array<{ id: string; label: string; type: string; score: number }>;
  edges: Array<{ id: string; source: string; target: string; label: string; weight: number }>;
};

export type ThemeCluster = {
  name: string;
  papers: string[];
  concepts: string[];
  saturation_score: number;
};

export type GapDetectionResponse = {
  analysis_id: string;
  status: string;
  research_domain: string;
  papers: GapPaper[];
  theme_clusters: ThemeCluster[];
  contradictions: Array<{ claim_a: string; claim_b: string; papers: string[]; severity: number; explanation: string }>;
  gaps: Array<{ category: string; description: string; evidence: string[]; novelty_score: number; impact_score: number; feasibility_score: number }>;
  innovations: Array<{
    title: string;
    type: string;
    rationale: string;
    novelty_score: number;
    feasibility_score: number;
    impact_score: number;
    commercialization_potential_score: number;
  }>;
  scores: {
    novelty_score: number;
    research_saturation_score: number;
    impact_score: number;
    feasibility_score: number;
    commercialization_potential_score: number;
  };
  knowledge_graph: KnowledgeGraph;
  visualizations: {
    theme_clusters: ThemeCluster[];
    research_trends: Array<{ name: string; papers: number }>;
    gap_heatmap: Array<{ category: string; count: number }>;
    opportunity_matrix: Array<{ title: string; impact: number; feasibility: number; commercialization: number }>;
    innovation_scores: Record<string, number>;
  };
  report_markdown: string;
  created_at?: string;
};

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function runResearch(query: string, sessionId?: string) {
  const response = await fetch(`${API_BASE_URL}/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, session_id: sessionId, top_k: 8 })
  });
  return parseResponse<ResearchResponse>(response);
}

export async function uploadPdf(file: File, sessionId?: string) {
  const form = new FormData();
  form.append("file", file);
  const suffix = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
  const response = await fetch(`${API_BASE_URL}/upload${suffix}`, { method: "POST", body: form });
  return parseResponse<{ document_id: string; filename: string; chunks_count: number; extracted_chars: number }>(response);
}

export async function fetchHistory() {
  const response = await fetch(`${API_BASE_URL}/history`, { cache: "no-store" });
  return parseResponse<Array<{ id: string; query: string; status: string; created_at: string; source_count: number }>>(response);
}

export function reportPdfUrl(reportId: string) {
  return `${API_BASE_URL}/report/${reportId}/pdf`;
}

export async function uploadGapPapers(files: File[]) {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  const response = await fetch(`${API_BASE_URL}/gap-detector/upload`, { method: "POST", body: form });
  return parseResponse<{ documents: Array<{ document_id: string; filename: string; chunks_count: number; extracted_chars: number }> }>(response);
}

export async function analyzeGaps(documentIds: string[], researchDomain: string) {
  const response = await fetch(`${API_BASE_URL}/gap-detector/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_ids: documentIds, research_domain: researchDomain, top_k: 12 })
  });
  return parseResponse<GapDetectionResponse>(response);
}

export function gapReportPdfUrl(analysisId: string) {
  return `${API_BASE_URL}/gap-detector/${analysisId}/pdf`;
}
