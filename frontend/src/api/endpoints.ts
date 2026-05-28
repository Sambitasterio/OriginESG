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

export const fetchDataSources = () =>
  api.get<{ results: DataSource[] }>('/api/datasources/').then((r) => r.data.results);

export const fetchRuns = () =>
  api.get<{ results: IngestionRun[] }>('/api/runs/').then((r) => r.data.results);

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
