import React, { useState, useEffect } from 'react';
import { 
  Calendar, Users, Clock, Filter, Search, CheckCircle, 
  AlertCircle, Edit2, RefreshCw, BarChart2, Shield 
} from 'lucide-react';
import { attendanceService } from '../../services/attendanceService';
import { employeeService } from '../../services/employeeService';
import { useAuth } from '../../context/AuthContext';
import AttendanceCorrectionModal from '../../components/attendance/AttendanceCorrectionModal';
import EmployeeAttendanceWidget from '../../components/attendance/EmployeeAttendanceWidget';

export default function AttendanceManagementPage() {
  const { role } = useAuth();
  const isHRorAdmin = role === 'ADMIN' || role === 'HR';

  const [records, setRecords] = useState([]);
  const [summary, setSummary] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

  // Correction Modal
  const [correctionRecord, setCorrectionRecord] = useState(null);
  const [isCorrectionModalOpen, setIsCorrectionModalOpen] = useState(false);

  const loadDepartments = async () => {
    try {
      const res = await employeeService.getDepartments(false);
      if (res.success) setDepartments(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadSummary = async () => {
    try {
      const res = await attendanceService.getSummary(selectedDate, selectedDept);
      if (res.success) setSummary(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadAttendance = async () => {
    setLoading(true);
    setError(null);
    try {
      if (isHRorAdmin) {
        const params = {
          search,
          department_id: selectedDept,
          status: selectedStatus,
          work_date: selectedDate
        };
        const res = await attendanceService.getAttendanceList(params);
        if (res.success) {
          setRecords(res.data.items || []);
          setTotalCount(res.data.total || 0);
        }
      } else {
        // Employee view
        const res = await attendanceService.getMyAttendance();
        if (res.success) {
          setRecords(res.data.items || []);
          setTotalCount(res.data.total || 0);
        }
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to load attendance logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDepartments();
  }, []);

  useEffect(() => {
    if (isHRorAdmin) loadSummary();
    const t = setTimeout(() => {
      loadAttendance();
    }, 250);
    return () => clearTimeout(t);
  }, [search, selectedDept, selectedStatus, selectedDate, isHRorAdmin]);

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      {/* Top Title */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Clock size={28} color="var(--primary)" /> Attendance Management & Multi-Shift Tracking
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
          Enterprise attendance recording, multi-shift tracking, and real-time operational status.
        </p>
      </div>

      {/* Employee Personal Shift Widget (Shown for all roles) */}
      <div style={{ marginBottom: '2rem' }}>
        <EmployeeAttendanceWidget onShiftUpdated={() => { loadAttendance(); if (isHRorAdmin) loadSummary(); }} />
      </div>

      {/* HR/Admin Summary Cards */}
      {isHRorAdmin && summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Present Employees</span>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--success)', marginTop: '0.25rem' }}>
              {summary.present_count} / {summary.total_employees}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Attendance Rate: {summary.attendance_rate}%</span>
          </div>

          <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Active Shifts Now</span>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary)', marginTop: '0.25rem' }}>
              {summary.active_shifts_now}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Currently clocked in</span>
          </div>

          <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Late Arrivals</span>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--warning)', marginTop: '0.25rem' }}>
              {summary.late_count}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Past shift threshold</span>
          </div>

          <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Hours Logged</span>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: '0.25rem' }}>
              {summary.total_hours_logged} hrs
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Across all shifts today</span>
          </div>
        </div>
      )}

      {/* Filter Bar (HR & Admin) */}
      {isHRorAdmin && (
        <div style={{
          display: 'flex', gap: '1rem', backgroundColor: 'var(--bg-surface)',
          padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)',
          marginBottom: '1.5rem', flexWrap: 'wrap'
        }}>
          <div style={{ flex: '1 1 200px', position: 'relative' }}>
            <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search by name, employee code..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: '100%', padding: '0.5rem 0.75rem 0.5rem 2.5rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: '0.875rem' }}
            />
          </div>

          <div style={{ flex: '0 0 160px' }}>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: '0.875rem' }}
            />
          </div>

          <div style={{ flex: '0 0 180px' }}>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: '0.875rem' }}
            >
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          <div style={{ flex: '0 0 140px' }}>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: '0.875rem' }}
            >
              <option value="">All Statuses</option>
              <option value="PRESENT">Present</option>
              <option value="LATE">Late</option>
              <option value="HALF_DAY">Half Day</option>
              <option value="ABSENT">Absent</option>
            </select>
          </div>
        </div>
      )}

      {/* Attendance Log Table */}
      <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', boxShadow: 'var(--shadow-sm)' }}>
        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 600 }}>
            {isHRorAdmin ? `Attendance Log (${totalCount} records)` : 'My Attendance History'}
          </h2>
        </div>

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 0.75rem' }} />
            Loading attendance records...
          </div>
        ) : records.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <Clock size={36} color="var(--text-muted)" style={{ margin: '0 auto 0.75rem' }} />
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>No attendance records found</h3>
            <p style={{ fontSize: '0.875rem', marginTop: '0.25rem' }}>Records will appear once employees log check-in shifts.</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-app)', borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                <th style={{ padding: '0.75rem 1.25rem' }}>Employee</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Date & Shift</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Check In</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Check Out</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Hours</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Status</th>
                {isHRorAdmin && <th style={{ padding: '0.75rem 1.25rem', textAlign: 'right' }}>Correction</th>}
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '0.875rem 1.25rem' }}>
                    <strong style={{ display: 'block', color: 'var(--text-primary)' }}>{r.employee_name || 'My Record'}</strong>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      {r.employee_code} {r.department_name && `• ${r.department_name}`}
                    </span>
                  </td>
                  <td style={{ padding: '0.875rem 1.25rem' }}>
                    <span style={{ fontWeight: 500 }}>{r.work_date}</span>
                    <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Shift #{r.shift_number}</span>
                  </td>
                  <td style={{ padding: '0.875rem 1.25rem' }}>
                    {r.check_in ? new Date(r.check_in).toLocaleTimeString() : '-'}
                  </td>
                  <td style={{ padding: '0.875rem 1.25rem' }}>
                    {r.check_out ? new Date(r.check_out).toLocaleTimeString() : <span style={{ color: 'var(--success)', fontWeight: 600 }}>Active</span>}
                  </td>
                  <td style={{ padding: '0.875rem 1.25rem', fontWeight: 600 }}>
                    {r.total_hours} hrs
                  </td>
                  <td style={{ padding: '0.875rem 1.25rem' }}>
                    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem' }}>
                      <span style={{
                        padding: '0.25rem 0.625rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600,
                        backgroundColor: r.status === 'PRESENT' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.12)',
                        color: r.status === 'PRESENT' ? 'var(--success)' : 'var(--warning)'
                      }}>
                        {r.status}
                      </span>
                      {r.is_corrected && (
                        <span title="Record was corrected by HR/Admin" style={{ fontSize: '0.6875rem', color: 'var(--primary)', fontWeight: 600 }}>
                          (Edited)
                        </span>
                      )}
                    </div>
                  </td>
                  {isHRorAdmin && (
                    <td style={{ padding: '0.875rem 1.25rem', textAlign: 'right' }}>
                      <button
                        onClick={() => { setCorrectionRecord(r); setIsCorrectionModalOpen(true); }}
                        title="Authorize Correction"
                        style={{ padding: '0.375rem 0.625rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                      >
                        <Edit2 size={13} /> Edit
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <AttendanceCorrectionModal
        isOpen={isCorrectionModalOpen}
        onClose={() => setIsCorrectionModalOpen(false)}
        attendanceRecord={correctionRecord}
        onCorrected={() => {
          loadAttendance();
          if (isHRorAdmin) loadSummary();
        }}
      />
    </div>
  );
}

