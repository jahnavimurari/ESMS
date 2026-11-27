import React from 'react';
import { Award } from 'lucide-react';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell 
} from 'recharts';

const RATING_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#3b82f6', '#10b981'];

export default function PerformanceChart({ data = [], title = "Performance Rating Distribution (Completed)" }) {
  if (!data || data.length === 0) {
    return (
      <div className="p-6 bg-slate-900/90 border border-slate-800 rounded-2xl flex flex-col items-center justify-center min-h-[280px] text-xs text-slate-400 gap-2">
        <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-500">
          <Award className="w-5 h-5" />
        </div>
        <span className="font-medium">No completed performance appraisals recorded.</span>
      </div>
    );
  }

  return (
    <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">{title}</h3>
        <span className="text-xs text-[var(--text-secondary)] font-medium">Scale 1 to 5</span>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
            <XAxis dataKey="score" stroke="var(--text-secondary)" fontSize={11} tickFormatter={(val) => `★ ${val}`} />
            <YAxis stroke="var(--text-secondary)" fontSize={11} allowDecimals={false} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', borderRadius: '0.75rem', fontSize: '12px' }}
              labelStyle={{ color: 'var(--text-primary)', fontWeight: 'bold' }}
              formatter={(val, name, props) => [`${val} reviews`, props.payload.label]}
            />
            <Bar dataKey="count" name="Reviews" radius={[6, 6, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={RATING_COLORS[(entry.score - 1) % RATING_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

