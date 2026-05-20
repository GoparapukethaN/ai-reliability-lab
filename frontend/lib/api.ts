import type {
  CompareResponse,
  DocumentSummary,
  EvalReport,
  IngestSummary,
  MetricsSummary,
  ProviderInfo,
  QueryResponse,
  TraceSummary
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers =
    init?.body instanceof FormData
      ? init.headers
      : {
          "Content-Type": "application/json",
          ...(init?.headers ?? {})
        };
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getProviders(): Promise<ProviderInfo[]> {
  return request<ProviderInfo[]>("/providers");
}

export function getDocuments(): Promise<DocumentSummary[]> {
  return request<DocumentSummary[]>("/documents");
}

export function ingestCorpus(): Promise<IngestSummary> {
  return request<IngestSummary>("/ingest", { method: "POST" });
}

export function uploadDocument(file: File): Promise<IngestSummary> {
  const formData = new FormData();
  formData.append("file", file);
  return request<IngestSummary>("/documents/upload", {
    method: "POST",
    body: formData
  });
}

export function askQuestion(
  question: string,
  provider: string,
  limit: number
): Promise<QueryResponse> {
  return request<QueryResponse>("/query", {
    method: "POST",
    body: JSON.stringify({ question, provider, limit })
  });
}

export function compareProviders(
  question: string,
  providers: string[],
  limit: number
): Promise<CompareResponse> {
  return request<CompareResponse>("/query/compare", {
    method: "POST",
    body: JSON.stringify({ question, providers: providers.length ? providers : undefined, limit })
  });
}

export function runEvaluation(): Promise<EvalReport> {
  return request<EvalReport>("/eval/run", { method: "POST" });
}

export function getTraces(): Promise<TraceSummary[]> {
  return request<TraceSummary[]>("/traces");
}

export function getMetricsSummary(): Promise<MetricsSummary> {
  return request<MetricsSummary>("/metrics/summary");
}
