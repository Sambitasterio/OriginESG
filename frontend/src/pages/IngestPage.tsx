import { useEffect, useState, FormEvent } from 'react';
import { CheckCircle, XCircle, Upload, Play } from 'lucide-react';
import Layout from '../components/Layout';
import {
  fetchDataSources,
  fetchRuns,
  ingestSAP,
  ingestUtility,
  ingestTravel,
  DataSource,
  IngestionRun,
  IngestResult,
} from '../api/endpoints';

function ResultBanner({ result }: { result: IngestResult }) {
  const ok = result.failed === 0;
  return (
    <div className={`flex items-start gap-3 p-4 rounded-lg border text-sm mt-3 ${
      ok ? 'bg-green-50 border-green-200 text-green-800' : 'bg-amber-50 border-amber-200 text-amber-800'
    }`}>
      {ok ? <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" /> : <XCircle className="w-4 h-4 mt-0.5 shrink-0" />}
      <div>
        <p className="font-medium">
          {result.created} record{result.created !== 1 ? 's' : ''} ingested
          {result.failed > 0 ? `, ${result.failed} failed` : ''}
          {' '}— run #{result.run_id}
        </p>
        {result.errors.length > 0 && (
          <ul className="mt-1 text-xs space-y-0.5 list-disc list-inside">
            {result.errors.slice(0, 5).map((e, i) => <li key={i}>{e}</li>)}
            {result.errors.length > 5 && <li>…and {result.errors.length - 5} more</li>}
          </ul>
        )}
      </div>
    </div>
  );
}

function SourceSelector({
  sources,
  sourceType,
  value,
  onChange,
}: {
  sources: DataSource[];
  sourceType: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const filtered = sources.filter((s) => s.source_type === sourceType);
  if (filtered.length === 0)
    return (
      <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
        No active {sourceType} data source found. Create one in{' '}
        <a href="/admin/organizations/datasource/add/" target="_blank" className="underline">
          Django admin
        </a>.
      </p>
    );
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full border border-[#dde5db] rounded-lg px-3 py-2 text-sm text-[#1f2a1d] focus:outline-none focus:ring-2 focus:ring-[#336443]/30 focus:border-[#336443] transition-colors"
    >
      <option value="">Select data source…</option>
      {filtered.map((s) => (
        <option key={s.id} value={s.id}>{s.name} ({s.organization_name})</option>
      ))}
    </select>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-[#e8ede6] p-6">
      <h2 className="text-sm font-semibold text-[#1f2a1d] mb-4">{title}</h2>
      {children}
    </div>
  );
}

export default function IngestPage() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [runs, setRuns] = useState<IngestionRun[]>([]);

  // SAP state
  const [sapSourceId, setSapSourceId] = useState('');
  const [sapJson, setSapJson] = useState('');
  const [sapLoading, setSapLoading] = useState(false);
  const [sapResult, setSapResult] = useState<IngestResult | null>(null);
  const [sapError, setSapError] = useState('');

  // Utility state
  const [utilSourceId, setUtilSourceId] = useState('');
  const [utilFile, setUtilFile] = useState<File | null>(null);
  const [utilLoading, setUtilLoading] = useState(false);
  const [utilResult, setUtilResult] = useState<IngestResult | null>(null);
  const [utilError, setUtilError] = useState('');

  // Travel state
  const [travelSourceId, setTravelSourceId] = useState('');
  const [travelJson, setTravelJson] = useState('');
  const [travelLoading, setTravelLoading] = useState(false);
  const [travelResult, setTravelResult] = useState<IngestResult | null>(null);
  const [travelError, setTravelError] = useState('');

  useEffect(() => {
    fetchDataSources().then(setSources).catch(() => {});
    fetchRuns().then(setRuns).catch(() => {});
  }, []);

  const refreshRuns = () => fetchRuns().then(setRuns).catch(() => {});

  const handleSAP = async (e: FormEvent) => {
    e.preventDefault();
    setSapError(''); setSapResult(null); setSapLoading(true);
    try {
      const payload = JSON.parse(sapJson);
      const result = await ingestSAP(Number(sapSourceId), payload);
      setSapResult(result);
      refreshRuns();
    } catch (err: unknown) {
      setSapError(err instanceof SyntaxError ? 'Invalid JSON.' : 'Ingestion failed. Check the payload.');
    } finally { setSapLoading(false); }
  };

  const handleUtility = async (e: FormEvent) => {
    e.preventDefault();
    setUtilError(''); setUtilResult(null);
    if (!utilFile) { setUtilError('Please select a CSV file.'); return; }
    setUtilLoading(true);
    try {
      const result = await ingestUtility(Number(utilSourceId), utilFile);
      setUtilResult(result);
      refreshRuns();
    } catch {
      setUtilError('Ingestion failed. Check the CSV format.');
    } finally { setUtilLoading(false); }
  };

  const handleTravel = async (e: FormEvent) => {
    e.preventDefault();
    setTravelError(''); setTravelResult(null); setTravelLoading(true);
    try {
      const payload = JSON.parse(travelJson);
      const result = await ingestTravel(Number(travelSourceId), payload);
      setTravelResult(result);
      refreshRuns();
    } catch (err: unknown) {
      setTravelError(err instanceof SyntaxError ? 'Invalid JSON.' : 'Ingestion failed. Check the payload.');
    } finally { setTravelLoading(false); }
  };

  const submitBtn = (loading: boolean, label: string, icon: React.ReactNode) => (
    <button
      type="submit"
      disabled={loading}
      className="flex items-center gap-2 bg-[#1f2a1d] hover:bg-[#2a3827] disabled:opacity-60 text-white text-sm font-semibold px-5 py-2.5 rounded-full transition-colors mt-2"
    >
      {icon}
      {loading ? 'Processing…' : label}
    </button>
  );

  const fieldLabel = (text: string) => (
    <label className="text-xs font-medium text-[#4b5b47] mb-1 block">{text}</label>
  );

  const errorMsg = (msg: string) => msg ? (
    <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2 mt-2">{msg}</p>
  ) : null;

  return (
    <Layout>
      <div className="px-8 py-8">
        <div className="mb-8">
          <h1
            className="text-2xl font-semibold text-[#1f2a1d] mb-1"
            style={{ fontFamily: '"Neue Haas Grotesk Display Pro 55 Roman", "Helvetica Neue", sans-serif' }}
          >
            Ingest Data
          </h1>
          <p className="text-sm text-[#4b5b47]">Upload or trigger ingestion for each emissions source</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
          {/* SAP */}
          <SectionCard title="SAP OData — Scope 1">
            <form onSubmit={handleSAP} className="flex flex-col gap-3">
              {fieldLabel('Data source')}
              <SourceSelector sources={sources} sourceType="SAP" value={sapSourceId} onChange={setSapSourceId} />
              {fieldLabel('OData V4 JSON payload')}
              <textarea
                value={sapJson}
                onChange={(e) => setSapJson(e.target.value)}
                rows={6}
                placeholder={'{\n  "value": [...]\n}'}
                className="w-full border border-[#dde5db] rounded-lg px-3 py-2 text-xs font-mono text-[#1f2a1d] focus:outline-none focus:ring-2 focus:ring-[#336443]/30 focus:border-[#336443] resize-none"
              />
              {submitBtn(sapLoading, 'Run SAP Ingestion', <Play className="w-3.5 h-3.5" />)}
              {errorMsg(sapError)}
              {sapResult && <ResultBanner result={sapResult} />}
            </form>
          </SectionCard>

          {/* Utility */}
          <SectionCard title="Utility CSV — Scope 2">
            <form onSubmit={handleUtility} className="flex flex-col gap-3">
              {fieldLabel('Data source')}
              <SourceSelector sources={sources} sourceType="UTILITY" value={utilSourceId} onChange={setUtilSourceId} />
              {fieldLabel('Green Button CSV file')}
              <label className="flex flex-col items-center justify-center border-2 border-dashed border-[#dde5db] rounded-lg px-4 py-6 cursor-pointer hover:border-[#336443] transition-colors">
                <Upload className="w-6 h-6 text-[#7a8f76] mb-2" />
                <span className="text-xs text-[#7a8f76]">
                  {utilFile ? utilFile.name : 'Click to upload .csv'}
                </span>
                <input
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={(e) => setUtilFile(e.target.files?.[0] ?? null)}
                />
              </label>
              {submitBtn(utilLoading, 'Upload CSV', <Upload className="w-3.5 h-3.5" />)}
              {errorMsg(utilError)}
              {utilResult && <ResultBanner result={utilResult} />}
            </form>
          </SectionCard>

          {/* Travel */}
          <SectionCard title="Concur Travel — Scope 3">
            <form onSubmit={handleTravel} className="flex flex-col gap-3">
              {fieldLabel('Data source')}
              <SourceSelector sources={sources} sourceType="TRAVEL" value={travelSourceId} onChange={setTravelSourceId} />
              {fieldLabel('Concur Itinerary JSON payload')}
              <textarea
                value={travelJson}
                onChange={(e) => setTravelJson(e.target.value)}
                rows={6}
                placeholder={'{\n  "Itineraries": [...]\n}'}
                className="w-full border border-[#dde5db] rounded-lg px-3 py-2 text-xs font-mono text-[#1f2a1d] focus:outline-none focus:ring-2 focus:ring-[#336443]/30 focus:border-[#336443] resize-none"
              />
              {submitBtn(travelLoading, 'Run Travel Ingestion', <Play className="w-3.5 h-3.5" />)}
              {errorMsg(travelError)}
              {travelResult && <ResultBanner result={travelResult} />}
            </form>
          </SectionCard>
        </div>

        {/* Run history */}
        {runs.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold text-[#1f2a1d] mb-3">Run history</h2>
            <div className="bg-white rounded-xl border border-[#e8ede6] overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#e8ede6] bg-[#f9faf8]">
                    {['Run ID', 'Source', 'Status', 'Created', 'Failed', 'Started', 'Completed'].map((h) => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-medium text-[#7a8f76]">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run) => (
                    <tr key={run.id} className="border-b border-[#e8ede6] last:border-0 hover:bg-[#f9faf8]">
                      <td className="px-4 py-3 text-[#7a8f76]">#{run.id}</td>
                      <td className="px-4 py-3 font-medium text-[#1f2a1d]">{run.source_name}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          run.status === 'COMPLETE' ? 'bg-green-100 text-green-700' :
                          run.status === 'FAILED' ? 'bg-red-100 text-red-700' :
                          'bg-amber-100 text-amber-700'
                        }`}>{run.status}</span>
                      </td>
                      <td className="px-4 py-3 text-[#4b5b47]">{run.records_created}</td>
                      <td className="px-4 py-3 text-red-600">{run.records_failed || '—'}</td>
                      <td className="px-4 py-3 text-[#7a8f76] text-xs">{new Date(run.started_at).toLocaleString()}</td>
                      <td className="px-4 py-3 text-[#7a8f76] text-xs">
                        {run.completed_at ? new Date(run.completed_at).toLocaleString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
