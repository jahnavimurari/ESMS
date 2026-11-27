import React, { useState } from 'react';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { leaveService } from '../../services/leaveService';

export default function ReviewLeaveModal({ isOpen, onClose, leaveRequest, onReviewed }) {
  const [comments, setComments] = useState('');
  const [actionType, setActionType] = useState('APPROVE');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !leaveRequest) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (actionType === 'APPROVE') {
        await leaveService.approveLeave(leaveRequest.id, comments);
      } else {
        await leaveService.rejectLeave(leaveRequest.id, comments);
      }
      onReviewed();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to process leave decision.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: '1.5rem'
    }}>
      <div style={{
        backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)',
        width: '100%', maxWidth: '500px', padding: '2rem', boxShadow: 'var(--shadow-xl)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Review Leave Application</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>✕</button>
        </div>

        <div style={{ backgroundColor: 'var(--bg-app)', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
          <div><strong>Applicant:</strong> {leaveRequest.employee_name} ({leaveRequest.employee_code})</div>
          <div><strong>Leave Type:</strong> {leaveRequest.leave_type_name}</div>
          <div><strong>Duration:</strong> {leaveRequest.start_date} to {leaveRequest.end_date} ({leaveRequest.total_days} days)</div>
          <div style={{ marginTop: '0.5rem', color: 'var(--text-secondary)' }}><strong>Reason:</strong> {leaveRequest.reason}</div>
        </div>

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', padding: '0.75rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.875rem' }}>
            <AlertCircle size={16} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Decision</label>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', cursor: 'pointer', fontSize: '0.875rem' }}>
                <input
                  type="radio"
                  name="decision"
                  checked={actionType === 'APPROVE'}
                  onChange={() => setActionType('APPROVE')}
                />
                <span style={{ color: 'var(--success)', fontWeight: 600 }}>Approve</span>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', cursor: 'pointer', fontSize: '0.875rem' }}>
                <input
                  type="radio"
                  name="decision"
                  checked={actionType === 'REJECT'}
                  onChange={() => setActionType('REJECT')}
                />
                <span style={{ color: 'var(--danger)', fontWeight: 600 }}>Reject</span>
              </label>
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>
              Reviewer Comments {actionType === 'REJECT' && '(Required for rejection)'}
            </label>
            <input
              type="text"
              required={actionType === 'REJECT'}
              placeholder={actionType === 'APPROVE' ? 'Optional remarks...' : 'Provide reason for rejection...'}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
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
              style={{
                padding: '0.5rem 1.25rem',
                backgroundColor: actionType === 'APPROVE' ? 'var(--success)' : 'var(--danger)',
                color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontWeight: 600, cursor: 'pointer'
              }}
            >
              {loading ? 'Processing...' : actionType === 'APPROVE' ? 'Approve Request' : 'Reject Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

