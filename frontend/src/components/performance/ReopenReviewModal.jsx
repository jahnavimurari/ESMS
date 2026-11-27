import React, { useState } from 'react';
import { X, RotateCcw, AlertCircle } from 'lucide-react';
import { performanceService } from '../../services/performanceService';

export default function ReopenReviewModal({ isOpen, onClose, onSuccess, review }) {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !review) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!reason || reason.trim().length < 5) {
      setError('A valid justification reason (at least 5 characters) is required to reopen this review.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const res = await performanceService.reopenReview(review.id, reason.trim());
      if (res?.success) {
        onSuccess(res.data);
        onClose();
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || err.message || 'Failed to reopen review.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <RotateCcw className="w-5 h-5 text-amber-500" />
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Reopen Completed Review</h2>
          </div>
          <button onClick={onClose} className="p-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)] rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mx-6 mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-2 text-sm text-red-500">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-xs text-[var(--text-secondary)]">
            Reopening a completed review transitions it back to <strong className="text-[var(--text-primary)]">MANAGER_REVIEW</strong>. 
            All adjustments are permanently logged in the compliance audit trail.
          </p>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
              Justification Reason *
            </label>
            <textarea
              required
              rows="3"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="State the official justification (e.g. executive calibration, grievance appeal, retroactive project milestone credit)..."
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-amber-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--border)]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-[var(--border)] rounded-xl text-sm font-medium hover:bg-[var(--surface-hover)]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 bg-amber-600 hover:bg-amber-700 text-white font-medium rounded-xl text-sm transition-colors flex items-center gap-2"
            >
              {loading ? 'Reopening...' : 'Confirm Reopen'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

