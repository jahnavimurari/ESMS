import React, { useState, useEffect } from 'react';
import { 
  FileText, Download, Filter, RefreshCw, Calendar, 
  Users, Clock, CheckSquare, Award, AlertTriangle, ArrowLeft
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { reportsService } from '../../services/reportsService';
import { employeeService } from '../../services/employeeService';
import { performanceService } from '../../services/performanceService';

const REPORT_CATEGORIES = [
  { id: 'employees', label: 'Employee Directory', icon: Users, roles: ['ADMIN', 'HR'] },
  { id: 'attendance', label: 'Attendance & Shifts', icon: Clock, roles: ['ADMIN', 'HR', 'EMPLOYEE'] },
  { id: 'leaves', label: 'Leave Requests', icon: Calendar, roles: ['ADMIN', 'HR', 'EMPLOYEE'] },
  { id: 'tasks', label: 'Tasks & Progress', icon: CheckSquare, roles: ['ADMIN', 'HR', 'EMPLOYEE'] },
  { id: 'performance', label: 'Performance Reviews', icon: Award, roles: ['ADMIN', 'HR', 'EMPLOYEE'] }
];

export default function ReportsPage() {
  const { user } = useAuth();
  const userRole = user?.role || 'EMPLOYEE';

  // Filter allowed categories for role
  const availableCategories = REPORT_CATEGORIES.filter(c => c.roles.includes(userRole));
  const [selectedCategory, setSelectedCategory] = useState(availableCategories[0]?.id || 'attendance');

  // Filter parameters state
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [status, setStatus] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [priority, setPriority] = useState('');
  const [cycleId, setCycleId] = useState('');

  // Dropdown options
  const [departments, setDepartments] = useState([]);
  const [cycles, setCycles] = useState([]);

  // Report data state
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  useEffect(() => {
    // Load departments for Admin/HR
    if (['ADMIN', 'HR'].includes(userRole)) {
      employeeService.getDepartments(false)
        .then(res => {
          const deptList = Array.isArray(res?.data) ? res.data : (res?.data?.items || []);
          setDepartments(deptList);
        })
        .catch(() => setDepartments([]));
    }
    // Load performance cycles
    performanceService.getCycles({ per_page: 100 })
      .then(res => {
        const cycleList = Array.isArray(res?.data) ? res.data : (res?.data?.items || []);
        setCycles(cycleList);
      })
      .catch(() => setCycles([]));
  }, [userRole]);

  useEffect(() => {
    // Reset filters when switching category
    setStatus('');
    setPriority('');
    setDepartmentId('');
    setCycleId('');
    setCurrentPage(1);
    fetchReport();
  }, [selectedCategory]);

  const fetchReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (status) params.status = status;
      if (departmentId) params.department_id = departmentId;
      if (priority) params.priority = priority;
      if (cycleId) params.cycle_id = cycleId;

      let res;
      switch (selectedCategory) {
        case 'employees':
          res = await reportsService.getEmployeeReport(params);
          break;
        case 'attendance':
          res = await reportsService.getAttendanceReport(params);
          break;
        case 'leaves':
          res = await reportsService.getLeaveReport(params);
          break;
        case 'tasks':
          res = await reportsService.getTaskReport(params);
          break;
        case 'performance':
          res = await reportsService.getPerformanceReport(params);
          break;
        default:
          throw new Error('Invalid report category.');
      }

      if (res?.success) {
        setReportData(res.data);
        setCurrentPage(1);
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || err?.message || 'Failed to load report data.');
      setReportData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    setExporting(true);
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (status) params.status = status;
      if (departmentId) params.department_id = departmentId;
      if (priority) params.priority = priority;
      if (cycleId) params.cycle_id = cycleId;

      let res;
      switch (selectedCategory) {
        case 'employees':
          res = await reportsService.exportEmployeeReport(params, format);
          break;
        case 'attendance':
          res = await reportsService.exportAttendanceReport(params, format);
          break;
        case 'leaves':
          res = await reportsService.exportLeaveReport(params, format);
          break;
        case 'tasks':
          res = await reportsService.exportTaskReport(params, format);
          break;
        case 'performance':
          res = await reportsService.exportPerformanceReport(params, format);
          break;
        default:
          return;
      }

      // Download file blob
      const blob = new Blob([res.data], { type: res.headers['content-type'] });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${selectedCategory}_report_${Date.now()}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err?.response?.data?.error?.message || 'Failed to export report file.');
    } finally {
      setExporting(false);
    }
  };

  const headers = reportData?.headers || [];
  const rows = reportData?.rows || [];
  const totalRecords = rows.length;
  const paginatedRows = rows.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const totalPages = Math.ceil(totalRecords / pageSize) || 1;

  const dashboardUrl = userRole === 'ADMIN' ? '/dashboard/admin' : userRole === 'HR' ? '/dashboard/hr' : '/dashboard/employee';

  return (
    <div style={{ padding: '2rem', maxWidth: '1440px', margin: '0 auto', width: '100%' }} className="space-y-6">
      {/* Top Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingBottom: '1.25rem',
        borderBottom: '1px solid var(--border)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ backgroundColor: 'rgba(59, 130, 246, 0.15)', padding: '0.625rem', borderRadius: 'var(--radius-md)' }}>
            <FileText size={26} color="var(--primary)" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Reports & Export Center</h1>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              Operational audits, multi-shift attendance logs, tasks, leaves, and appraisal exports
            </span>
          </div>
        </div>

        <a
          href={dashboardUrl}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 1rem',
            backgroundColor: 'var(--bg-surface-hover)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--text-primary)',
            fontSize: '0.875rem',
            textDecoration: 'none'
          }}
        >
          <ArrowLeft size={16} /> Back to Dashboard
        </a>
      </div>

      {/* Category Tab Bar */}
      <div className="flex flex-wrap gap-2 border-b border-[var(--border)] pb-3">
        {availableCategories.map(cat => {
          const Icon = cat.icon;
          const isActive = selectedCategory === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all ${
                isActive 
                  ? 'bg-blue-600 text-white shadow-md' 
                  : 'bg-[var(--surface)] text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] border border-[var(--border)]'
              }`}
            >
              <Icon size={16} />
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* Filters Form Card */}
      <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)]">
            <Filter size={16} className="text-blue-500" />
            <span>Filter Criteria</span>
          </div>
          <button
            onClick={fetchReport}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Generating...' : 'Generate Report'}
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 text-xs">
          {/* Date range filters */}
          <div>
            <label className="block text-[var(--text-secondary)] mb-1 font-medium">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-[var(--text-secondary)] mb-1 font-medium">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Department filter (Admin/HR only) */}
          {['ADMIN', 'HR'].includes(userRole) && departments.length > 0 && (
            <div>
              <label className="block text-[var(--text-secondary)] mb-1 font-medium">Department</label>
              <select
                value={departmentId}
                onChange={(e) => setDepartmentId(e.target.value)}
                className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
              >
                <option value="">All Departments</option>
                {(Array.isArray(departments) ? departments : []).map(d => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Category-specific status dropdown */}
          {selectedCategory === 'employees' && (
            <div>
              <label className="block text-[var(--text-secondary)] mb-1 font-medium">Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="ON_LEAVE">ON_LEAVE</option>
                <option value="TERMINATED">TERMINATED</option>
                <option value="SUSPENDED">SUSPENDED</option>
              </select>
            </div>
          )}

          {selectedCategory === 'attendance' && (
            <div>
              <label className="block text-[var(--text-secondary)] mb-1 font-medium">Attendance Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="PRESENT">PRESENT</option>
                <option value="LATE">LATE</option>
                <option value="HALF_DAY">HALF_DAY</option>
                <option value="ABSENT">ABSENT</option>
              </select>
            </div>
          )}

          {selectedCategory === 'leaves' && (
            <div>
              <label className="block text-[var(--text-secondary)] mb-1 font-medium">Leave Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="PENDING">PENDING</option>
                <option value="APPROVED">APPROVED</option>
                <option value="REJECTED">REJECTED</option>
                <option value="CANCELLED">CANCELLED</option>
              </select>
            </div>
          )}

          {selectedCategory === 'tasks' && (
            <>
              <div>
                <label className="block text-[var(--text-secondary)] mb-1 font-medium">Task Status</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                >
                  <option value="">All Statuses</option>
                  <option value="TODO">TODO</option>
                  <option value="IN_PROGRESS">IN_PROGRESS</option>
                  <option value="REVIEW">REVIEW</option>
                  <option value="COMPLETED">COMPLETED</option>
                  <option value="OVERDUE">OVERDUE (Delayed)</option>
                  <option value="BLOCKED">BLOCKED</option>
                  <option value="CANCELLED">CANCELLED</option>
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] mb-1 font-medium">Priority</label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                >
                  <option value="">All Priorities</option>
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                  <option value="URGENT">URGENT</option>
                </select>
              </div>
            </>
          )}

          {selectedCategory === 'performance' && (
            <>
              <div>
                <label className="block text-[var(--text-secondary)] mb-1 font-medium">Review Cycle</label>
                <select
                  value={cycleId}
                  onChange={(e) => setCycleId(e.target.value)}
                  className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                >
                  <option value="">All Cycles</option>
                  {(Array.isArray(cycles) ? cycles : []).map(c => (
                    <option key={c.id} value={c.id}>{c.title}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[var(--text-secondary)] mb-1 font-medium">Review Status</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-xl text-[var(--text-primary)] focus:outline-none focus:border-blue-500"
                >
                  <option value="">All Statuses</option>
                  <option value="COMPLETED">COMPLETED Only</option>
                  <option value="MANAGER_REVIEW">MANAGER_REVIEW</option>
                  <option value="SELF_ASSESSMENT">SELF_ASSESSMENT</option>
                  <option value="DRAFT">DRAFT</option>
                </select>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center gap-3 text-sm text-red-500">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
          <button onClick={fetchReport} className="ml-auto underline font-medium">Retry</button>
        </div>
      )}

      {/* Report Preview & Export Actions */}
      <div className="p-5 bg-[var(--surface)] border border-[var(--border)] rounded-2xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-[var(--text-primary)]">
              {reportData?.title || 'Report Preview'}
            </h2>
            <span className="text-xs text-[var(--text-secondary)]">
              Showing {totalRecords} records {reportData?.total_working_hours ? `• Total Working Hours: ${reportData.total_working_hours}h` : ''} {reportData?.average_completed_rating ? `• Avg Completed Rating: ★ ${reportData.average_completed_rating}` : ''}
            </span>
          </div>

          {/* Export Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleExport('csv')}
              disabled={exporting || totalRecords === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
            >
              <Download size={13} />
              CSV
            </button>
            <button
              onClick={() => handleExport('xlsx')}
              disabled={exporting || totalRecords === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
            >
              <Download size={13} />
              Excel (.xlsx)
            </button>
            <button
              onClick={() => handleExport('pdf')}
              disabled={exporting || totalRecords === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
            >
              <Download size={13} />
              PDF
            </button>
          </div>
        </div>

        {/* Tabular Data Preview */}
        {loading ? (
          <div className="p-12 flex flex-col items-center justify-center text-sm text-[var(--text-secondary)] gap-2">
            <RefreshCw size={24} className="animate-spin text-blue-500" />
            <span>Compiling report records...</span>
          </div>
        ) : totalRecords === 0 ? (
          <div className="p-12 border border-dashed border-[var(--border)] rounded-2xl flex flex-col items-center justify-center text-xs text-[var(--text-secondary)]">
            No records found matching the specified filter criteria.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-[var(--border)]">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-[var(--surface-hover)] border-b border-[var(--border)] text-[var(--text-secondary)] font-semibold">
                  {headers.map((h, i) => (
                    <th key={i} className="p-3 whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {paginatedRows.map((row, rIdx) => (
                  <tr key={rIdx} className="hover:bg-[var(--surface-hover)] transition-colors">
                    {row.map((cell, cIdx) => (
                      <td key={cIdx} className="p-3 whitespace-nowrap text-[var(--text-primary)]">
                        {cell === null || cell === undefined || cell === '' ? '-' : String(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination controls */}
        {totalRecords > pageSize && (
          <div className="flex items-center justify-between text-xs text-[var(--text-secondary)] pt-2">
            <span>
              Page {currentPage} of {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 bg-[var(--background)] border border-[var(--border)] rounded-lg disabled:opacity-40"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 bg-[var(--background)] border border-[var(--border)] rounded-lg disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

