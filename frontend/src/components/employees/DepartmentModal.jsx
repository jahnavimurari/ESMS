import React, { useState, useEffect } from 'react';
import { Building, Plus, CheckCircle, AlertCircle, Edit2, Shield } from 'lucide-react';
import { employeeService } from '../../services/employeeService';
import { useAuth } from '../../context/AuthContext';

export default function DepartmentManagementModal({ isOpen, onClose, onDepartmentChange }) {
  const { role } = useAuth();
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [formData, setFormData] = useState({ name: '', code: '', description: '', is_active: true });
  const [editingDeptId, setEditingDeptId] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const canManage = role === 'ADMIN' || role === 'HR';

  const loadDepartments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await employeeService.getDepartments(true);
      if (res.success) {
        setDepartments(res.data);
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to load departments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadDepartments();
      setFormData({ name: '', code: '', description: '', is_active: true });
      setEditingDeptId(null);
      setError(null);
      setSuccess(null);
    }
  }, [isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || !formData.code) {
      setError('Department Name and Code are required.');
      return;
    }
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      if (editingDeptId) {
        await employeeService.updateDepartment(editingDeptId, formData);
        setSuccess('Department updated successfully.');
      } else {
        await employeeService.createDepartment(formData);
        setSuccess('Department created successfully.');
      }
      setFormData({ name: '', code: '', description: '', is_active: true });
      setEditingDeptId(null);
      loadDepartments();
      if (onDepartmentChange) onDepartmentChange();
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to save department.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (dept) => {
    setEditingDeptId(dept.id);
    setFormData({
      name: dept.name,
      code: dept.code,
      description: dept.description || '',
      is_active: dept.is_active
    });
    setError(null);
    setSuccess(null);
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1.5rem'
    }}>
      <div style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        width: '100%',
        maxWidth: '750px',
        maxHeight: '90vh',
        overflowY: 'auto',
        padding: '2rem',
        boxShadow: 'var(--shadow-xl)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            <Building size={24} color="var(--primary)" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Department Management</h2>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '1.25rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>✕</button>
        </div>

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', padding: '0.75rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.875rem' }}>
            <AlertCircle size={16} /> {error}
          </div>
        )}

        {success && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', padding: '0.75rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', fontSize: '0.875rem' }}>
            <CheckCircle size={16} /> {success}
          </div>
        )}

        {canManage && (
          <form onSubmit={handleSubmit} style={{ backgroundColor: 'var(--bg-app)', padding: '1.25rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', border: '1px solid var(--border)' }}>
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: '1rem' }}>
              {editingDeptId ? 'Edit Department' : 'Create New Department'}
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Department Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Engineering"
                  required
                  style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Department Code *</label>
                <input
                  type="text"
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  placeholder="e.g. ENG"
                  required
                  style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
                />
              </div>
            </div>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem' }}>Description</label>
              <input
                type="text"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief department responsibilities..."
                style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)' }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              {editingDeptId && (
                <button
                  type="button"
                  onClick={() => { setEditingDeptId(null); setFormData({ name: '', code: '', description: '', is_active: true }); }}
                  style={{ padding: '0.5rem 1rem', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}
                >
                  Cancel
                </button>
              )}
              <button
                type="submit"
                disabled={submitting}
                style={{ padding: '0.5rem 1rem', backgroundColor: 'var(--primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontWeight: 600, cursor: 'pointer' }}
              >
                {submitting ? 'Saving...' : editingDeptId ? 'Update Department' : 'Create Department'}
              </button>
            </div>
          </form>
        )}

        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem' }}>Active Departments</h3>
        {loading ? (
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Loading departments...</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {departments.map((dept) => (
              <div key={dept.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.875rem 1rem', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <strong style={{ fontSize: '0.9375rem' }}>{dept.name}</strong>
                    <span style={{ fontSize: '0.75rem', backgroundColor: 'var(--bg-app)', padding: '0.125rem 0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>{dept.code}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>• {dept.employee_count || 0} employees</span>
                  </div>
                  {dept.description && <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>{dept.description}</p>}
                </div>
                {canManage && (
                  <button
                    onClick={() => handleEdit(dept)}
                    style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', padding: '0.375rem 0.625rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', fontSize: '0.75rem', cursor: 'pointer' }}
                  >
                    <Edit2 size={13} /> Edit
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

