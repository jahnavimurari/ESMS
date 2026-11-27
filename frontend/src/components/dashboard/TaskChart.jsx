import React from 'react';
import { CheckSquare } from 'lucide-react';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell 
} from 'recharts';

const TASK_STATUS_COLORS = {
  TODO: '#71717a',
  IN_PROGRESS: '#3b82f6',
  REVIEW: '#f59e0b',
  COMPLETED: '#10b981',
  BLOCKED: '#ef4444',
  CANCELLED: '#a1a1aa'
};

export default function TaskChart({ data = [], title = "Task Status Distribution" }) {
  if (!data || data.length === 0) {
    return (
      <div className="p-6 bg-slate-900/90 border border-slate-800 rounded-2xl flex flex-col items-center justify-center min-h-[280px] text-xs text-slate-400 gap-2">
        <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-500">
          <CheckSquare className="w-5 h-5" />
        </div>
        <span className="font-medium">No task records available.</span>
      </div>
    );
  }

  return (
    <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">{title}</h3>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
            <XAxis dataKey="status" stroke="var(--text-secondary)" fontSize={11} />
            <YAxis stroke="var(--text-secondary)" fontSize={11} allowDecimals={false} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', borderRadius: '0.75rem', fontSize: '12px' }}
              labelStyle={{ color: 'var(--text-primary)', fontWeight: 'bold' }}
            />
            <Bar dataKey="count" name="Tasks" radius={[6, 6, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={TASK_STATUS_COLORS[entry.status] || '#6366f1'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

