import React from 'react';

export default function DashboardStatCard({ 
  title, 
  value, 
  subtext, 
  icon: Icon, 
  color = '#3b82f6', 
  bgLight = 'rgba(59, 130, 246, 0.1)',
  badge,
  loading = false
}) {
  if (loading) {
    return (
      <div className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl animate-pulse">
        <div className="h-4 bg-slate-800 rounded w-24 mb-3"></div>
        <div className="h-8 bg-slate-800 rounded w-16 mb-2"></div>
        <div className="h-3 bg-slate-800 rounded w-32"></div>
      </div>
    );
  }

  return (
    <div className="p-5 bg-slate-900/90 border border-slate-800 hover:border-slate-700 rounded-2xl flex flex-col justify-between shadow-lg shadow-black/20 hover:shadow-xl transition-all">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
        {Icon && (
          <div style={{ backgroundColor: bgLight, color: color }} className="p-2 rounded-xl">
            <Icon size={18} />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2 mt-1">
        <div className="text-2xl font-bold text-white tracking-tight">{value ?? 0}</div>
        {badge && (
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {badge}
          </span>
        )}
      </div>

      {subtext && (
        <span className="text-xs text-slate-400 mt-2 block">{subtext}</span>
      )}
    </div>
  );
}

