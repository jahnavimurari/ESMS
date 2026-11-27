import React, { useState, useEffect } from 'react';
import { 
  X, AlertCircle, Clock, Calendar, User, Tag, 
  History, CheckCircle2, ShieldAlert, Flag, Building 
} from 'lucide-react';
import { taskService } from '../../services/taskService';

export default function TaskDetailsModal({ isOpen, onClose, task, onStatusClick }) {
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [activeTab, setActiveTab] = useState('details');

  useEffect(() => {
    if (!isOpen || !task) return;
    setActiveTab('details');

    const fetchHistory = async () => {
      setLoadingHistory(true);
      try {
        const res = await taskService.getTaskHistory(task.id);
        if (res.success) {
          setHistory(res.data);
        }
      } catch (err) {
        console.error('Failed to load task history', err);
      } finally {
        setLoadingHistory(false);
      }
    };

    fetchHistory();
  }, [isOpen, task]);

  if (!isOpen || !task) return null;

  const getPriorityBadge = (priority) => {
    const map = {
      URGENT: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
      HIGH: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      MEDIUM: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      LOW: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${map[priority] || map.MEDIUM}`}>
        {priority}
      </span>
    );
  };

  const getStatusBadge = (status) => {
    const map = {
      TODO: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
      IN_PROGRESS: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
      REVIEW: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
      COMPLETED: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
      BLOCKED: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
      CANCELLED: 'bg-slate-700/50 text-slate-400 border-slate-600',
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${map[status] || map.TODO}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <div className="flex items-center space-x-3">
            <div className="rounded-lg bg-indigo-500/20 p-2 text-indigo-400">
              <Tag className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono text-slate-400">Task #{task.id}</span>
                {getStatusBadge(task.status)}
                {getPriorityBadge(task.priority)}
                {task.is_overdue && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/30 text-rose-300 border border-rose-500/50 animate-pulse">
                    OVERDUE
                  </span>
                )}
              </div>
              <h2 className="text-base font-semibold text-white mt-1 line-clamp-1">{task.title}</h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab switcher */}
        <div className="flex border-b border-slate-800 px-6">
          <button
            onClick={() => setActiveTab('details')}
            className={`py-3 text-sm font-medium border-b-2 mr-6 transition-colors ${
              activeTab === 'details'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            Details & Criteria
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-3 text-sm font-medium border-b-2 transition-colors flex items-center space-x-1.5 ${
              activeTab === 'history'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <History className="h-4 w-4" />
            <span>Activity History ({history.length})</span>
          </button>
        </div>

        {/* Content body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {activeTab === 'details' ? (
            <>
              {/* Description */}
              <div>
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Task Description
                </h4>
                <div className="rounded-xl border border-slate-800 bg-slate-800/40 p-4 text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
                  {task.description || 'No detailed description provided.'}
                </div>
              </div>

              {/* Grid attributes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div className="rounded-xl border border-slate-800 bg-slate-800/30 p-3.5 space-y-2">
                  <div className="flex items-center text-xs text-slate-400">
                    <User className="h-4 w-4 mr-1.5 text-indigo-400" />
                    <span>Assignee Information</span>
                  </div>
                  <div className="text-sm font-medium text-white">{task.assignee_name || 'Unassigned'}</div>
                  <div className="text-xs text-slate-400">
                    Code: <span className="text-slate-200">{task.assignee_code || 'N/A'}</span>
                  </div>
                  {task.assignee_email && (
                    <div className="text-xs text-slate-400">
                      Email: <span className="text-slate-200">{task.assignee_email}</span>
                    </div>
                  )}
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-800/30 p-3.5 space-y-2">
                  <div className="flex items-center text-xs text-slate-400">
                    <Building className="h-4 w-4 mr-1.5 text-indigo-400" />
                    <span>Department & Category</span>
                  </div>
                  <div className="text-sm font-medium text-white">
                    {task.department_name || 'General Operations'}
                  </div>
                  <div className="text-xs text-slate-400">
                    Category: <span className="text-indigo-300">{task.category || 'Standard'}</span>
                  </div>
                  <div className="text-xs text-slate-400">
                    Creator: <span className="text-slate-200">{task.creator_email || 'System'}</span>
                  </div>
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-800/30 p-3.5 space-y-2">
                  <div className="flex items-center text-xs text-slate-400">
                    <Calendar className="h-4 w-4 mr-1.5 text-indigo-400" />
                    <span>Schedule & Timeline</span>
                  </div>
                  <div className="text-xs text-slate-300">
                    Start Date: <span className="font-medium text-white">{task.start_date || 'Not set'}</span>
                  </div>
                  <div className="text-xs text-slate-300">
                    Due Date:{' '}
                    <span className={`font-medium ${task.is_overdue ? 'text-rose-400' : 'text-white'}`}>
                      {task.due_date || 'No due date'}
                    </span>
                  </div>
                  {task.completed_at && (
                    <div className="text-xs text-emerald-400">
                      Completed: {new Date(task.completed_at).toLocaleDateString()}
                    </div>
                  )}
                </div>

                <div className="rounded-xl border border-slate-800 bg-slate-800/30 p-3.5 space-y-2">
                  <div className="flex items-center text-xs text-slate-400">
                    <Clock className="h-4 w-4 mr-1.5 text-indigo-400" />
                    <span>Timestamps</span>
                  </div>
                  <div className="text-xs text-slate-400">
                    Created: <span className="text-slate-300">{new Date(task.created_at).toLocaleString()}</span>
                  </div>
                  <div className="text-xs text-slate-400">
                    Last Updated: <span className="text-slate-300">{new Date(task.updated_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            /* History Timeline */
            <div className="space-y-4">
              {loadingHistory ? (
                <div className="text-center py-8 text-sm text-slate-400">Loading audit history...</div>
              ) : history.length === 0 ? (
                <div className="text-center py-8 text-sm text-slate-400">No activity history recorded yet.</div>
              ) : (
                <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                  {history.map((h) => (
                    <div key={h.id} className="relative">
                      <div className="absolute -left-6 top-1.5 h-3 w-3 rounded-full border-2 border-slate-900 bg-indigo-500" />
                      <div className="rounded-xl border border-slate-800 bg-slate-800/40 p-3 text-xs">
                        <div className="flex items-center justify-between text-slate-400 mb-1">
                          <span className="font-semibold text-indigo-400">{h.action.replace('_', ' ')}</span>
                          <span>{new Date(h.timestamp).toLocaleString()}</span>
                        </div>
                        <div className="text-slate-300">
                          By: <span className="text-white font-medium">{h.user_email || 'System'}</span>
                        </div>
                        {h.new_state?.comment && (
                          <div className="mt-2 rounded-lg bg-slate-900/60 p-2 text-slate-300 italic border border-slate-800">
                            "{h.new_state.comment}"
                          </div>
                        )}
                        {h.new_state?.status && h.previous_state?.status && (
                          <div className="mt-1 text-slate-400">
                            Status changed: <span className="text-slate-200">{h.previous_state.status}</span> →{' '}
                            <span className="text-emerald-400 font-semibold">{h.new_state.status}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-slate-800 px-6 py-4 bg-slate-900/80">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 transition-colors"
          >
            Close
          </button>
          {task.status !== 'CANCELLED' && onStatusClick && (
            <button
              type="button"
              onClick={() => {
                onClose();
                onStatusClick(task);
              }}
              className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors shadow-lg shadow-indigo-600/30"
            >
              Update Status
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

