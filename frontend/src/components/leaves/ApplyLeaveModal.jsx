import React, { useState, useEffect } from 'react';
import { Calendar, AlertCircle, CheckCircle, FileText } from 'lucide-react';
import { leaveService } from '../../services/leaveService';

export default function ApplyLeaveModal({ isOpen, onClose, onLeaveApplied, leaveTypes = [] }) {
  const [formData, setFormData] = useState({
    leave_type_id: '',
    start_date: '',
    end_date: '',
    reason: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setFormData({
        leave_type_id: leaveTypes[0]?.id || '',
        start_date: '',
        end_date: '',
        reason: ''
      });
      setError(null);
    }
  }, [isOpen, leaveTypes]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!formData.leave_type_id || !formData.start_date || !formData.end_date || !formData.reason) {
      setError('Please fill out all required fields.');
      return;
    }

    if (new Date(formData.end_date) < new Date(formData.start_date)) {
      setError('End date cannot be earlier than start date.');
      return;
    }

    setLoading(true);
    try {
      await leaveService.applyLeave(formData);
      onLeaveApplied();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to submit leave application.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

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
            <Calendar size={22} color="var(--primary)" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Apply for Leave</h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>✕</button>
        </div>

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', padding: '0.75rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.875rem' }}>
            <AlertCircle size={16} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Leave Type *</label>
            <select
              value={formData.leave_type_id}
              onChange={(e) => setFormData({ ...formData, leave_type_id: parseInt(e.target.value) })}
              required
              style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
            >
              {leaveTypes.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.code}) - {t.is_paid ? `${t.days_per_year} days/yr` : 'Unpaid'}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Start Date *</label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                required
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>End Date *</label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                required
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Reason for Leave *</label>
            <textarea
              rows="3"
              required
              placeholder="Please explain the purpose of your leave request..."
              value={formData.reason}
              onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
              style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', resize: 'vertical' }}
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
              {loading ? 'Submitting...' : 'Submit Application'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

