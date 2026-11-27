import React, { useState, useEffect } from 'react';
import { 
  Users, Calendar, Award, LogOut, CheckCircle2, 
  CheckSquare, Clock, AlertTriangle, ArrowRight, Filter, RotateCw
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { dashboardService } from '../../services/dashboardService';
import { employeeService } from '../../services/employeeService';
import DashboardStatCard from '../../components/dashboard/DashboardStatCard';
import AttendanceChart from '../../components/dashboard/AttendanceChart';
import DepartmentChart from '../../components/dashboard/DepartmentChart';
import LeaveChart from '../../components/dashboard/LeaveChart';
import TaskChart from '../../components/dashboard/TaskChart';

export default function HRDashboard() {
  const { user, logout } = useAuth();
  const [data, setData] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [selectedDept, setSelectedDept] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    employeeService.getDepartments(false)
      .then(res => { if (res?.data) setDepartments(res.data); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchDashboard(selectedDept);
  }, [selectedDept]);

  const fetchDashboard = async (deptId) => {
    setLoading(true);
    setError(null);
    try {
      const res = await dashboardService.getHRDashboard(deptId || null);
      if (res?.success) {
        setData(res.data);
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to load HR dashboard.');
    } finally {
      setLoading(false);
    }
  };

  const metrics = data?.metrics || {};
  const charts = data?.charts || {};

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Users size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Human Resources Operations</h1>
            <p className="text-xs text-slate-400">
              Logged in as <span className="font-semibold text-slate-200">{user?.email}</span> &bull; Workforce and Lifecycle Oversight
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          {departments.length > 0 && (
            <div className="flex items-center gap-2 text-xs bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5">
              <Filter className="w-3.5 h-3.5 text-emerald-400" />
              <select
                value={selectedDept}
                onChange={(e) => setSelectedDept(e.target.value)}
                className="bg-transparent text-xs text-slate-200 focus:outline-none"
              >
                <option value="" className="bg-slate-900 text-slate-200">All Departments</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id} className="bg-slate-900 text-slate-200">{d.name}</option>
                ))}
              </select>
            </div>
          )}

          <button
            onClick={() => fetchDashboard(selectedDept)}
            disabled={loading}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-all disabled:opacity-50"
          >
            <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-sm text-red-500">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
          <button onClick={() => fetchDashboard(selectedDept)} className="ml-auto underline font-medium">Retry</button>
        </div>
      )}

      {/* HR KPI Overview Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <DashboardStatCard 
          title="Active Workforce" 
          value={metrics.active_employees} 
          subtext={`Out of ${metrics.total_employees || 0} total headcount`}
          icon={Users} 
          color="#10b981" 
          bgLight="rgba(16, 185, 129, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Today's Attendance" 
          value={metrics.today_attendance?.present || 0} 
          subtext={`${metrics.today_attendance?.currently_checked_in || 0} actively clocked in`}
          badge={metrics.today_attendance?.currently_checked_in > 0 ? "Live" : null}
          icon={Clock} 
          color="#3b82f6" 
          bgLight="rgba(59, 130, 246, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Leave Approvals Queue" 
          value={metrics.pending_leave_approvals} 
          subtext={`${metrics.approved_leaves || 0} approved, ${metrics.rejected_leaves || 0} rejected`}
          badge={metrics.pending_leave_approvals > 0 ? "Action Required" : null}
          icon={Calendar} 
          color="#f59e0b" 
          bgLight="rgba(245, 158, 11, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Appraisal Progress" 
          value={`${metrics.review_completion_rate || 0}%`} 
          subtext={`${metrics.completed_reviews || 0} reviews finalized across ${metrics.active_cycles || 0} active cycles`}
          icon={Award} 
          color="#8b5cf6" 
          bgLight="rgba(139, 92, 246, 0.1)"
          loading={loading}
        />
      </div>

      {/* Task Summary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <DashboardStatCard 
          title="Total Assigned Tasks" 
          value={metrics.total_tasks} 
          subtext={`${metrics.completed_tasks || 0} completed`}
          icon={CheckSquare} 
          color="#6366f1" 
          bgLight="rgba(99, 102, 241, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Pending Deliverables" 
          value={metrics.pending_tasks} 
          subtext="In progress or under review"
          icon={CheckSquare} 
          color="#3b82f6" 
          bgLight="rgba(59, 130, 246, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Overdue Tasks" 
          value={metrics.overdue_tasks} 
          subtext="Requires HR or manager follow-up"
          icon={AlertTriangle} 
          color="#ef4444" 
          bgLight="rgba(239, 68, 68, 0.1)"
          loading={loading}
        />
      </div>

      {/* Visual Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AttendanceChart data={charts.attendance_trends} title="Attendance Trends (Last 14 Days)" days={14} />
        <DepartmentChart data={charts.department_employees} title="Department-wise Headcount" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LeaveChart data={charts.leave_trends} title="Leave Request Status Breakdown" />
        <TaskChart data={charts.task_completion} title="Task Completion Status" />
      </div>

      {/* Performance Cycle Completion Progress */}
      {charts.cycle_progress && charts.cycle_progress.length > 0 && (
        <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <Award className="w-4 h-4 text-emerald-400" /> Active Performance Cycles Progress
            </h3>
            <span className="text-xs text-[var(--text-secondary)]">Completion Rates</span>
          </div>

          <div className="space-y-3">
            {charts.cycle_progress.map((cycle) => (
              <div key={cycle.cycle_id} className="p-4 bg-[var(--background)] border border-[var(--border)] rounded-xl space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[var(--text-primary)] text-sm">{cycle.title}</span>
                  <span className="font-bold text-emerald-400">{cycle.completion_rate}% Completed</span>
                </div>
                <div className="w-full bg-[var(--surface)] h-2.5 rounded-full overflow-hidden border border-[var(--border)]">
                  <div 
                    className="bg-emerald-500 h-full rounded-full transition-all duration-300"
                    style={{ width: `${cycle.completion_rate}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[11px] text-[var(--text-secondary)] pt-1">
                  <span>{cycle.completed} of {cycle.total} reviews finalized</span>
                  {cycle.due_date && <span>Due: {cycle.due_date}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Module Portals Access */}
      <div className="pt-4 border-t border-[var(--border)]">
        <h2 className="text-sm font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-4">Operations Portals</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <a
            href="/employees"
            className="p-4 bg-[var(--surface)] border border-[var(--border)] rounded-2xl hover:border-emerald-500 hover:shadow-md transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-500">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Manage Employees</h3>
                <p className="text-xs text-[var(--text-secondary)]">Onboarding & records</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[var(--text-secondary)] group-hover:translate-x-1 group-hover:text-emerald-400 transition-all" />
          </a>

          <a
            href="/attendance"
            className="p-4 bg-[var(--surface)] border border-[var(--border)] rounded-2xl hover:border-emerald-500 hover:shadow-md transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-500">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Attendance Logs</h3>
                <p className="text-xs text-[var(--text-secondary)]">Shift monitoring</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[var(--text-secondary)] group-hover:translate-x-1 group-hover:text-emerald-400 transition-all" />
          </a>

          <a
            href="/leaves"
            className="p-4 bg-[var(--surface)] border border-[var(--border)] rounded-2xl hover:border-emerald-500 hover:shadow-md transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-500">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Leave Approvals</h3>
                <p className="text-xs text-[var(--text-secondary)]">Review applications</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[var(--text-secondary)] group-hover:translate-x-1 group-hover:text-emerald-400 transition-all" />
          </a>

          <a
            href="/performance"
            className="p-4 bg-[var(--surface)] border border-[var(--border)] rounded-2xl hover:border-emerald-500 hover:shadow-md transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-500">
                <Award className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Performance Hub</h3>
                <p className="text-xs text-[var(--text-secondary)]">Evaluate & calibrate</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[var(--text-secondary)] group-hover:translate-x-1 group-hover:text-emerald-400 transition-all" />
          </a>
        </div>
      </div>
    </div>
  );
}
