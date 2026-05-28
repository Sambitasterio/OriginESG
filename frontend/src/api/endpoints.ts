import api from './client';

export interface DataSource {
  id: number;
  name: string;
  source_type: 'SAP' | 'UTILITY' | 'TRAVEL';
  organization_name: string;
  is_active: boolean;
}

export interface IngestionRun {
  id: number;
  source_name: string;
  source_type: 'SAP' | 'UTILITY' | 'TRAVEL';
  status: 'PENDING' | 'PROCESSING' | 'COMPLETE' | 'FAILED';
  records_created: number;
  records_failed: number;
  error_log: string;
  started_at: string;
  completed_at: string | null;
}

export interface IngestResult {
  run_id: number;
  created: number;
  failed: number;
  errors: string[];
}

export type RecordStatus = 'PENDING' | 'APPROVED' | 'FLAGGED' | 'LOCKED';
export type SourceType = 'SAP' | 'UTILITY' | 'TRAVEL';

export interface NormalizedRecord {
  id: number;
  ghg_scope: 1 | 2 | 3;
  activity_type: string;
  original_value: string;
  original_unit: string;
  normalized_value: string;
  normalized_unit: string;
  emission_factor_source: string;
  status: RecordStatus;
  period_start: string | null;
  period_end: string | null;
  source_type: SourceType;
  run_id: number;
  created_at: string;
}

export interface ReviewAction {
  id: number;
  action: 'APPROVE' | 'FLAG' | 'UNFLAG' | 'LOCK';
  comment: string;
  actor_name: string;
  created_at: string;
}

export interface NormalizedRecordDetail extends NormalizedRecord {
  emission_factor_used: string;
  updated_at: string;
  raw: {
    id: number;
    source_row_id: string;
    raw_data: Record<string, unknown>;
    created_at: string;
  };
  review_actions: ReviewAction[];
}

export interface RecordFilters {
  status?: string;
  scope?: string;
  source_type?: string;
  page?: number;
}

export interface PaginatedRecords {
  count: number;
  next: string | null;
  previous: string | null;
  results: NormalizedRecord[];
}

export const fetchDataSources = () =>
  api.get<{ results: DataSource[] }>('/api/datasources/').then((r) => r.data.results);

export const fetchRuns = () =>
  api.get<{ results: IngestionRun[] }>('/api/runs/').then((r) => r.data.results);

export const fetchRecords = (filters: RecordFilters = {}) => {
  const params: Record<string, string> = {};
  if (filters.status) params.status = filters.status;
  if (filters.scope) params.scope = filters.scope;
  if (filters.source_type) params.source_type = filters.source_type;
  if (filters.page && filters.page > 1) params.page = String(filters.page);
  return api.get<PaginatedRecords>('/api/records/', { params }).then((r) => r.data);
};

export const fetchRecord = (id: number) =>
  api.get<NormalizedRecordDetail>(`/api/records/${id}/`).then((r) => r.data);

export const approveRecord = (id: number) =>
  api.post<{ id: number; status: RecordStatus }>(`/api/records/${id}/approve/`).then((r) => r.data);

export const flagRecord = (id: number, comment: string) =>
  api.post<{ id: number; status: RecordStatus }>(`/api/records/${id}/flag/`, { comment }).then((r) => r.data);

export const batchApprove = (ids: number[]) =>
  api.post<{ approved: number; ids: number[] }>('/api/records/batch-approve/', { ids }).then((r) => r.data);

export const ingestSAP = (data_source_id: number, payload: object) =>
  api.post<IngestResult>('/api/ingest/sap/', { data_source_id, payload }).then((r) => r.data);

export const ingestUtility = (data_source_id: number, file: File) => {
  const form = new FormData();
  form.append('data_source_id', String(data_source_id));
  form.append('file', file);
  return api.post<IngestResult>('/api/ingest/utility/', form).then((r) => r.data);
};

export const ingestTravel = (data_source_id: number, payload: object) =>
  api.post<IngestResult>('/api/ingest/travel/', { data_source_id, payload }).then((r) => r.data);
