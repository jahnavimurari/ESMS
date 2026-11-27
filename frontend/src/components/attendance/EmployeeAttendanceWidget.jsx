import React, { useState, useEffect } from 'react';
import { Clock, Play, Square, CheckCircle, AlertCircle, Calendar, ArrowRight, RefreshCw } from 'lucide-react';
import { attendanceService } from '../../services/attendanceService';

export default function EmployeeAttendanceWidget({ onShiftUpdated }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [notes, setNotes] = useState('');
  const [elapsedTime, setElapsedTime] = useState('00:00:00');

  const loadAttendance = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await attendanceService.getMyAttendance();
      if (res.success) {
        setData(res.data);
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to load shift status.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAttendance();
  }, []);

  // Live timer for active shift
  useEffect(() => {
    if (!data?.today?.active_session?.check_in) {
      setElapsedTime('00:00:00');
      return;
    }

    const checkInTime = new Date(data.today.active_session.check_in).getTime();

    const updateTimer = () => {
      const now = Date.now();
      const diffMs = Math.max(0, now - checkInTime);
      const totalSec = Math.floor(diffMs / 1000);
      const hrs = String(Math.floor(totalSec / 3600)).padStart(2, '0');
      const mins = String(Math.floor((totalSec % 3600) / 60)).padStart(2, '0');
      const secs = String(totalSec % 60).padStart(2, '0');
      setElapsedTime(`${hrs}:${mins}:${secs}`);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [data?.today?.active_session]);

  const handleCheckIn = async () => {
    setActionLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await attendanceService.checkIn(notes);
      setSuccess(`Check-in recorded for Shift ${res.data.shift_number}.`);
      setNotes('');
      loadAttendance();
      if (onShiftUpdated) onShiftUpdated();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Check-in failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCheckOut = async () => {
    setActionLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await attendanceService.checkOut(notes);
      setSuccess(`Check-out recorded for Shift ${res.data.shift_number} (${res.data.total_hours} hrs).`);
      setNotes('');
      loadAttendance();
      if (onShiftUpdated) onShiftUpdated();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Check-out failed.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '2rem', textAlign: 'center' }}>
        <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 0.5rem' }} />
        <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Loading shift workspace...</span>
      </div>
    );
  }

  const hasActiveSession = data?.today?.has_active_session;
  const activeSession = data?.today?.active_session;
  const shifts = data?.today?.shifts || [];
  const todayHours = data?.today?.today_hours || 0.0;

  return (
    <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '1.75rem', boxShadow: 'var(--shadow-sm)' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ backgroundColor: hasActiveSession ? 'rgba(16, 185, 129, 0.15)' : 'rgba(59, 130, 246, 0.15)', padding: '0.625rem', borderRadius: 'var(--radius-md)' }}>
            <Clock size={24} color={hasActiveSession ? 'var(--success)' : 'var(--primary)'} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Shift Attendance Tracker</h2>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              {data?.today?.work_date} • {shifts.length} shift{shifts.length === 1 ? '' : 's'} logged today
            </span>
          </div>
        </div>

        <div style={{ textAlign: 'right' }}>
          <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>Total Hours Today</span>
          <strong style={{ fontSize: '1.25rem', color: 'var(--primary)' }}>{todayHours} hrs</strong>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.875rem' }}>
          <AlertCircle size={16} /> {error}
        </div>
      )}

      {success && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.875rem' }}>
          <CheckCircle size={16} /> {success}
        </div>
      )}

      {/* Active Session Timer Banner */}
      {hasActiveSession ? (
        <div style={{ backgroundColor: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 'var(--radius-md)', padding: '1.25rem', marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '9999px', backgroundColor: 'var(--success)' }} />
              <strong style={{ fontSize: '0.9375rem', color: 'var(--success)' }}>
                Active Shift {activeSession.shift_number} in progress
              </strong>
            </div>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              Checked in at {new Date(activeSession.check_in).toLocaleTimeString()}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{ fontFamily: 'monospace', fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              {elapsedTime}
            </div>

            <button
              onClick={handleCheckOut}
              disabled={actionLoading}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.625rem 1.25rem', backgroundColor: 'var(--danger)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: '0.875rem', cursor: 'pointer' }}
            >
              <Square size={16} /> {actionLoading ? 'Recording...' : 'End Shift (Check Out)'}
            </button>
          </div>
        </div>
      ) : (
        <div style={{ backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1.25rem', marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <strong style={{ display: 'block', fontSize: '0.9375rem', color: 'var(--text-primary)' }}>
              Ready to work?
            </strong>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              Next shift will be recorded as Shift {(shifts.length || 0) + 1}.
            </span>
          </div>

          <button
            onClick={handleCheckIn}
            disabled={actionLoading}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.625rem 1.5rem', backgroundColor: 'var(--primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: '0.875rem', cursor: 'pointer' }}
          >
            <Play size={16} /> {actionLoading ? 'Starting...' : 'Start Shift (Check In)'}
          </button>
        </div>
      )}

      {/* Completed Shifts Table for Today */}
      {shifts.length > 0 && (
        <div>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.75rem', textTransform: 'uppercase' }}>
            Today's Completed Shift Log
          </h3>
          <div style={{ border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8125rem' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-app)', borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                  <th style={{ padding: '0.625rem 1rem' }}>Shift #</th>
                  <th style={{ padding: '0.625rem 1rem' }}>Check In</th>
                  <th style={{ padding: '0.625rem 1rem' }}>Check Out</th>
                  <th style={{ padding: '0.625rem 1rem' }}>Duration</th>
                  <th style={{ padding: '0.625rem 1rem' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {shifts.map((s) => (
                  <tr key={s.id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '0.625rem 1rem', fontWeight: 600 }}>Shift {s.shift_number}</td>
                    <td style={{ padding: '0.625rem 1rem' }}>{s.check_in ? new Date(s.check_in).toLocaleTimeString() : '-'}</td>
                    <td style={{ padding: '0.625rem 1rem' }}>{s.check_out ? new Date(s.check_out).toLocaleTimeString() : <span style={{ color: 'var(--success)' }}>Active</span>}</td>
                    <td style={{ padding: '0.625rem 1rem', fontWeight: 600 }}>{s.total_hours} hrs</td>
                    <td style={{ padding: '0.625rem 1rem' }}>
                      <span style={{
                        padding: '0.125rem 0.5rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600,
                        backgroundColor: s.status === 'PRESENT' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.12)',
                        color: s.status === 'PRESENT' ? 'var(--success)' : 'var(--warning)'
                      }}>
                        {s.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

