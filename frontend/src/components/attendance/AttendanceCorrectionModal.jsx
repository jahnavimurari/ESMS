import React, { useState, useEffect } from 'react';
import { Edit2, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { attendanceService } from '../../services/attendanceService';

export default function AttendanceCorrectionModal({ isOpen, onClose, attendanceRecord, onCorrected }) {
  const [formData, setFormData] = useState({
    status: 'PRESENT',
    total_hours: 0.0,
    notes: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && attendanceRecord) {
      setFormData({
        status: attendanceRecord.status || 'PRESENT',
        total_hours: attendanceRecord.total_hours || 0.0,
        notes: ''
      });
      setError(null);
    }
  }, [isOpen, attendanceRecord]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!attendanceRecord) return;

    setLoading(true);
    setError(null);
    try {
      await attendanceService.correctAttendance(attendanceRecord.id, formData);
      onCorrected();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to apply attendance correction.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !attendanceRecord) return null;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: '1.5rem'
    }}>
      <div style={{
        backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)',
        width: '100%', maxWidth: '520px', padding: '2rem', boxShadow: 'var(--shadow-xl)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Clock size={22} color="var(--primary)" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Attendance Record Correction</h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>✕</button>
        </div>

        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
          Correcting record for <strong>{attendanceRecord.employee_name}</strong> ({attendanceRecord.work_date}, Shift {attendanceRecord.shift_number}). This action will be recorded in the audit trail.
        </p>

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', padding: '0.75rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.875rem' }}>
            <AlertCircle size={16} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Attendance Status</label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
            >
              <option value="PRESENT">Present</option>
              <option value="LATE">Late Arrival</option>
              <option value="HALF_DAY">Half Day</option>
              <option value="ABSENT">Absent</option>
            </select>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Approved Worked Hours (0 - 24)</label>
            <input
              type="number"
              step="0.25"
              min="0"
              max="24"
              value={formData.total_hours}
              onChange={(e) => setFormData({ ...formData, total_hours: parseFloat(e.target.value) || 0 })}
              style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Audit Reason / Notes *</label>
            <input
              type="text"
              required
              placeholder="e.g. Approved overtime or forgotten checkout"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button
              type="button"
              onClick={onClose}
              style={{ padding: '0.5rem 1rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{ padding: '0.5rem 1.25rem', backgroundColor: 'var(--primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontWeight: 600, cursor: 'pointer' }}
            >
              {loading ? 'Saving...' : 'Apply Correction'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

