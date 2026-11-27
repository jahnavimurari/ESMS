import React, { useState, useEffect } from 'react';
import { 
  FileText, Search, Filter, RefreshCw, AlertCircle, 
  ChevronLeft, ChevronRight, Eye, X, ArrowLeft, Shield 
} from 'lucide-react';
import { adminService } from '../../services/adminService';

export default function AuditLogPage() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filters
  const [actionFilter, setActionFilter] = useState('');
  const [entityFilter, setEntityFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Inspection modal
  const [selectedLog, setSelectedLog] = useState(null);

  useEffect(() => {
    fetchAuditLogs();
  }, [page]);

  const fetchAuditLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, per_page: 15 };
      if (actionFilter.trim()) params.action = actionFilter.trim();
      if (entityFilter.trim()) params.entity_type = entityFilter.trim();
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const res = await adminService.listAuditLogs(params);
      if (res?.success) {
        setLogs(res.data.logs);
        setTotal(res.data.total);
        setPages(res.data.pages);
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to retrieve audit trail.');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchAuditLogs();
  };

  const getActionBadgeColor = (action) => {
    if (action.includes('CREATE') || action.includes('APPROVED')) return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    if (action.includes('UPDATE') || action.includes('RESET')) return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    if (action.includes('DELETE') || action.includes('DEACTIVATE') || action.includes('REJECTED')) return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
    return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors mb-2"
          >
            <ArrowLeft size={14} /> Back
          </button>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <FileText size={26} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">System Audit Trail</h1>
              <p className="text-xs text-slate-400">
                Immutable event history recording administrative actions, authentication changes, role updates, and state diffs.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={fetchAuditLogs}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-all disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-2.5 text-sm">
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* Filter Form */}
      <form onSubmit={handleFilterSubmit} className="flex gap-3 flex-wrap items-center bg-slate-900/60 border border-slate-800 p-4 rounded-2xl">
        <input
          type="text"
          placeholder="Action (e.g. UPDATE_USER_ROLE)"
          value={actionFilter}
          onChange={e => setActionFilter(e.target.value)}
          className="px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm flex-1 min-w-[180px] focus:border-blue-500 transition-colors"
        />
        <input
          type="text"
          placeholder="Entity (e.g. USER, TASK, LEAVE)"
          value={entityFilter}
          onChange={e => setEntityFilter(e.target.value)}
          className="px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm flex-1 min-w-[180px] focus:border-blue-500 transition-colors"
        />
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span>From:</span>
          <input
            type="date"
            value={startDate}
            onChange={e => setStartDate(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs"
          />
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span>To:</span>
          <input
            type="date"
            value={endDate}
            onChange={e => setEndDate(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs"
          />
        </div>
        <button
          type="submit"
          className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-md shadow-blue-500/20 transition-all"
        >
          Apply Filters
        </button>
      </form>

      {/* Audit Logs Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="bg-slate-800/60 border-b border-slate-800 text-slate-300 text-xs font-bold uppercase tracking-wider">
                <th className="py-3.5 px-4">Timestamp (UTC)</th>
                <th className="py-3.5 px-4">Actor ID</th>
                <th className="py-3.5 px-4">Action</th>
                <th className="py-3.5 px-4">Target Entity</th>
                <th className="py-3.5 px-4">Target ID</th>
                <th className="py-3.5 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    <div className="flex items-center justify-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
                      <span>Loading audit records...</span>
                    </div>
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No audit records matching criteria.
                  </td>
                </tr>
              ) : (
                logs.map(log => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 text-xs font-mono text-slate-400">
                      {new Date(log.created_at).toISOString().replace('T', ' ').substring(0, 19)}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-300">
                      {log.actor_user_id ? log.actor_user_id.substring(0, 8) + '...' : 'SYSTEM'}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold border ${getActionBadgeColor(log.action)}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-medium text-xs">
                      {log.target_entity_type || '—'}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-400">
                      {log.target_entity_id ? log.target_entity_id.substring(0, 8) + '...' : '—'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium text-blue-400 hover:text-white bg-blue-500/10 hover:bg-blue-600 border border-blue-500/20 transition-all"
                      >
                        <Eye size={12} /> View Diff
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between p-4 border-t border-slate-800 text-xs text-slate-400 gap-3">
          <div>
            Total Logged Events: <strong className="text-white font-semibold">{total}</strong> &bull; Page {page} of {pages}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-800/60 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft size={14} /> Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(pages, p + 1))}
              disabled={page >= pages}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-800/60 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              Next <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* State Inspection Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2 text-white font-bold text-base">
                <Shield className="w-5 h-5 text-purple-400" />
                <span>Audit Event Record #{selectedLog.id}</span>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                <span className="text-slate-400 block font-medium">Actor User ID</span>
                <span className="font-mono text-white text-xs">{selectedLog.actor_user_id || 'SYSTEM AUTOMATION'}</span>
              </div>
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                <span className="text-slate-400 block font-medium">Action Performed</span>
                <span className="font-semibold text-white">{selectedLog.action}</span>
              </div>
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                <span className="text-slate-400 block font-medium">Target Entity</span>
                <span className="text-white">{selectedLog.target_entity_type || '—'} ({selectedLog.target_entity_id || '—'})</span>
              </div>
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                <span className="text-slate-400 block font-medium">Timestamp</span>
                <span className="text-white">{new Date(selectedLog.created_at).toLocaleString()}</span>
              </div>
            </div>

            {/* State Diffs */}
            <div className="space-y-3">
              <div>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Before State</span>
                <pre className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono text-slate-300 overflow-x-auto max-h-48">
                  {selectedLog.before_state ? JSON.stringify(selectedLog.before_state, null, 2) : '<No prior state recorded>'}
                </pre>
              </div>

              <div>
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1.5">After State</span>
                <pre className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono text-emerald-400 overflow-x-auto max-h-48">
                  {selectedLog.after_state ? JSON.stringify(selectedLog.after_state, null, 2) : '<No new state recorded>'}
                </pre>
              </div>
            </div>

            <button
              onClick={() => setSelectedLog(null)}
              className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs border border-slate-700 transition-all"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
