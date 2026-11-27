import React, { useState, useEffect } from 'react';
import { X, AlertCircle, CheckCircle2, RotateCw } from 'lucide-react';
import { taskService } from '../../services/taskService';
import { useAuth } from '../../context/AuthContext';

export default function UpdateStatusModal({ isOpen, onClose, task, onSuccess }) {
  const { role } = useAuth();
  const isHRorAdmin = role === 'ADMIN' || role === 'HR';

  const [status, setStatus] = useState('');
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !task) return;
    setError(null);
    setComment('');

    // Pre-select next logical status
    if (task.status === 'TODO') {
      setStatus('IN_PROGRESS');
    } else if (task.status === 'IN_PROGRESS') {
      setStatus(isHRorAdmin ? 'COMPLETED' : 'REVIEW');
    } else if (task.status === 'REVIEW') {
      setStatus(isHRorAdmin ? 'COMPLETED' : 'IN_PROGRESS');
    } else {
      setStatus(task.status);
    }
  }, [isOpen, task, isHRorAdmin]);

  if (!isOpen || !task) return null;

  // Compute allowed transitions
  let allowedStatuses = [];
  if (isHRorAdmin) {
    if (task.status === 'TODO') allowedStatuses = ['IN_PROGRESS', 'BLOCKED', 'CANCELLED'];
    else if (task.status === 'IN_PROGRESS') allowedStatuses = ['REVIEW', 'COMPLETED', 'BLOCKED', 'CANCELLED'];
    else if (task.status === 'REVIEW') allowedStatuses = ['COMPLETED', 'IN_PROGRESS', 'BLOCKED', 'CANCELLED'];
    else if (task.status === 'BLOCKED') allowedStatuses = ['IN_PROGRESS', 'TODO', 'CANCELLED'];
    else if (task.status === 'COMPLETED') allowedStatuses = ['IN_PROGRESS', 'CANCELLED'];
  } else {
    // Employee transitions
    if (task.status === 'TODO') allowedStatuses = ['IN_PROGRESS', 'BLOCKED'];
    else if (task.status === 'IN_PROGRESS') allowedStatuses = ['REVIEW', 'BLOCKED'];
    else if (task.status === 'REVIEW') allowedStatuses = ['IN_PROGRESS'];
    else if (task.status === 'BLOCKED') allowedStatuses = ['IN_PROGRESS', 'TODO'];
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!status) {
      setError('Please select a target status.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await taskService.updateTaskStatus(task.id, status, comment.trim() || null);
      if (res.success) {
        onSuccess();
        onClose();
      }
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.message || 'Failed to update status';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <div className="flex items-center space-x-2">
            <div className="rounded-lg bg-emerald-500/20 p-2 text-emerald-400">
              <RotateCw className="h-5 w-5" />
            </div>
            <h2 className="text-lg font-semibold text-white">Update Status</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="flex items-center space-x-2 rounded-lg bg-rose-500/10 border border-rose-500/30 p-3 text-sm text-rose-400">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="rounded-lg bg-slate-800/60 p-3 border border-slate-800">
            <div className="text-xs text-slate-400">Task Title</div>
            <div className="text-sm font-medium text-white truncate">{task.title}</div>
            <div className="mt-2 flex items-center space-x-2 text-xs">
              <span className="text-slate-400">Current Status:</span>
              <span className="font-semibold text-indigo-400">{task.status}</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              New Status <span className="text-rose-400">*</span>
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3.5 py-2 text-sm text-white focus:border-emerald-500 focus:outline-none"
            >
              {allowedStatuses.map((st) => (
                <option key={st} value={st}>
                  {st.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Progress Comment / Feedback
            </label>
            <textarea
              rows={3}
              placeholder="Provide a brief update or notes regarding this status change..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-emerald-600 px-5 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50 transition-colors shadow-lg shadow-emerald-600/30"
            >
              {submitting ? 'Updating...' : 'Update Status'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

