import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldCheck, Users, Building, LogOut, CheckCircle2, 
  CheckSquare, Award, Clock, AlertTriangle, RotateCw, 
  ArrowRight, Calendar
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { dashboardService } from '../../services/dashboardService';
import DashboardStatCard from '../../components/dashboard/DashboardStatCard';
import AttendanceChart from '../../components/dashboard/AttendanceChart';
import DepartmentChart from '../../components/dashboard/DepartmentChart';
import LeaveChart from '../../components/dashboard/LeaveChart';
import TaskChart from '../../components/dashboard/TaskChart';
import PerformanceChart from '../../components/dashboard/PerformanceChart';

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [attendanceWindow, setAttendanceWindow] = useState(7); // 7 or 30 days

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await dashboardService.getAdminDashboard();
      if (res?.success) {
        setData(res.data);
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to load admin dashboard.');
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
          <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <ShieldCheck size={28} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Admin Command Center</h1>
            <p className="text-xs text-slate-400">
              Logged in as <span className="font-semibold text-slate-200">{user?.email}</span> &bull; Full administrative authority
            </p>
          </div>
        </div>

        <button
          onClick={fetchDashboard}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-all disabled:opacity-50 self-start sm:self-auto"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-sm text-red-500">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
          <button onClick={fetchDashboard} className="ml-auto underline font-medium">Retry</button>
        </div>
      )}

      {/* Primary KPI Grid (15 Key Metrics) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Workforce */}
        <DashboardStatCard 
          title="Total Employees" 
          value={metrics.total_employees} 
          subtext={`${metrics.active_employees || 0} active, ${metrics.inactive_employees || 0} inactive`}
          icon={Users} 
          color="#3b82f6" 
          bgLight="rgba(59, 130, 246, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Departments" 
          value={metrics.total_departments} 
          subtext="Operational teams"
          icon={Building} 
          color="#8b5cf6" 
          bgLight="rgba(139, 92, 246, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Today's Attendance" 
          value={metrics.today_attendance_count} 
          subtext={`${metrics.currently_checked_in || 0} currently checked in`}
          badge={metrics.currently_checked_in > 0 ? "Active Sessions" : null}
          icon={Clock} 
          color="#10b981" 
          bgLight="rgba(16, 185, 129, 0.1)"
          loading={loading}
        />
        {/* Leaves */}
        <DashboardStatCard 
          title="Pending Leaves" 
          value={metrics.pending_leaves} 
          subtext={`${metrics.approved_leaves || 0} approved leaves`}
          icon={Calendar} 
          color="#f59e0b" 
          bgLight="rgba(245, 158, 11, 0.1)"
          loading={loading}
        />
        {/* Performance Rating */}
        <DashboardStatCard 
          title="Avg Rating" 
          value={metrics.average_rating ? `${metrics.average_rating} / 5` : "0.00"} 
          subtext={`${metrics.completed_reviews || 0} completed reviews`}
          icon={Award} 
          color="#ec4899" 
          bgLight="rgba(236, 72, 153, 0.1)"
          loading={loading}
        />
      </div>

      {/* Secondary Task & Lifecycle KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <DashboardStatCard 
          title="Total Tasks" 
          value={metrics.total_tasks} 
          subtext={`${metrics.completed_tasks || 0} tasks completed`}
          icon={CheckSquare} 
          color="#6366f1" 
          bgLight="rgba(99, 102, 241, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Pending Tasks" 
          value={metrics.pending_tasks} 
          subtext="Todo, in progress & review"
          icon={CheckSquare} 
          color="#3b82f6" 
          bgLight="rgba(59, 130, 246, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Overdue Tasks" 
          value={metrics.overdue_tasks} 
          subtext="Action required"
          icon={AlertTriangle} 
          color="#ef4444" 
          bgLight="rgba(239, 68, 68, 0.1)"
          loading={loading}
        />
        <DashboardStatCard 
          title="Active Review Cycles" 
          value={metrics.active_cycles} 
          subtext="Performance evaluation"
          icon={Award} 
          color="#10b981" 
          bgLight="rgba(16, 185, 129, 0.1)"
          loading={loading}
        />
      </div>

      {/* Visual Analytics Grid (Recharts) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Attendance Trends with 7d / 30d toggle */}
        <div className="space-y-2">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">Attendance Activity</span>
            <div className="flex items-center gap-1 bg-[var(--surface)] border border-[var(--border)] rounded-xl p-0.5 text-xs">
              <button
                type="button"
                onClick={() => setAttendanceWindow(7)}
                className={`px-2.5 py-1 rounded-lg font-semibold ${attendanceWindow === 7 ? 'bg-indigo-600 text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
              >
                7 Days
              </button>
              <button
                type="button"
                onClick={() => setAttendanceWindow(30)}
                className={`px-2.5 py-1 rounded-lg font-semibold ${attendanceWindow === 30 ? 'bg-indigo-600 text-white' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
              >
                30 Days
              </button>
            </div>
          </div>
          <AttendanceChart 
            data={attendanceWindow === 7 ? charts.attendance_trends_7d : charts.attendance_trends_30d} 
            title={`Attendance Trends (${attendanceWindow} Days)`}
            days={attendanceWindow}
          />
        </div>

        {/* Department Distribution */}
        <div className="space-y-2">
          <div className="px-1 text-xs font-bold text-[var(--text-secondary)] uppercase tracking-wider">Staffing Distribution</div>
          <DepartmentChart data={charts.department_distribution} title="Employee Headcount by Department" />
        </div>
      </div>

      {/* Second Analytics Row: Leaves, Tasks, Performance */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <LeaveChart data={charts.leave_distribution} title="Leave Requests Status" />
        <TaskChart data={charts.task_distribution} title="Task Status Overview" />
        <PerformanceChart data={charts.performance_distribution} title="Performance Ratings Distribution" />
      </div>

      {/* Quick Navigation Cards (Module Portals) */}
      <div className="pt-4 border-t border-slate-800">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Module Management Quick Access</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            to="/employees"
            className="p-4 bg-slate-900/90 border border-slate-800 rounded-2xl hover:border-blue-500 hover:shadow-lg transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400">
                <Users className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Employee Directory</h3>
                <p className="text-xs text-slate-400">Onboard & manage</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500 group-hover:translate-x-1 group-hover:text-blue-400 transition-all" />
          </Link>

          <Link
            to="/attendance"
            className="p-4 bg-slate-900/90 border border-slate-800 rounded-2xl hover:border-emerald-500 hover:shadow-lg transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400">
                <Clock className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Attendance & Shifts</h3>
                <p className="text-xs text-slate-400">Live punch & logs</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500 group-hover:translate-x-1 group-hover:text-emerald-400 transition-all" />
          </Link>

          <Link
            to="/tasks"
            className="p-4 bg-slate-900/90 border border-slate-800 rounded-2xl hover:border-indigo-500 hover:shadow-lg transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400">
                <CheckSquare className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Task Workflow</h3>
                <p className="text-xs text-slate-400">Delegate & track</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500 group-hover:translate-x-1 group-hover:text-indigo-400 transition-all" />
          </Link>

          <Link
            to="/performance"
            className="p-4 bg-slate-900/90 border border-slate-800 rounded-2xl hover:border-purple-500 hover:shadow-lg transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400">
                <Award className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">Performance Hub</h3>
                <p className="text-xs text-slate-400">Cycles & appraisals</p>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-slate-500 group-hover:translate-x-1 group-hover:text-purple-400 transition-all" />
          </Link>
        </div>
      </div>
    </div>
  );
}
