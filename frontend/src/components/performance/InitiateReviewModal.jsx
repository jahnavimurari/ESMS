import React, { useState } from 'react';
import { X, UserCheck, AlertCircle } from 'lucide-react';
import { performanceService } from '../../services/performanceService';

export default function InitiateReviewModal({ isOpen, onClose, onSuccess, cycles, employees }) {
  const [formData, setFormData] = useState({
    cycle_id: cycles.length > 0 ? cycles[0].id : '',
    employee_id: employees.length > 0 ? employees[0].id : '',
    review_period: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const payload = {
        cycle_id: parseInt(formData.cycle_id, 10),
        employee_id: formData.employee_id,
        review_period: formData.review_period ? formData.review_period.trim() : undefined
      };

      const res = await performanceService.createReview(payload);
      if (res?.success) {
        onSuccess(res.data);
        onClose();
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || err.message || 'Failed to initiate review.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-indigo-500" />
            <h2 className="text-lg font-semibold text-[var(--text-primary)]">Initiate Performance Review</h2>
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
          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
              Performance Cycle *
            </label>
            <select
              name="cycle_id"
              required
              value={formData.cycle_id}
              onChange={handleChange}
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-indigo-500"
            >
              <option value="">Select Cycle</option>
              {cycles.filter(c => c.status === 'ACTIVE').map((cycle) => (
                <option key={cycle.id} value={cycle.id}>
                  {cycle.title} (Due: {cycle.due_date})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
              Select Employee *
            </label>
            <select
              name="employee_id"
              required
              value={formData.employee_id}
              onChange={handleChange}
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-indigo-500"
            >
              <option value="">Select Employee</option>
              {employees.filter(e => e.status === 'ACTIVE').map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.employee_code} - {emp.full_name} ({emp.designation || 'Staff'})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-1">
              Review Period / Label (Optional)
            </label>
            <input
              type="text"
              name="review_period"
              value={formData.review_period}
              onChange={handleChange}
              placeholder="Defaults to cycle title if left blank"
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-sm focus:outline-none focus:border-indigo-500"
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
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-xl text-sm transition-colors flex items-center gap-2"
            >
              {loading ? 'Initiating...' : 'Initiate Review'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

