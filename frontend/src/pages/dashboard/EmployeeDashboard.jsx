import React, { useState, useEffect } from 'react';
import { 
  User, Clock, CheckSquare, Award, LogOut, CheckCircle2, 
  Calendar, Star, AlertTriangle, ArrowRight, ShieldCheck, Briefcase, RotateCw
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { dashboardService } from '../../services/dashboardService';
import DashboardStatCard from '../../components/dashboard/DashboardStatCard';
import AttendanceChart from '../../components/dashboard/AttendanceChart';
import TaskChart from '../../components/dashboard/TaskChart';

export default function EmployeeDashboard() {
  const { user, logout } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await dashboardService.getEmployeeDashboard();
      if (res?.success) {
        setData(res.data);
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to load employee dashboard.');
    } finally {
      setLoading(false);
    }
  };

  const profile = data?.profile || {};
  const attendance = data?.attendance || {};
  const leaves = data?.leaves || {};
  const tasks = data?.tasks || {};
  const performance = data?.performance || {};
  const charts = data?.charts || {};

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <User size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Employee Personal Workspace</h1>
            <p className="text-xs text-slate-400">
              Logged in as <span className="font-semibold text-slate-200">{user?.email}</span> &bull; Self-Service Operations
            </p>
          </div>
        </div>

        <button
          onClick={fetchDashboard}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-all disabled:opacity-50 self-start sm:self-auto"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-sm text-red-500">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
          <button onClick={fetchDashboard} className="ml-auto underline font-medium">Retry</button>
        </div>
      )}

      {/* 1. Profile Summary Card */}
      <div className="p-6 bg-[var(--surface)] border border-[var(--border)] rounded-2xl shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-500 flex items-center justify-center font-bold text-xl">
            {profile.full_name ? profile.full_name.charAt(0) : 'E'}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-[var(--text-primary)]">{profile.full_name || 'Loading profile...'}</h2>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {profile.status || 'ACTIVE'}
              </span>
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-0.5">
              {profile.employee_code} • {profile.designation} • {profile.department} Department
            </p>
          </div>
        </div>

        {/* Today's live check-in pill */}
        <div className="flex items-center gap-3 p-3 bg-[var(--background)] border border-[var(--border)] rounded-xl">
          <Clock className={`w-5 h-5 ${attendance.today_status === 'CHECKED_IN' ? 'text-emerald-400 animate-pulse' : 'text-zinc-400'}`} />
          <div className="text-xs">
            <span className="text-[var(--text-secondary)] block">Today's Punch Status</span>
            <span className={`font-bold ${attendance.today_status === 'CHECKED_IN' ? 'text-emerald-400' : 'text-[var(--text-primary)]'}`}>
              {attendance.today_status === 'CHECKED_IN' ? 'Currently Clocked In' : attendance.today_status === 'CHECKED_OUT' ? 'Clocked Out' : 'Not Clocked In'}
            </span>
          </div>
          <a
            href="/attendance"
            className="ml-2 px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-medium text-xs transition-colors"
          >
            Clock In/Out
          </a>
        </div>
      </div>

      {/* 2. Monthly Attendance & Leave KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <DashboardStatCard 
          title="Attendance This Month" 
          value={`${attendance.month_attendance_days || 0} Days`} 
          subtext="Total present shifts this month"
          icon={Clock} 
          color="#10b981" 
          bgLight="rgba(16, 185, 129, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Hours Completed" 
          value={`${attendance.month_working_hours || 0} hrs`} 
          subtext="Cumulative monthly duration"
          icon={Clock} 
          color="#3b82f6" 
          bgLight="rgba(59, 130, 246, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Pending Leaves" 
          value={leaves.pending_requests || 0} 
          subtext="Awaiting manager approval"
          badge={leaves.pending_requests > 0 ? "Under Review" : null}
          icon={Calendar} 
          color="#f59e0b" 
          bgLight="rgba(245, 158, 11, 0.1)"
          loading={loading}
        />
        {/* Performance Appraisal Score (STRICT: only if completed) */}
        <DashboardStatCard 
          title="Latest Appraisal Score" 
          value={performance.latest_rating ? `${performance.latest_rating} / 5` : (performance.has_review ? "In Progress" : "None")} 
          subtext={performance.latest_rating_label || (performance.latest_review_status ? `Status: ${performance.latest_review_status}` : "No review on file")}
          badge={performance.latest_rating ? "Finalized" : null}
          icon={Award} 
          color="#ec4899" 
          bgLight="rgba(236, 72, 153, 0.1)"
          loading={loading}
        />
      </div>

      {/* 3. Task Progress KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <DashboardStatCard 
          title="Assigned Tasks" 
          value={tasks.assigned_tasks || 0} 
          subtext={`${tasks.completed_tasks || 0} deliverables completed`}
          icon={CheckSquare} 
          color="#6366f1" 
          bgLight="rgba(99, 102, 241, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Pending Tasks" 
          value={tasks.pending_tasks || 0} 
          subtext="Todo, in progress & review"
          icon={CheckSquare} 
          color="#3b82f6" 
          bgLight="rgba(59, 130, 246, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="My Overdue Tasks" 
          value={tasks.overdue_tasks || 0} 
          subtext={tasks.overdue_tasks > 0 ? "Past due date!" : "All deadlines met"}
          badge={tasks.overdue_tasks > 0 ? "Urgent" : null}
          icon={AlertTriangle} 
          color="#ef4444" 
          bgLight="rgba(239, 68, 68, 0.1)"
          loading={loading}
        />
      </div>

      {/* 4. Charts: Attendance 7d and Task Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AttendanceChart data={charts.attendance_7d} title="My Daily Attendance (Last 7 Days)" days={7} />
        <TaskChart data={charts.task_distribution} title="My Task Status Breakdown" />
      </div>

      {/* 5. Leave Balances & Recent Leave History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Entitlements Card */}
        <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl space-y-3">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
            <Calendar className="w-4 h-4 text-amber-400" /> My Annual Leave Balances
          </h3>
          <div className="space-y-2">
            {leaves.balances && leaves.balances.length > 0 ? (
              leaves.balances.map((b) => (
                <div key={b.leave_type_id} className="p-3 bg-[var(--background)] border border-[var(--border)] rounded-xl flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-[var(--text-primary)] block">{b.leave_type_name} ({b.leave_type_code})</span>
                    <span className="text-[var(--text-secondary)] text-[11px]">{b.approved_days} used • {b.pending_days} pending</span>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-amber-400 text-sm">{b.remaining_balance}</span>
                    <span className="text-[var(--text-secondary)] block text-[10px]">remaining</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-[var(--text-secondary)] italic">No leave entitlement records available.</p>
            )}
          </div>
        </div>

        {/* Recent Leaves History */}
        <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <Calendar className="w-4 h-4 text-indigo-400" /> Recent Leave Applications
            </h3>
            <a href="/leaves" className="text-xs text-indigo-400 font-semibold hover:underline">Apply Leave →</a>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[var(--background)] border-b border-[var(--border)] text-[var(--text-secondary)] uppercase">
                <tr>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Dates</th>
                  <th className="py-2.5 px-3">Days</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {charts.leave_history && charts.leave_history.length > 0 ? (
                  charts.leave_history.map((lr) => (
                    <tr key={lr.id} className="hover:bg-[var(--surface-hover)]">
                      <td className="py-2.5 px-3 font-semibold text-[var(--text-primary)]">{lr.leave_type}</td>
                      <td className="py-2.5 px-3 text-[var(--text-secondary)]">{lr.start_date} to {lr.end_date}</td>
                      <td className="py-2.5 px-3 font-bold text-[var(--text-primary)]">{lr.total_days}</td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                          lr.status === 'APPROVED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                          lr.status === 'PENDING' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                          'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                        }`}>
                          {lr.status}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" className="py-4 text-center text-[var(--text-secondary)]">No recent leave requests.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Module Portals Access */}
      <div className="pt-4 border-t border-[var(--border)]">
        <h2 className="text-sm font-bold text-[var(--text-secondary)] uppercase tracking-wider mb-4">Quick Workspaces</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <a
            href="/attendance"
            className="p-4 bg-[var(--surface)] border border-[var(--border)] rounded-2xl hover:border-amber-500 hover:shadow-md transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-500">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">My Attendance</h3>
                <p className="text-xs text-[var(--text-secondary)]">Clock in & history</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[var(--text-secondary)] group-hover:translate-x-1 group-hover:text-amber-400 transition-all" />
          </a>

          <a
            href="/leaves"
            className="p-4 bg-[var(--surface)] border border-[var(--border)] rounded-2xl hover:border-amber-500 hover:shadow-md transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-500">
                <Calendar className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Leave Portal</h3>
                <p className="text-xs text-[var(--text-secondary)]">Apply & balances</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[var(--text-secondary)] group-hover:translate-x-1 group-hover:text-amber-400 transition-all" />
          </a>

          <a
            href="/tasks"
            className="p-4 bg-[var(--surface)] border border-[var(--border)] rounded-2xl hover:border-amber-500 hover:shadow-md transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-500">
                <CheckSquare className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">My Tasks</h3>
                <p className="text-xs text-[var(--text-secondary)]">Objectives & milestones</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[var(--text-secondary)] group-hover:translate-x-1 group-hover:text-amber-400 transition-all" />
          </a>

          <a
            href="/performance"
            className="p-4 bg-[var(--surface)] border border-[var(--border)] rounded-2xl hover:border-amber-500 hover:shadow-md transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-500">
                <Award className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">My Appraisals</h3>
                <p className="text-xs text-[var(--text-secondary)]">Self-assess & feedback</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[var(--text-secondary)] group-hover:translate-x-1 group-hover:text-amber-400 transition-all" />
          </a>
        </div>
      </div>
    </div>
  );
}
