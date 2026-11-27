import React, { useState, useEffect } from 'react';
import { UserPlus, Edit3, AlertCircle, CheckCircle } from 'lucide-react';
import { employeeService } from '../../services/employeeService';

export default function EmployeeFormModal({ isOpen, onClose, employeeToEdit, onEmployeeSaved, departments = [] }) {
  const [formData, setFormData] = useState({
    employee_code: '',
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    role: 'EMPLOYEE',
    phone: '',
    gender: 'PREFER_NOT_TO_SAY',
    department_id: '',
    designation: '',
    joining_date: '',
    employment_type: 'FULL_TIME',
    status: 'ACTIVE'
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      if (employeeToEdit) {
        setFormData({
          employee_code: employeeToEdit.employee_code || '',
          first_name: employeeToEdit.first_name || '',
          last_name: employeeToEdit.last_name || '',
          email: employeeToEdit.email || '',
          password: '',
          role: employeeToEdit.role || 'EMPLOYEE',
          phone: employeeToEdit.phone || '',
          gender: employeeToEdit.gender || 'PREFER_NOT_TO_SAY',
          department_id: employeeToEdit.department_id || (departments[0]?.id || ''),
          designation: employeeToEdit.designation || '',
          joining_date: employeeToEdit.joining_date || '',
          employment_type: employeeToEdit.employment_type || 'FULL_TIME',
          status: employeeToEdit.status || 'ACTIVE'
        });
      } else {
        setFormData({
          employee_code: `EMP-${Math.floor(1000 + Math.random() * 9000)}`,
          first_name: '',
          last_name: '',
          email: '',
          password: 'Welcome123!',
          role: 'EMPLOYEE',
          phone: '',
          gender: 'PREFER_NOT_TO_SAY',
          department_id: departments[0]?.id || '',
          designation: '',
          joining_date: new Date().toISOString().split('T')[0],
          employment_type: 'FULL_TIME',
          status: 'ACTIVE'
        });
      }
      setError(null);
    }
  }, [isOpen, employeeToEdit, departments]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!formData.first_name || !formData.last_name || !formData.department_id || !formData.designation) {
      setError('Please fill in all mandatory fields.');
      return;
    }

    setLoading(true);
    try {
      if (employeeToEdit) {
        await employeeService.updateEmployee(employeeToEdit.id, formData);
      } else {
        await employeeService.createEmployee(formData);
      }
      onEmployeeSaved();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to save employee profile.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

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
        width: '100%', maxWidth: '700px', maxHeight: '90vh',
        overflowY: 'auto', padding: '2rem', boxShadow: 'var(--shadow-xl)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            {employeeToEdit ? <Edit3 size={24} color="var(--primary)" /> : <UserPlus size={24} color="var(--primary)" />}
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              {employeeToEdit ? `Edit Profile: ${employeeToEdit.full_name}` : 'Onboard New Employee'}
            </h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>✕</button>
        </div>

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', padding: '0.75rem', borderRadius: 'var(--radius-md)', marginBottom: '1.25rem', fontSize: '0.875rem' }}>
            <AlertCircle size={16} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Employee Code *</label>
              <input
                type="text"
                value={formData.employee_code}
                onChange={(e) => setFormData({ ...formData, employee_code: e.target.value })}
                disabled={Boolean(employeeToEdit)}
                required
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Work Email *</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                disabled={Boolean(employeeToEdit)}
                required
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>First Name *</label>
              <input
                type="text"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                required
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Last Name *</label>
              <input
                type="text"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                required
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Department *</label>
              <select
                value={formData.department_id}
                onChange={(e) => setFormData({ ...formData, department_id: parseInt(e.target.value) })}
                required
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              >
                <option value="">Select Department</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Designation *</label>
              <input
                type="text"
                value={formData.designation}
                onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                placeholder="e.g. Senior Frontend Engineer"
                required
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Phone Number</label>
              <input
                type="text"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="+1 234 567 890"
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Employment Type</label>
              <select
                value={formData.employment_type}
                onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              >
                <option value="FULL_TIME">Full Time</option>
                <option value="PART_TIME">Part Time</option>
                <option value="CONTRACT">Contract</option>
                <option value="INTERN">Intern</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>System Role</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              >
                <option value="EMPLOYEE">Employee</option>
                <option value="HR">HR Specialist</option>
                <option value="ADMIN">Administrator</option>
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Employment Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              >
                <option value="ACTIVE">Active</option>
                <option value="ON_LEAVE">On Leave</option>
                <option value="SUSPENDED">Suspended</option>
                <option value="TERMINATED">Terminated</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button
              type="button"
              onClick={onClose}
              style={{ padding: '0.625rem 1.25rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{ padding: '0.625rem 1.25rem', backgroundColor: 'var(--primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontWeight: 600, cursor: 'pointer' }}
            >
              {loading ? 'Saving...' : employeeToEdit ? 'Save Changes' : 'Create Employee'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

