import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, Database, Users, Layers, Lock, 
  Activity, CheckCircle2, AlertTriangle, RefreshCw, ArrowLeft, Shield 
} from 'lucide-react';
import { adminService } from '../../services/adminService';

export default function SystemAdminPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminService.getSystemStats();
      if (res?.success) {
        setStats(res.data);
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to retrieve telemetry.');
    } finally {
      setLoading(false);
    }
  };

  const health = stats?.system_health || stats?.database_health || {};
  const metrics = stats?.metrics || stats?.user_metrics || {};
  const security = stats?.security_telemetry || {};
  const roleDist = stats?.role_distribution || stats?.roles_distribution || metrics.roles_distribution || {};
  const recentActivities = stats?.recent_activity || security.recent_security_events || [];

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
            <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <ShieldAlert size={26} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">System Administration Telemetry</h1>
              <p className="text-xs text-slate-400">
                Real-time infrastructure health, security monitoring, database socket status, and user distribution.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={fetchStats}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-all disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-2.5 text-sm">
          <AlertTriangle size={18} /> {error}
        </div>
      )}

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Users */}
        <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl flex flex-col justify-between shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Registered Users</span>
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400">
              <Users size={18} />
            </div>
          </div>
          <div className="text-2xl font-bold text-white tracking-tight my-1">
            {metrics.total_users ?? 0}
          </div>
          <div className="text-xs text-emerald-400 font-medium">
            {metrics.active_users ?? 0} Active &bull; {metrics.inactive_users ?? 0} Inactive
          </div>
        </div>

        {/* Employee Profiles */}
        <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl flex flex-col justify-between shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Employee Profiles</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <Layers size={18} />
            </div>
          </div>
          <div className="text-2xl font-bold text-white tracking-tight my-1">
            {metrics.total_employees ?? 0}
          </div>
          <div className="text-xs text-slate-400">
            Active Personnel Roster
          </div>
        </div>

        {/* Security Monitoring */}
        <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl flex flex-col justify-between shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Security Monitoring</span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
              <Lock size={18} />
            </div>
          </div>
          <div className="text-2xl font-bold text-white tracking-tight my-1">
            {security.monitored_accounts ?? 0}
          </div>
          <div className={`text-xs font-medium ${security.locked_accounts > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
            {security.locked_accounts ?? 0} Locked &bull; {security.failed_attempts_recorded ?? 0} Failed Attempts
          </div>
        </div>

        {/* Database Health */}
        <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl flex flex-col justify-between shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Database Health</span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <Database size={18} />
            </div>
          </div>
          <div className="flex items-center gap-2 my-1">
            <span className={`w-2.5 h-2.5 rounded-full ${
              health.database_connection === 'connected' ? 'bg-emerald-400 shadow-md shadow-emerald-400/50' : 'bg-rose-400'
            }`} />
            <span className="text-lg font-bold text-white capitalize">
              {health.database_connection || 'Unknown'}
            </span>
          </div>
          <div className="text-xs text-slate-400">
            API: <strong className="text-emerald-400 font-semibold">{health.api_service || 'Operational'}</strong>
          </div>
        </div>
      </div>

      {/* Grid: Role Distribution & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Role Distribution Panel */}
        <div className="p-6 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-xl space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Shield size={18} className="text-blue-400" />
            <span>Security Role Distribution</span>
          </h2>
          <div className="space-y-3 pt-2">
            {Object.entries(roleDist).map(([r, count]) => {
              const pct = metrics.total_users ? Math.round((count / metrics.total_users) * 100) : 0;
              const barColor = r === 'ADMIN' ? 'bg-rose-500' : r === 'HR' ? 'bg-amber-500' : 'bg-blue-500';
              return (
                <div key={r} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-200">{r}</span>
                    <span className="text-slate-400 font-mono">{count} ({pct}%)</span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                    <div className={`h-full rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Activity Log Preview */}
        <div className="p-6 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-xl space-y-4">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Activity size={18} className="text-emerald-400" />
            <span>Recent Administrative Activity</span>
          </h2>
          <div className="space-y-2 pt-2">
            {recentActivities.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">
                No recent activity records.
              </div>
            ) : (
              recentActivities.map((act, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-400" />
                    <span className="font-semibold text-white">{act.action}</span>
                    <span className="text-slate-400 font-mono">({act.target_entity || act.target_entity_type || 'SYSTEM'})</span>
                  </div>
                  <span className="text-slate-500 font-mono text-[11px]">
                    {act.timestamp ? new Date(act.timestamp).toLocaleString() : 'Recent'}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
