import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Flag, ChevronRight, ChevronLeft, Loader2 } from 'lucide-react';
import Layout from '../components/Layout';
import {
  fetchRecords,
  approveRecord,
  batchApprove,
  NormalizedRecord,
  RecordStatus,
  RecordFilters,
} from '../api/endpoints';

const STATUS_STYLES: Record<RecordStatus, string> = {
  PENDING:  'bg-gray-100 text-gray-600',
  APPROVED: 'bg-green-100 text-green-700',
  FLAGGED:  'bg-amber-100 text-amber-700',
  LOCKED:   'bg-blue-100 text-blue-700',
};

const SCOPE_LABEL: Record<number, string> = { 1: 'Scope 1', 2: 'Scope 2', 3: 'Scope 3' };
const SOURCE_LABEL: Record<string, string> = { SAP: 'SAP OData', UTILITY: 'Utility', TRAVEL: 'Travel' };

function FlagModal({
  onConfirm,
  onClose,
}: {
  onConfirm: (comment: string) => void;
  onClose: () => void;
}) {
  const [comment, setComment] = useState('');
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="bg-white rounded-xl border border-[#e8ede6] shadow-lg p-6 w-full max-w-sm">
        <h3 className="text-sm font-semibold text-[#1f2a1d] mb-3">Flag record</h3>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Reason for flagging (optional)"
          rows={3}
          className="w-full border border-[#dde5db] rounded-lg px-3 py-2 text-sm text-[#1f2a1d] focus:outline-none focus:ring-2 focus:ring-[#336443]/30 focus:border-[#336443] resize-none mb-4"
        />
        <div className="flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-[#4b5b47] hover:text-[#1f2a1d] transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() => onConfirm(comment)}
            className="px-4 py-2 text-sm font-semibold bg-amber-500 hover:bg-amber-600 text-white rounded-full transition-colors"
          >
            Flag
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ReviewPage() {
  const navigate = useNavigate();
  const [records, setRecords] = useState<NormalizedRecord[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [filterStatus, setFilterStatus] = useState('');
  const [filterScope, setFilterScope] = useState('');
  const [filterSource, setFilterSource] = useState('');

  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [batchLoading, setBatchLoading] = useState(false);

  const [flagTarget, setFlagTarget] = useState<number | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const PAGE_SIZE = 20;
  const totalPages = Math.ceil(count / PAGE_SIZE);

  const load = useCallback(() => {
    setLoading(true);
    setError('');
    const filters: RecordFilters = { page };
    if (filterStatus) filters.status = filterStatus;
    if (filterScope) filters.scope = filterScope;
    if (filterSource) filters.source_type = filterSource;
    fetchRecords(filters)
      .then((data) => { setRecords(data.results); setCount(data.count); })
      .catch(() => setError('Failed to load records.'))
      .finally(() => setLoading(false));
  }, [page, filterStatus, filterScope, filterSource]);

  useEffect(() => { load(); }, [load]);

  // Reset page when filters change
  useEffect(() => { setPage(1); setSelected(new Set()); }, [filterStatus, filterScope, filterSource]);

  const handleApprove = async (id: number) => {
    setActionLoading(id);
    try {
      const updated = await approveRecord(id);
      setRecords((prev) => prev.map((r) => r.id === id ? { ...r, status: updated.status } : r));
    } finally { setActionLoading(null); }
  };

  const handleFlagConfirm = async (comment: string) => {
    if (!flagTarget) return;
    const id = flagTarget;
    setFlagTarget(null);
    setActionLoading(id);
    try {
      const { flagRecord } = await import('../api/endpoints');
      const updated = await flagRecord(id, comment);
      setRecords((prev) => prev.map((r) => r.id === id ? { ...r, status: updated.status } : r));
    } finally { setActionLoading(null); }
  };

  const handleBatchApprove = async () => {
    if (!selected.size) return;
    setBatchLoading(true);
    try {
      await batchApprove(Array.from(selected));
      setSelected(new Set());
      load();
    } finally { setBatchLoading(false); }
  };

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    const approvable = records.filter((r) => r.status !== 'LOCKED').map((r) => r.id);
    if (approvable.every((id) => selected.has(id))) {
      setSelected(new Set());
    } else {
      setSelected(new Set(approvable));
    }
  };

  const allSelected = records.length > 0 &&
    records.filter((r) => r.status !== 'LOCKED').every((r) => selected.has(r.id));

  const selectEl = (
    label: string,
    value: string,
    onChange: (v: string) => void,
    options: { value: string; label: string }[],
  ) => (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="border border-[#dde5db] rounded-lg px-3 py-1.5 text-sm text-[#1f2a1d] focus:outline-none focus:ring-2 focus:ring-[#336443]/30 focus:border-[#336443] bg-white"
      aria-label={label}
    >
      <option value="">{label}: All</option>
      {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );

  return (
    <Layout>
      <div className="px-8 py-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1
              className="text-2xl font-semibold text-[#1f2a1d] mb-1"
              style={{ fontFamily: '"Neue Haas Grotesk Display Pro 55 Roman", "Helvetica Neue", sans-serif' }}
            >
              Review Records
            </h1>
            <p className="text-sm text-[#4b5b47]">
              {count} record{count !== 1 ? 's' : ''} {filterStatus || filterScope || filterSource ? 'matching filters' : 'total'}
            </p>
          </div>

          {selected.size > 0 && (
            <button
              onClick={handleBatchApprove}
              disabled={batchLoading}
              className="flex items-center gap-2 bg-[#336443] hover:bg-[#1f2a1d] disabled:opacity-60 text-white text-sm font-semibold px-4 py-2 rounded-full transition-colors"
            >
              {batchLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
              Approve {selected.size} selected
            </button>
          )}
        </div>

        {/* Filters */}
        <div className="flex gap-3 mb-5 flex-wrap">
          {selectEl('Status', filterStatus, setFilterStatus, [
            { value: 'PENDING', label: 'Pending' },
            { value: 'APPROVED', label: 'Approved' },
            { value: 'FLAGGED', label: 'Flagged' },
            { value: 'LOCKED', label: 'Locked' },
          ])}
          {selectEl('Scope', filterScope, setFilterScope, [
            { value: '1', label: 'Scope 1' },
            { value: '2', label: 'Scope 2' },
            { value: '3', label: 'Scope 3' },
          ])}
          {selectEl('Source', filterSource, setFilterSource, [
            { value: 'SAP', label: 'SAP OData' },
            { value: 'UTILITY', label: 'Utility' },
            { value: 'TRAVEL', label: 'Travel' },
          ])}
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-[#e8ede6] overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-16 text-sm text-[#7a8f76]">
              <Loader2 className="w-4 h-4 animate-spin mr-2" /> Loading…
            </div>
          ) : error ? (
            <p className="text-sm text-red-600 p-6">{error}</p>
          ) : records.length === 0 ? (
            <p className="text-sm text-[#7a8f76] p-6">No records found.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#e8ede6] bg-[#f9faf8]">
                  <th className="px-4 py-3 w-8">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      onChange={toggleSelectAll}
                      className="rounded border-[#dde5db] accent-[#336443]"
                    />
                  </th>
                  {['ID', 'Activity', 'Source', 'Scope', 'Original', 'CO₂e (kg)', 'Period', 'Status', 'Actions'].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-[#7a8f76]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {records.map((rec) => {
                  const locked = rec.status === 'LOCKED';
                  const isActing = actionLoading === rec.id;
                  return (
                    <tr
                      key={rec.id}
                      className="border-b border-[#e8ede6] last:border-0 hover:bg-[#f9faf8] cursor-pointer"
                      onClick={() => navigate(`/review/${rec.id}`)}
                    >
                      <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                        {!locked && (
                          <input
                            type="checkbox"
                            checked={selected.has(rec.id)}
                            onChange={() => toggleSelect(rec.id)}
                            className="rounded border-[#dde5db] accent-[#336443]"
                          />
                        )}
                      </td>
                      <td className="px-4 py-3 text-[#7a8f76] text-xs">#{rec.id}</td>
                      <td className="px-4 py-3 font-medium text-[#1f2a1d] max-w-[180px] truncate" title={rec.activity_type}>
                        {rec.activity_type}
                      </td>
                      <td className="px-4 py-3 text-[#4b5b47]">{SOURCE_LABEL[rec.source_type] ?? rec.source_type}</td>
                      <td className="px-4 py-3 text-[#4b5b47]">{SCOPE_LABEL[rec.ghg_scope]}</td>
                      <td className="px-4 py-3 text-[#4b5b47] text-xs">{rec.original_value} {rec.original_unit}</td>
                      <td className="px-4 py-3 font-medium text-[#1f2a1d]">{Number(rec.normalized_value).toFixed(2)}</td>
                      <td className="px-4 py-3 text-[#7a8f76] text-xs">
                        {rec.period_start ? new Date(rec.period_start).toLocaleDateString() : '—'}
                        {rec.period_end ? ` – ${new Date(rec.period_end).toLocaleDateString()}` : ''}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_STYLES[rec.status]}`}>
                          {rec.status}
                        </span>
                      </td>
                      <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center gap-1.5">
                          {!locked && (
                            <>
                              <button
                                onClick={() => handleApprove(rec.id)}
                                disabled={isActing || rec.status === 'APPROVED'}
                                title="Approve"
                                className="p-1.5 rounded-lg text-green-600 hover:bg-green-50 disabled:opacity-40 transition-colors"
                              >
                                {isActing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
                              </button>
                              <button
                                onClick={() => setFlagTarget(rec.id)}
                                disabled={isActing}
                                title="Flag"
                                className="p-1.5 rounded-lg text-amber-500 hover:bg-amber-50 disabled:opacity-40 transition-colors"
                              >
                                <Flag className="w-3.5 h-3.5" />
                              </button>
                            </>
                          )}
                          <button
                            onClick={() => navigate(`/review/${rec.id}`)}
                            title="View detail"
                            className="p-1.5 rounded-lg text-[#7a8f76] hover:bg-[#f5f7f4] transition-colors"
                          >
                            <ChevronRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <p className="text-xs text-[#7a8f76]">
              Page {page} of {totalPages} ({count} records)
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => p - 1)}
                disabled={page === 1}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-[#4b5b47] border border-[#dde5db] rounded-lg hover:bg-[#f5f7f4] disabled:opacity-40 transition-colors"
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Prev
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page === totalPages}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-[#4b5b47] border border-[#dde5db] rounded-lg hover:bg-[#f5f7f4] disabled:opacity-40 transition-colors"
              >
                Next <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {flagTarget !== null && (
        <FlagModal
          onConfirm={handleFlagConfirm}
          onClose={() => setFlagTarget(null)}
        />
      )}
    </Layout>
  );
}
