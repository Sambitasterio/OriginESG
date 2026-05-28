import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, CheckCircle, Flag, Lock, Loader2 } from 'lucide-react';
import Layout from '../components/Layout';
import {
  fetchRecord,
  approveRecord,
  flagRecord,
  NormalizedRecordDetail,
  RecordStatus,
  ReviewAction,
} from '../api/endpoints';

const STATUS_STYLES: Record<RecordStatus, string> = {
  PENDING:  'bg-gray-100 text-gray-600',
  APPROVED: 'bg-green-100 text-green-700',
  FLAGGED:  'bg-amber-100 text-amber-700',
  LOCKED:   'bg-blue-100 text-blue-700',
};

const ACTION_STYLES: Record<string, string> = {
  APPROVE: 'text-green-700',
  FLAG:    'text-amber-600',
  UNFLAG:  'text-gray-600',
  LOCK:    'text-blue-600',
};

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <p className="text-xs font-medium text-[#7a8f76] mb-0.5">{label}</p>
      <p className="text-sm text-[#1f2a1d]">{value ?? '—'}</p>
    </div>
  );
}

function FlagModal({ onConfirm, onClose }: { onConfirm: (c: string) => void; onClose: () => void }) {
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
          className="w-full border border-[#dde5db] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#336443]/30 focus:border-[#336443] resize-none mb-4"
        />
        <div className="flex gap-2 justify-end">
          <button onClick={onClose} className="px-4 py-2 text-sm text-[#4b5b47] hover:text-[#1f2a1d]">Cancel</button>
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

function AuditEntry({ action }: { action: ReviewAction }) {
  const label: Record<string, string> = {
    APPROVE: 'Approved',
    FLAG: 'Flagged',
    UNFLAG: 'Unflagged',
    LOCK: 'Locked',
  };
  return (
    <div className="flex items-start gap-3 py-3 border-b border-[#e8ede6] last:border-0">
      <div className="mt-0.5">
        {action.action === 'APPROVE' && <CheckCircle className="w-4 h-4 text-green-500" />}
        {action.action === 'FLAG' && <Flag className="w-4 h-4 text-amber-500" />}
        {action.action === 'LOCK' && <Lock className="w-4 h-4 text-blue-500" />}
        {action.action === 'UNFLAG' && <Flag className="w-4 h-4 text-gray-400" />}
      </div>
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${ACTION_STYLES[action.action]}`}>
          {label[action.action] ?? action.action}
          <span className="text-[#4b5b47] font-normal"> by {action.actor_name}</span>
        </p>
        {action.comment && (
          <p className="text-xs text-[#7a8f76] mt-0.5 italic">"{action.comment}"</p>
        )}
        <p className="text-xs text-[#7a8f76] mt-0.5">
          {new Date(action.created_at).toLocaleString()}
        </p>
      </div>
    </div>
  );
}

export default function RecordDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [record, setRecord] = useState<NormalizedRecordDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [showFlagModal, setShowFlagModal] = useState(false);

  useEffect(() => {
    if (!id) return;
    fetchRecord(Number(id))
      .then(setRecord)
      .catch(() => setError('Record not found.'))
      .finally(() => setLoading(false));
  }, [id]);

  const handleApprove = async () => {
    if (!record) return;
    setActionLoading(true);
    try {
      const updated = await approveRecord(record.id);
      setRecord((r) => r ? { ...r, status: updated.status } : r);
    } finally { setActionLoading(false); }
  };

  const handleFlagConfirm = async (comment: string) => {
    if (!record) return;
    setShowFlagModal(false);
    setActionLoading(true);
    try {
      const updated = await flagRecord(record.id, comment);
      setRecord((r) => r ? {
        ...r,
        status: updated.status,
        review_actions: [
          ...r.review_actions,
          { id: Date.now(), action: 'FLAG', comment, actor_name: 'you', created_at: new Date().toISOString() },
        ],
      } : r);
    } finally { setActionLoading(false); }
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh] text-sm text-[#7a8f76]">
          <Loader2 className="w-4 h-4 animate-spin mr-2" /> Loading…
        </div>
      </Layout>
    );
  }

  if (error || !record) {
    return (
      <Layout>
        <div className="px-8 py-8">
          <p className="text-sm text-red-600">{error || 'Record not found.'}</p>
        </div>
      </Layout>
    );
  }

  const locked = record.status === 'LOCKED';

  return (
    <Layout>
      <div className="px-8 py-8 max-w-5xl">
        {/* Breadcrumb + actions */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => navigate('/review')}
            className="flex items-center gap-1.5 text-sm text-[#4b5b47] hover:text-[#1f2a1d] transition-colors"
          >
            <ChevronLeft className="w-4 h-4" /> Back to Review
          </button>

          {!locked && (
            <div className="flex gap-2">
              <button
                onClick={handleApprove}
                disabled={actionLoading || record.status === 'APPROVED'}
                className="flex items-center gap-2 bg-[#336443] hover:bg-[#1f2a1d] disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-full transition-colors"
              >
                {actionLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
                Approve
              </button>
              <button
                onClick={() => setShowFlagModal(true)}
                disabled={actionLoading}
                className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-full transition-colors"
              >
                <Flag className="w-3.5 h-3.5" /> Flag
              </button>
            </div>
          )}
        </div>

        {/* Title row */}
        <div className="flex items-center gap-3 mb-6">
          <h1
            className="text-xl font-semibold text-[#1f2a1d]"
            style={{ fontFamily: '"Neue Haas Grotesk Display Pro 55 Roman", "Helvetica Neue", sans-serif' }}
          >
            Record #{record.id}
          </h1>
          <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${STATUS_STYLES[record.status]}`}>
            {record.status}
          </span>
          {locked && <Lock className="w-4 h-4 text-blue-500" />}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
          {/* Normalized data panel */}
          <div className="bg-white rounded-xl border border-[#e8ede6] p-5">
            <h2 className="text-xs font-semibold text-[#7a8f76] uppercase tracking-wide mb-4">Normalized Record</h2>
            <div className="grid grid-cols-2 gap-x-6 gap-y-4">
              <Field label="Activity Type" value={record.activity_type} />
              <Field label="GHG Scope" value={`Scope ${record.ghg_scope}`} />
              <Field label="Source" value={record.source_type} />
              <Field label="Run ID" value={`#${record.run_id}`} />
              <Field label="Original Value" value={`${record.original_value} ${record.original_unit}`} />
              <Field label="CO₂e (kg)" value={Number(record.normalized_value).toFixed(4)} />
              <Field label="Emission Factor" value={record.emission_factor_used} />
              <Field label="Factor Source" value={record.emission_factor_source} />
              <Field
                label="Period Start"
                value={record.period_start ? new Date(record.period_start).toLocaleDateString() : null}
              />
              <Field
                label="Period End"
                value={record.period_end ? new Date(record.period_end).toLocaleDateString() : null}
              />
              <Field label="Created" value={new Date(record.created_at).toLocaleString()} />
              <Field label="Updated" value={new Date(record.updated_at).toLocaleString()} />
            </div>
          </div>

          {/* Raw data panel */}
          <div className="bg-white rounded-xl border border-[#e8ede6] p-5">
            <h2 className="text-xs font-semibold text-[#7a8f76] uppercase tracking-wide mb-4">
              Raw Record (immutable)
            </h2>
            <div className="mb-3 flex gap-6 text-sm">
              <div>
                <p className="text-xs text-[#7a8f76] mb-0.5">Source Row ID</p>
                <p className="text-[#1f2a1d] font-mono text-xs">{record.raw.source_row_id || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-[#7a8f76] mb-0.5">Ingested at</p>
                <p className="text-[#1f2a1d] text-xs">{new Date(record.raw.created_at).toLocaleString()}</p>
              </div>
            </div>
            <div className="bg-[#f9faf8] rounded-lg border border-[#e8ede6] p-3 overflow-auto max-h-64">
              <pre className="text-xs text-[#1f2a1d] font-mono whitespace-pre-wrap break-all">
                {JSON.stringify(record.raw.raw_data, null, 2)}
              </pre>
            </div>
          </div>
        </div>

        {/* Audit trail */}
        <div className="bg-white rounded-xl border border-[#e8ede6] p-5">
          <h2 className="text-xs font-semibold text-[#7a8f76] uppercase tracking-wide mb-2">Audit Trail</h2>
          {record.review_actions.length === 0 ? (
            <p className="text-sm text-[#7a8f76] py-2">No actions yet.</p>
          ) : (
            record.review_actions.map((a) => <AuditEntry key={a.id} action={a} />)
          )}
        </div>
      </div>

      {showFlagModal && (
        <FlagModal onConfirm={handleFlagConfirm} onClose={() => setShowFlagModal(false)} />
      )}
    </Layout>
  );
}
