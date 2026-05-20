export type ProviderInfo = {
  id: string;
  label: string;
  enabled: boolean;
  requires_key: boolean;
  model: string;
  reason?: string;
};

export type DocumentSummary = {
  source: string;
  title: string;
  checksum: string;
  chunk_count: number;
  ingested_at: string;
};

export type IngestSummary = {
  documents: number;
  chunks: number;
  sources: string[];
};

export type RetrievedChunk = {
  chunk_id: string;
  source: string;
  heading: string;
  text: string;
  score: number;
  matched_terms: string[];
};

export type Citation = {
  chunk_id: string;
  source: string;
  heading: string;
  quote?: string;
};

export type QueryResponse = {
  trace_id: string;
  provider: string;
  model: string;
  answer: string;
  citations: Citation[];
  retrieved_chunks: RetrievedChunk[];
  latency_ms: number;
  estimated_cost_usd: number;
  warnings: string[];
  diagnostics: {
    source_coverage: number;
    refused: boolean;
    retrieved_count: number;
    provider_latency_ms: number;
    confidence: number;
  };
};

export type CompareResponse = {
  question: string;
  results: QueryResponse[];
};

export type EvalResult = {
  case_id: string;
  passed: boolean;
  answer: string;
  matched_sources: string[];
  missing_terms: string[];
  reason: string;
};

export type EvalReport = {
  provider: string;
  total: number;
  passed: number;
  failed: number;
  results: EvalResult[];
};

export type TraceSummary = {
  trace_id: string;
  question: string;
  provider: string;
  latency_ms: number;
  refused: boolean;
  source_coverage: number;
  estimated_cost_usd: number;
  created_at: string;
};

export type MetricsSummary = {
  query_count: number;
  eval_runs: number;
  average_latency_ms: number;
  refusal_count: number;
  estimated_cost_usd: number;
  provider_usage: Record<string, number>;
  recent_failures: EvalResult[];
};
