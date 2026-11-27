import React, { useState, useEffect } from 'react';
import { 
  Calendar, CheckCircle2, XCircle, Clock, Plus, Filter, 
  Search, AlertCircle, RefreshCw, X 
} from 'lucide-react';
import { leaveService } from '../../services/leaveService';
import { employeeService } from '../../services/employeeService';
import { useAuth } from '../../context/AuthContext';
import ApplyLeaveModal from '../../components/leaves/ApplyLeaveModal';
import ReviewLeaveModal from '../../components/leaves/ReviewLeaveModal';

export default function LeaveManagementPage() {
  const { role } = useAuth();
  const isHRorAdmin = role === 'ADMIN' || role === 'HR';

  const [leaves, setLeaves] = useState([]);
  const [balances, setBalances] = useState([]);
  const [summary, setSummary] = useState(null);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');

  // Modals
  const [isApplyModalOpen, setIsApplyModalOpen] = useState(false);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [selectedLeave, setSelectedLeave] = useState(null);

  const loadMetadata = async () => {
    try {
      const [typeRes, deptRes] = await Promise.all([
        leaveService.getLeaveTypes(),
        employeeService.getDepartments(false)
      ]);
      if (typeRes.success) setLeaveTypes(typeRes.data);
      if (deptRes.success) setDepartments(deptRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadSummary = async () => {
    if (!isHRorAdmin) return;
    try {
      const res = await leaveService.getLeaveSummary();
      if (res.success) setSummary(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadLeaves = async () => {
    setLoading(true);
    setError(null);
    try {
      if (isHRorAdmin) {
        const params = {
          search,
          department_id: selectedDept,
          leave_type_id: selectedType,
          status: selectedStatus
        };
        const res = await leaveService.getLeavesList(params);
        if (res.success) {
          setLeaves(res.data.items || []);
          setTotalCount(res.data.total || 0);
        }
      } else {
        const res = await leaveService.getMyLeaves({ status: selectedStatus });
        if (res.success) {
          setLeaves(res.data.items || []);
          setBalances(res.data.balances || []);
          setTotalCount(res.data.total || 0);
        }
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to load leave records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMetadata();
  }, []);

  useEffect(() => {
    loadSummary();
    const t = setTimeout(() => {
      loadLeaves();
    }, 250);
    return () => clearTimeout(t);
  }, [search, selectedDept, selectedType, selectedStatus, isHRorAdmin]);

  const handleCancel = async (leaveId) => {
    if (!window.confirm('Are you sure you want to cancel this leave request?')) return;
    try {
      await leaveService.cancelLeave(leaveId);
      setSuccess('Leave request cancelled successfully.');
      loadLeaves();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to cancel leave request.');
    }
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      {/* Title & Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Calendar size={28} color="var(--primary)" /> Leave Management & Approvals
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Automated balance accounting, conflict-free scheduling, and approval workflows.
          </p>
        </div>

        <button
          onClick={() => setIsApplyModalOpen(true)}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.625rem 1.25rem', backgroundColor: 'var(--primary)',
            color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: '0.875rem', cursor: 'pointer'
          }}
        >
          <Plus size={16} /> Apply for Leave
        </button>
      </div>

      {/* Alerts */}
      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'rgba(239, 68, 68, 0.12)', color: 'var(--danger)', padding: '0.875rem 1.25rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {success && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'rgba(16, 185, 129, 0.12)', color: 'var(--success)', padding: '0.875rem 1.25rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
          <CheckCircle2 size={18} /> {success}
        </div>
      )}

      {/* Employee Leave Balance Cards (Shown for all users) */}
      {!isHRorAdmin && balances.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem' }}>My Annual Leave Balances</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            {balances.map((b) => (
              <div key={b.leave_type_id} style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{b.leave_type_name} ({b.leave_type_code})</span>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary)', marginTop: '0.25rem' }}>
                  {b.is_paid ? `${b.remaining_balance} days` : 'Unlimited'}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.375rem', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Approved: {b.approved_days}d</span>
                  <span>Pending: {b.pending_days}d</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* HR/Admin Summary KPI Cards */}
      {isHRorAdmin && summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Pending Approvals</span>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--warning)', marginTop: '0.25rem' }}>
              {summary.pending_approvals}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Awaiting decision</span>
          </div>

          <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>On Leave Today</span>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--primary)', marginTop: '0.25rem' }}>
              {summary.employees_on_leave_today}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Active approved leaves</span>
          </div>

          <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Approved ({summary.year})</span>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--success)', marginTop: '0.25rem' }}>
              {summary.approved_this_year}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Cumulative this year</span>
          </div>

          <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Rejected ({summary.year})</span>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--danger)', marginTop: '0.25rem' }}>
              {summary.rejected_this_year}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Declined requests</span>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div style={{
        display: 'flex', gap: '1rem', backgroundColor: 'var(--bg-surface)',
        padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)',
        marginBottom: '1.5rem', flexWrap: 'wrap'
      }}>
        {isHRorAdmin && (
          <div style={{ flex: '1 1 200px', position: 'relative' }}>
            <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search by employee name or code..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: '100%', padding: '0.5rem 0.75rem 0.5rem 2.5rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: '0.875rem' }}
            />
          </div>
        )}

        <div style={{ flex: '0 0 160px' }}>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: '0.875rem' }}
          >
            <option value="">All Leave Types</option>
            {leaveTypes.map((t) => (
              <option key={t.id} value={t.id}>{t.name} ({t.code})</option>
            ))}
          </select>
        </div>

        <div style={{ flex: '0 0 150px' }}>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: '0.875rem' }}
          >
            <option value="">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Leave Requests Table */}
      <div style={{ backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', boxShadow: 'var(--shadow-sm)' }}>
        <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border)' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 600 }}>
            {isHRorAdmin ? `Company Leave Applications (${totalCount})` : 'My Submitted Requests'}
          </h2>
        </div>

        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 0.75rem' }} />
            Loading leave requests...
          </div>
        ) : leaves.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <Calendar size={36} color="var(--text-muted)" style={{ margin: '0 auto 0.75rem' }} />
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>No leave applications found</h3>
            <p style={{ fontSize: '0.875rem', marginTop: '0.25rem' }}>No records match the selected filters.</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ backgroundColor: 'var(--bg-app)', borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                <th style={{ padding: '0.75rem 1.25rem' }}>Employee</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Type</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Dates</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Days</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Status</th>
                <th style={{ padding: '0.75rem 1.25rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {leaves.map((l) => (
                <tr key={l.id} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '0.875rem 1.25rem' }}>
                    <strong style={{ display: 'block', color: 'var(--text-primary)' }}>{l.employee_name || 'My Request'}</strong>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{l.employee_code}</span>
                  </td>
                  <td style={{ padding: '0.875rem 1.25rem' }}>
                    <span style={{ backgroundColor: 'var(--bg-app)', padding: '0.25rem 0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', fontSize: '0.8125rem' }}>
                      {l.leave_type_name}
                    </span>
                  </td>
                  <td style={{ padding: '0.875rem 1.25rem' }}>
                    <span>{l.start_date} to {l.end_date}</span>
                    <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{l.reason}</span>
                  </td>
                  <td style={{ padding: '0.875rem 1.25rem', fontWeight: 600 }}>{l.total_days}d</td>
                  <td style={{ padding: '0.875rem 1.25rem' }}>
                    <span style={{
                      padding: '0.25rem 0.625rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600,
                      backgroundColor: 
                        l.status === 'APPROVED' ? 'rgba(16, 185, 129, 0.12)' :
                        l.status === 'PENDING' ? 'rgba(245, 158, 11, 0.12)' :
                        'rgba(239, 68, 68, 0.12)',
                      color:
                        l.status === 'APPROVED' ? 'var(--success)' :
                        l.status === 'PENDING' ? 'var(--warning)' :
                        'var(--danger)'
                    }}>
                      {l.status}
                    </span>
                  </td>
                  <td style={{ padding: '0.875rem 1.25rem', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '0.5rem' }}>
                      {isHRorAdmin && l.status === 'PENDING' && (
                        <button
                          onClick={() => { setSelectedLeave(l); setIsReviewModalOpen(true); }}
                          style={{ padding: '0.375rem 0.75rem', backgroundColor: 'var(--primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}
                        >
                          Review
                        </button>
                      )}

                      {(l.status === 'PENDING' || l.status === 'APPROVED') && (
                        <button
                          onClick={() => handleCancel(l.id)}
                          title="Cancel Leave"
                          style={{ padding: '0.375rem 0.625rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', fontSize: '0.75rem', cursor: 'pointer', color: 'var(--danger)' }}
                        >
                          Cancel
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modals */}
      <ApplyLeaveModal
        isOpen={isApplyModalOpen}
        onClose={() => setIsApplyModalOpen(false)}
        leaveTypes={leaveTypes}
        onLeaveApplied={() => {
          setSuccess('Leave application submitted successfully.');
          loadLeaves();
          loadSummary();
        }}
      />

      <ReviewLeaveModal
        isOpen={isReviewModalOpen}
        onClose={() => setIsReviewModalOpen(false)}
        leaveRequest={selectedLeave}
        onReviewed={() => {
          setSuccess('Leave request decision recorded.');
          loadLeaves();
          loadSummary();
        }}
      />
    </div>
  );
}

