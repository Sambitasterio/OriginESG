import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, Clock, AlertCircle, ChevronRight } from 'lucide-react';
import Layout from '../components/Layout';
import { fetchRuns, IngestionRun } from '../api/endpoints';

const SOURCE_LABELS: Record<string, string> = {
  SAP: 'SAP OData',
  UTILITY: 'Utility / Green Button',
  TRAVEL: 'Concur Travel',
};

const SOURCE_TYPES = ['SAP', 'UTILITY', 'TRAVEL'] as const;

function StatusBadge({ status }: { status: IngestionRun['status'] }) {
  const map = {
    COMPLETE:   { icon: CheckCircle,  text: 'Complete',   cls: 'text-green-700 bg-green-50 border-green-200' },
    FAILED:     { icon: XCircle,      text: 'Failed',     cls: 'text-red-700 bg-red-50 border-red-200' },
    PROCESSING: { icon: Clock,        text: 'Processing', cls: 'text-amber-700 bg-amber-50 border-amber-200' },
    PENDING:    { icon: AlertCircle,  text: 'Pending',    cls: 'text-gray-600 bg-gray-50 border-gray-200' },
  };
  const { icon: Icon, text, cls } = map[status] ?? map.PENDING;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${cls}`}>
      <Icon className="w-3.5 h-3.5" />
      {text}
    </span>
  );
}

function SourceCard({
  sourceType,
  lastRun,
}: {
  sourceType: string;
  lastRun: IngestionRun | undefined;
}) {
  const navigate = useNavigate();
  const borderColor = !lastRun
    ? 'border-gray-200'
    : lastRun.status === 'COMPLETE'
    ? 'border-l-green-400'
    : lastRun.status === 'FAILED'
    ? 'border-l-red-400'
    : 'border-l-amber-400';

  return (
    <div className={`bg-white rounded-xl border border-[#e8ede6] border-l-4 ${borderColor} p-5`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-xs font-medium text-[#7a8f76] uppercase tracking-wide mb-1">
            {sourceType}
          </p>
          <h3 className="text-sm font-semibold text-[#1f2a1d]">{SOURCE_LABELS[sourceType]}</h3>
        </div>
        {lastRun && <StatusBadge status={lastRun.status} />}
      </div>

      {lastRun ? (
        <>
          <div className="flex gap-4 mb-3">
            <div>
              <p className="text-xl font-semibold text-[#1f2a1d]">{lastRun.records_created}</p>
              <p className="text-xs text-[#7a8f76]">records ingested</p>
            </div>
            {lastRun.records_failed > 0 && (
              <div>
                <p className="text-xl font-semibold text-red-600">{lastRun.records_failed}</p>
                <p className="text-xs text-[#7a8f76]">failed</p>
              </div>
            )}
          </div>
          <p className="text-xs text-[#7a8f76]">
            Last run: {new Date(lastRun.started_at).toLocaleString()}
          </p>
        </>
      ) : (
        <p className="text-sm text-[#7a8f76]">No ingestion runs yet.</p>
      )}

      <button
        onClick={() => navigate('/ingest')}
        className="mt-4 flex items-center gap-1 text-xs font-medium text-[#336443] hover:text-[#1f2a1d] transition-colors"
      >
        Ingest data <ChevronRight className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

export default function DashboardPage() {
  const [runs, setRuns] = useState<IngestionRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchRuns()
      .then(setRuns)
      .catch(() => setError('Failed to load ingestion runs.'))
      .finally(() => setLoading(false));
  }, []);

  // Latest run per source type
  const lastRunBySource = SOURCE_TYPES.reduce<Record<string, IngestionRun | undefined>>(
    (acc, type) => {
      acc[type] = runs.find((r) => r.source_type === type);
      return acc;
    },
    {},
  );

  const totalRecords = runs.reduce((sum, r) => sum + r.records_created, 0);
  const totalFailed = runs.reduce((sum, r) => sum + r.records_failed, 0);
  const completedRuns = runs.filter((r) => r.status === 'COMPLETE').length;

  return (
    <Layout>
      <div className="px-8 py-8">
        <div className="mb-8">
          <h1
            className="text-2xl font-semibold text-[#1f2a1d] mb-1"
            style={{ fontFamily: '"Neue Haas Grotesk Display Pro 55 Roman", "Helvetica Neue", sans-serif' }}
          >
            Dashboard
          </h1>
          <p className="text-sm text-[#4b5b47]">Emissions ingestion status across all sources</p>
        </div>

        {/* Summary strip */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: 'Total Records', value: totalRecords },
            { label: 'Completed Runs', value: completedRuns },
            { label: 'Failed Records', value: totalFailed, red: totalFailed > 0 },
          ].map(({ label, value, red }) => (
            <div key={label} className="bg-white rounded-xl border border-[#e8ede6] px-5 py-4">
              <p className="text-xs font-medium text-[#7a8f76] mb-1">{label}</p>
              <p className={`text-2xl font-semibold ${red ? 'text-red-600' : 'text-[#1f2a1d]'}`}>
                {value}
              </p>
            </div>
          ))}
        </div>

        {/* Source cards */}
        {loading ? (
          <p className="text-sm text-[#7a8f76]">Loading…</p>
        ) : error ? (
          <p className="text-sm text-red-600">{error}</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {SOURCE_TYPES.map((type) => (
              <SourceCard key={type} sourceType={type} lastRun={lastRunBySource[type]} />
            ))}
          </div>
        )}

        {/* Recent runs table */}
        {runs.length > 0 && (
          <div className="mt-8">
            <h2 className="text-sm font-semibold text-[#1f2a1d] mb-3">Recent runs</h2>
            <div className="bg-white rounded-xl border border-[#e8ede6] overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#e8ede6] bg-[#f9faf8]">
                    {['Source', 'Status', 'Created', 'Failed', 'Started'].map((h) => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-medium text-[#7a8f76]">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {runs.slice(0, 10).map((run) => (
                    <tr key={run.id} className="border-b border-[#e8ede6] last:border-0 hover:bg-[#f9faf8]">
                      <td className="px-4 py-3 font-medium text-[#1f2a1d]">{run.source_name}</td>
                      <td className="px-4 py-3"><StatusBadge status={run.status} /></td>
                      <td className="px-4 py-3 text-[#4b5b47]">{run.records_created}</td>
                      <td className="px-4 py-3 text-red-600">{run.records_failed || '—'}</td>
                      <td className="px-4 py-3 text-[#7a8f76]">
                        {new Date(run.started_at).toLocaleString()}
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
