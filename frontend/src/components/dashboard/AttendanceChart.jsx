import React from 'react';
import { Calendar } from 'lucide-react';
import { 
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, 
  Tooltip, CartesianGrid, Legend 
} from 'recharts';

export default function AttendanceChart({ data = [], title = "Attendance Trends", days = 7 }) {
  if (!data || data.length === 0) {
    return (
      <div className="p-6 bg-slate-900/90 border border-slate-800 rounded-2xl flex flex-col items-center justify-center min-h-[280px] text-xs text-slate-400 gap-2">
        <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-500">
          <Calendar className="w-5 h-5" />
        </div>
        <span className="font-medium">No attendance records found for this period.</span>
      </div>
    );
  }

  return (
    <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">{title}</h3>
        <span className="text-xs text-[var(--text-secondary)] font-medium">Last {days} days</span>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="colorHours" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" opacity={0.5} />
            <XAxis dataKey="day_name" stroke="var(--text-secondary)" fontSize={11} />
            <YAxis stroke="var(--text-secondary)" fontSize={11} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--surface)', borderColor: 'var(--border)', borderRadius: '0.75rem', fontSize: '12px' }}
              labelStyle={{ color: 'var(--text-primary)', fontWeight: 'bold' }}
            />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
            <Area 
              type="monotone" 
              dataKey="count" 
              name="Attendees" 
              stroke="#6366f1" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorCount)" 
            />
            <Area 
              type="monotone" 
              dataKey="hours" 
              name="Total Hours" 
              stroke="#10b981" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorHours)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

