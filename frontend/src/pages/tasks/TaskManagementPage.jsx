import React, { useState, useEffect } from 'react';
import { 
  CheckSquare, Plus, Filter, Search, Clock, 
  AlertCircle, CheckCircle2, RotateCw, RefreshCw, 
  Calendar, Flag, User, ShieldAlert, ArrowUpDown, ChevronLeft, ChevronRight, Eye, Edit, Trash2 
} from 'lucide-react';
import { taskService } from '../../services/taskService';
import { employeeService } from '../../services/employeeService';
import { useAuth } from '../../context/AuthContext';
import CreateTaskModal from '../../components/tasks/CreateTaskModal';
import EditTaskModal from '../../components/tasks/EditTaskModal';
import UpdateStatusModal from '../../components/tasks/UpdateStatusModal';
import TaskDetailsModal from '../../components/tasks/TaskDetailsModal';

export default function TaskManagementPage() {
  const { role, user } = useAuth();
  const isHRorAdmin = role === 'ADMIN' || role === 'HR';

  const [activeTab, setActiveTab] = useState(isHRorAdmin ? 'all' : 'my');
  const [tasks, setTasks] = useState([]);
  const [summary, setSummary] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedPriority, setSelectedPriority] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [overdueOnly, setOverdueOnly] = useState(false);

  // Pagination
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState({ total: 0, page: 1, per_page: 15, pages: 1 });

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isStatusOpen, setIsStatusOpen] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);

  const loadMetadata = async () => {
    if (isHRorAdmin) {
      try {
        const deptRes = await employeeService.getDepartments(false);
        if (deptRes?.data) setDepartments(deptRes.data);
      } catch (err) {
        console.error('Failed to load departments', err);
      }
    }
  };

  const loadSummary = async () => {
    try {
      const res = await taskService.getTaskSummary(selectedDept || null);
      if (res?.success) {
        setSummary(res.data);
      }
    } catch (err) {
      console.error('Failed to load summary', err);
    }
  };

  const loadTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page,
        per_page: 15,
        search: search.trim() || undefined,
        status: selectedStatus || undefined,
        priority: selectedPriority || undefined,
        department_id: selectedDept || undefined,
        overdue: overdueOnly ? 'true' : undefined,
      };

      let res;
      if (activeTab === 'my') {
        res = await taskService.getMyTasks(params);
      } else {
        res = await taskService.getTasks(params);
      }

      if (res.success) {
        setTasks(res.data);
        if (res.pagination) {
          setPagination(res.pagination);
        }
      }
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.message || 'Failed to load tasks';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetadata();
  }, [isHRorAdmin]);

  useEffect(() => {
    loadSummary();
  }, [selectedDept, isHRorAdmin]);

  useEffect(() => {
    loadTasks();
  }, [activeTab, page, selectedStatus, selectedPriority, selectedDept, overdueOnly]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadTasks();
  };

  const handleCancelTask = async (task) => {
    if (!window.confirm(`Are you sure you want to cancel Task #${task.id} (${task.title})?`)) {
      return;
    }

    try {
      const res = await taskService.cancelTask(task.id, 'Cancelled from management dashboard');
      if (res.success) {
        setSuccess(`Task #${task.id} has been cancelled.`);
        loadTasks();
        loadSummary();
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to cancel task');
    }
  };

  const getPriorityBadge = (priority) => {
    const map = {
      URGENT: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
      HIGH: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      MEDIUM: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      LOW: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    };
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${map[priority] || map.MEDIUM}`}>
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
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${map[status] || map.TODO}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 p-6 sm:p-8 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <CheckSquare className="h-6 w-6 text-indigo-400" />
              <h1 className="text-2xl font-bold tracking-tight text-white">Task Management</h1>
            </div>
            <p className="mt-1 text-sm text-slate-400">
              Track project objectives, workflows, overdue milestones, and team deliverables.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => {
                loadTasks();
                loadSummary();
              }}
              className="inline-flex items-center rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </button>

            {isHRorAdmin && (
              <button
                onClick={() => setIsCreateOpen(true)}
                className="inline-flex items-center rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition-colors"
              >
                <Plus className="mr-1.5 h-4 w-4" />
                Create Task
              </button>
            )}
          </div>
        </div>

        {/* Notifications */}
        {error && (
          <div className="flex items-center justify-between rounded-xl bg-rose-500/10 border border-rose-500/30 p-4 text-sm text-rose-400">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
            <button onClick={() => setError(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        {success && (
          <div className="flex items-center justify-between rounded-xl bg-emerald-500/10 border border-emerald-500/30 p-4 text-sm text-emerald-400">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>{success}</span>
            </div>
            <button onClick={() => setSuccess(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        {/* KPI Summary Cards */}
        {summary && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="text-xs font-medium text-slate-400">Total Tasks</div>
              <div className="mt-1 text-2xl font-bold text-white">{summary.total_tasks}</div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="text-xs font-medium text-blue-400">In Progress</div>
              <div className="mt-1 text-2xl font-bold text-blue-400">{summary.in_progress}</div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="text-xs font-medium text-purple-400">In Review</div>
              <div className="mt-1 text-2xl font-bold text-purple-400">{summary.review}</div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="text-xs font-medium text-emerald-400">Completed</div>
              <div className="mt-1 text-2xl font-bold text-emerald-400">{summary.completed}</div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="text-xs font-medium text-rose-400">Overdue</div>
              <div className="mt-1 text-2xl font-bold text-rose-400">{summary.overdue}</div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="text-xs font-medium text-amber-400">High / Urgent</div>
              <div className="mt-1 text-2xl font-bold text-amber-400">{summary.high_priority}</div>
            </div>
          </div>
        )}

        {/* Navigation Tabs (All vs My Tasks) */}
        {isHRorAdmin && (
          <div className="flex border-b border-slate-800">
            <button
              onClick={() => {
                setActiveTab('all');
                setPage(1);
              }}
              className={`py-3 px-4 text-sm font-semibold border-b-2 transition-colors ${
                activeTab === 'all'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              All Team Tasks
            </button>
            <button
              onClick={() => {
                setActiveTab('my');
                setPage(1);
              }}
              className={`py-3 px-4 text-sm font-semibold border-b-2 transition-colors ${
                activeTab === 'my'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-white'
              }`}
            >
              My Assigned Tasks
            </button>
          </div>
        )}

        {/* Filters Bar */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4 space-y-3">
          <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search tasks by title, description or category..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-xl border border-slate-700 bg-slate-800/80 pl-10 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <button
              type="submit"
              className="rounded-xl bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-700 hover:text-white transition-colors"
            >
              Search
            </button>
          </form>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <select
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value);
                setPage(1);
              }}
              className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="TODO">To Do</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="REVIEW">In Review</option>
              <option value="COMPLETED">Completed</option>
              <option value="BLOCKED">Blocked</option>
              <option value="CANCELLED">Cancelled</option>
            </select>

            <select
              value={selectedPriority}
              onChange={(e) => {
                setSelectedPriority(e.target.value);
                setPage(1);
              }}
              className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
            >
              <option value="">All Priorities</option>
              <option value="URGENT">Urgent</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>

            {isHRorAdmin && activeTab === 'all' && (
              <select
                value={selectedDept}
                onChange={(e) => {
                  setSelectedDept(e.target.value);
                  setPage(1);
                }}
                className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-white focus:border-indigo-500 focus:outline-none"
              >
                <option value="">All Departments</option>
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name}
                  </option>
                ))}
              </select>
            )}

            <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={overdueOnly}
                onChange={(e) => {
                  setOverdueOnly(e.target.checked);
                  setPage(1);
                }}
                className="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-0"
              />
              <span className="text-rose-400 font-medium">Overdue Tasks Only</span>
            </label>

            {(search || selectedStatus || selectedPriority || selectedDept || overdueOnly) && (
              <button
                onClick={() => {
                  setSearch('');
                  setSelectedStatus('');
                  setSelectedPriority('');
                  setSelectedDept('');
                  setOverdueOnly(false);
                  setPage(1);
                }}
                className="text-xs text-indigo-400 hover:text-indigo-300 ml-auto"
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>

        {/* Task Table */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-xl">
          {loading ? (
            <div className="p-12 text-center text-sm text-slate-400">Loading tasks...</div>
          ) : tasks.length === 0 ? (
            <div className="p-12 text-center">
              <CheckSquare className="mx-auto h-12 w-12 text-slate-600 mb-3" />
              <h3 className="text-base font-semibold text-white">No tasks found</h3>
              <p className="text-sm text-slate-400 mt-1">
                {activeTab === 'my'
                  ? 'You have no assigned tasks matching current filters.'
                  : 'No tasks found matching the selected criteria.'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-900 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-6 py-3.5">Task & Category</th>
                    <th className="px-6 py-3.5">Assignee</th>
                    <th className="px-6 py-3.5">Priority</th>
                    <th className="px-6 py-3.5">Status</th>
                    <th className="px-6 py-3.5">Due Date</th>
                    <th className="px-6 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {tasks.map((task) => (
                    <tr key={task.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-medium text-white">{task.title}</div>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className="text-xs text-slate-400">#{task.id}</span>
                          {task.category && (
                            <span className="text-[11px] font-mono text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded">
                              {task.category}
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="text-slate-200 font-medium">{task.assignee_name || 'Unassigned'}</div>
                        <div className="text-xs text-slate-500">
                          {task.department_name || 'General'}
                        </div>
                      </td>

                      <td className="px-6 py-4">{getPriorityBadge(task.priority)}</td>

                      <td className="px-6 py-4">{getStatusBadge(task.status)}</td>

                      <td className="px-6 py-4">
                        <div className={task.is_overdue ? 'text-rose-400 font-medium' : 'text-slate-300'}>
                          {task.due_date || 'No due date'}
                        </div>
                        {task.is_overdue && (
                          <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider">
                            Overdue
                          </span>
                        )}
                      </td>

                      <td className="px-6 py-4 text-right space-x-1">
                        <button
                          onClick={() => {
                            setSelectedTask(task);
                            setIsDetailsOpen(true);
                          }}
                          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
                          title="View Details & History"
                        >
                          <Eye className="h-4 w-4" />
                        </button>

                        {task.status !== 'CANCELLED' && (
                          <button
                            onClick={() => {
                              setSelectedTask(task);
                              setIsStatusOpen(true);
                            }}
                            className="rounded-lg p-1.5 text-emerald-400 hover:bg-emerald-500/20 transition-colors"
                            title="Update Status"
                          >
                            <RotateCw className="h-4 w-4" />
                          </button>
                        )}

                        {isHRorAdmin && task.status !== 'CANCELLED' && (
                          <button
                            onClick={() => {
                              setSelectedTask(task);
                              setIsEditOpen(true);
                            }}
                            className="rounded-lg p-1.5 text-blue-400 hover:bg-blue-500/20 transition-colors"
                            title="Edit Task"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                        )}

                        {isHRorAdmin && task.status !== 'CANCELLED' && (
                          <button
                            onClick={() => handleCancelTask(task)}
                            className="rounded-lg p-1.5 text-rose-400 hover:bg-rose-500/20 transition-colors"
                            title="Cancel Task"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Controls */}
          {pagination.pages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-800 px-6 py-3.5 bg-slate-900/40 text-xs text-slate-400">
              <div>
                Showing page <span className="text-white font-medium">{pagination.page}</span> of{' '}
                <span className="text-white font-medium">{pagination.pages}</span> ({pagination.total} total tasks)
              </div>
              <div className="flex items-center space-x-2">
                <button
                  disabled={pagination.page <= 1}
                  onClick={() => setPage(page - 1)}
                  className="rounded-lg border border-slate-700 p-1.5 hover:bg-slate-800 disabled:opacity-40 transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  disabled={pagination.page >= pagination.pages}
                  onClick={() => setPage(page + 1)}
                  className="rounded-lg border border-slate-700 p-1.5 hover:bg-slate-800 disabled:opacity-40 transition-colors"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <CreateTaskModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSuccess={() => {
          setSuccess('Task created successfully.');
          loadTasks();
          loadSummary();
        }}
      />

      <EditTaskModal
        isOpen={isEditOpen}
        task={selectedTask}
        onClose={() => {
          setIsEditOpen(false);
          setSelectedTask(null);
        }}
        onSuccess={() => {
          setSuccess('Task updated successfully.');
          loadTasks();
          loadSummary();
        }}
      />

      <UpdateStatusModal
        isOpen={isStatusOpen}
        task={selectedTask}
        onClose={() => {
          setIsStatusOpen(false);
          setSelectedTask(null);
        }}
        onSuccess={() => {
          setSuccess('Task status updated successfully.');
          loadTasks();
          loadSummary();
        }}
      />

      <TaskDetailsModal
        isOpen={isDetailsOpen}
        task={selectedTask}
        onClose={() => {
          setIsDetailsOpen(false);
          setSelectedTask(null);
        }}
        onStatusClick={(t) => {
          setSelectedTask(t);
          setIsStatusOpen(true);
        }}
      />
    </div>
  );
}

