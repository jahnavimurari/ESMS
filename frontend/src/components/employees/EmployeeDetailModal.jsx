import React from 'react';
import { User, Mail, Phone, Calendar, Briefcase, Building, Shield, CheckCircle2, XCircle } from 'lucide-react';

export default function EmployeeDetailModal({ isOpen, onClose, employee }) {
  if (!isOpen || !employee) return null;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1000, padding: '1.5rem'
    }}>
      <div style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        width: '100%', maxWidth: '600px', maxHeight: '90vh',
        overflowY: 'auto', padding: '2rem', boxShadow: 'var(--shadow-xl)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              width: '56px', height: '56px', borderRadius: '9999px',
              backgroundColor: 'rgba(59, 130, 246, 0.1)', color: 'var(--primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.5rem', fontWeight: 700
            }}>
              {employee.first_name[0]}{employee.last_name[0]}
            </div>
            <div>
              <h2 style={{ fontSize: '1.375rem', fontWeight: 700 }}>{employee.full_name}</h2>
              <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                {employee.designation} • {employee.department_name}
              </span>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>✕</button>
        </div>

        {/* Status Pills */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
            padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600,
            backgroundColor: employee.status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            color: employee.status === 'ACTIVE' ? 'var(--success)' : 'var(--danger)'
          }}>
            {employee.status === 'ACTIVE' ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
            {employee.status}
          </span>
          <span style={{
            padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600,
            backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', color: 'var(--text-secondary)'
          }}>
            {employee.employment_type}
          </span>
          <span style={{
            padding: '0.25rem 0.75rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600,
            backgroundColor: 'rgba(59, 130, 246, 0.1)', color: 'var(--primary)'
          }}>
            {employee.role}
          </span>
        </div>

        {/* Detailed Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', fontSize: '0.875rem' }}>
          <div>
            <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>Employee ID</span>
            <strong>{employee.employee_code}</strong>
          </div>
          <div>
            <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>Work Email</span>
            <strong>{employee.email || 'N/A'}</strong>
          </div>
          <div>
            <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>Phone</span>
            <strong>{employee.phone || 'Not provided'}</strong>
          </div>
          <div>
            <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>Joining Date</span>
            <strong>{employee.joining_date || 'N/A'}</strong>
          </div>
          <div>
            <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>Department</span>
            <strong>{employee.department_name} ({employee.department_code})</strong>
          </div>
          <div>
            <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '0.25rem' }}>Reporting Manager</span>
            <strong>{employee.reporting_manager_name || 'None'}</strong>
          </div>
        </div>

        <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{ padding: '0.5rem 1.25rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

