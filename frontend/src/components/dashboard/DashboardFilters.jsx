import React from 'react';
import { Calendar, Filter } from 'lucide-react';

export default function DashboardFilters({ 
  days, 
  onDaysChange, 
  departments = [], 
  selectedDept, 
  onDeptChange 
}) {
  return (
    <div className="flex flex-wrap items-center gap-3 p-3 bg-[var(--surface)] border border-[var(--border)] rounded-2xl">
      {onDaysChange && (
        <div className="flex items-center gap-1.5 text-xs">
          <Calendar className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-[var(--text-secondary)] font-medium">Window:</span>
          <div className="flex items-center bg-[var(--background)] border border-[var(--border)] rounded-xl p-0.5">
            {[7, 14, 30].map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => onDaysChange(d)}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                  days === d
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>
      )}

      {onDeptChange && departments.length > 0 && (
        <div className="flex items-center gap-1.5 text-xs">
          <Filter className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-[var(--text-secondary)] font-medium">Department:</span>
          <select
            value={selectedDept || ''}
            onChange={(e) => onDeptChange(e.target.value)}
            className="px-2.5 py-1 bg-[var(--background)] border border-[var(--border)] rounded-xl text-xs focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Departments</option>
            {departments.map((dept) => (
              <option key={dept.id} value={dept.id}>
                {dept.name}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}

