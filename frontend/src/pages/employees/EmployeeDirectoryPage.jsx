import React, { useState, useEffect } from 'react';
import { 
  Users, Search, Filter, Plus, Building, Eye, Edit2, 
  Power, CheckCircle, AlertCircle, RefreshCw, ChevronLeft, ChevronRight 
} from 'lucide-react';
import { employeeService } from '../../services/employeeService';
import { useAuth } from '../../context/AuthContext';
import DepartmentManagementModal from '../../components/employees/DepartmentModal';
import EmployeeFormModal from '../../components/employees/EmployeeFormModal';
import EmployeeDetailModal from '../../components/employees/EmployeeDetailModal';

export default function EmployeeDirectoryPage() {
  const { user, role } = useAuth();
  const isHRorAdmin = role === 'ADMIN' || role === 'HR';

  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');

  // Modals state
  const [isDeptModalOpen, setIsDeptModalOpen] = useState(false);
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [employeeToEdit, setEmployeeToEdit] = useState(null);

  const loadDepartments = async () => {
    try {
      const res = await employeeService.getDepartments(false);
      if (res.success) setDepartments(res.data);
    } catch (err) {
      console.error('Failed to load departments', err);
    }
  };

  const loadEmployees = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (search) params.search = search;
      if (selectedDept) params.department_id = selectedDept;
      if (selectedStatus) params.status = selectedStatus;

      const res = await employeeService.getEmployees(params);
      if (res.success) {
        setEmployees(res.data.items || []);
        setTotalCount(res.data.total || 0);
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to retrieve employee directory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDepartments();
  }, []);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      loadEmployees();
    }, 250);
    return () => clearTimeout(debounceTimer);
  }, [search, selectedDept, selectedStatus]);

  const handleToggleStatus = async (emp) => {
    const isActivating = emp.status !== 'ACTIVE';
    const confirmMsg = isActivating 
      ? `Are you sure you want to activate employee ${emp.full_name}?`
      : `Are you sure you want to suspend employee ${emp.full_name}?`;

    if (!window.confirm(confirmMsg)) return;

    try {
      const newStatus = isActivating ? 'ACTIVE' : 'SUSPENDED';
      await employeeService.updateEmployeeStatus(emp.id, {
        status: newStatus,
        is_active: isActivating
      });
      setSuccess(`Employee ${emp.full_name} status updated to ${newStatus}.`);
      loadEmployees();
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to update employee status.');
    }
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
      {/* Page Title & Action Bar */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem'
      }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Users size={28} color="var(--primary)" /> Employee Directory
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Centralized organizational registry • {totalCount} total employee record{totalCount === 1 ? '' : 's'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={() => setIsDeptModalOpen(true)}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
              padding: '0.625rem 1rem', backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
              color: 'var(--text-primary)', fontSize: '0.875rem', fontWeight: 500, cursor: 'pointer'
            }}
          >
            <Building size={16} /> Departments
          </button>

          {isHRorAdmin && (
            <button
              onClick={() => { setEmployeeToEdit(null); setIsFormModalOpen(true); }}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
                padding: '0.625rem 1.125rem', backgroundColor: 'var(--primary)',
                border: 'none', borderRadius: 'var(--radius-md)',
                color: '#fff', fontSize: '0.875rem', fontWeight: 600, cursor: 'pointer'
              }}
            >
              <Plus size={16} /> Onboard Employee
            </button>
          )}
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'rgba(239, 68, 68, 0.12)', color: 'var(--danger)', padding: '0.875rem 1.25rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {success && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'rgba(16, 185, 129, 0.12)', color: 'var(--success)', padding: '0.875rem 1.25rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
          <CheckCircle size={18} /> {success}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div style={{
        display: 'flex', gap: '1rem', backgroundColor: 'var(--bg-surface)',
        padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)',
        marginBottom: '1.5rem', flexWrap: 'wrap'
      }}>
        <div style={{ flex: '1 1 250px', position: 'relative' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search by name, employee code, email, designation..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '100%', padding: '0.5rem 0.75rem 0.5rem 2.5rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: '0.875rem' }}
          />
        </div>

        <div style={{ flex: '0 0 200px' }}>
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

        <div style={{ flex: '0 0 160px' }}>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', color: 'var(--text-primary)', fontSize: '0.875rem' }}
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="ON_LEAVE">On Leave</option>
            <option value="SUSPENDED">Suspended</option>
            <option value="TERMINATED">Terminated</option>
          </select>
        </div>
      </div>

      {/* Directory Table */}
      <div style={{
        backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)', overflow: 'hidden', boxShadow: 'var(--shadow-sm)'
      }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite', margin: '0 auto 0.75rem' }} />
            Loading employee profiles...
          </div>
        ) : employees.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            <Users size={36} color="var(--text-muted)" style={{ margin: '0 auto 0.75rem' }} />
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>No employees found</h3>
            <p style={{ fontSize: '0.875rem', marginTop: '0.25rem' }}>Try adjusting your search query or department filters.</p>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-app)', color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                <th style={{ padding: '0.75rem 1.25rem' }}>Employee</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Code</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Department</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Designation</th>
                <th style={{ padding: '0.75rem 1.25rem' }}>Status</th>
                <th style={{ padding: '0.75rem 1.25rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((emp) => (
                <tr key={emp.id} style={{ borderBottom: '1px solid var(--border)', transition: 'background 0.15s' }}>
                  <td style={{ padding: '0.875rem 1.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{
                        width: '36px', height: '36px', borderRadius: '9999px',
                        backgroundColor: 'rgba(59, 130, 246, 0.15)', color: 'var(--primary)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontWeight: 600, fontSize: '0.8125rem'
                      }}>
                        {emp.first_name[0]}{emp.last_name[0]}
                      </div>
                      <div>
                        <strong style={{ display: 'block', color: 'var(--text-primary)' }}>{emp.full_name}</strong>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{emp.email}</span>
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '0.875rem 1.25rem', fontFamily: 'monospace', fontWeight: 600 }}>{emp.employee_code}</td>
                  <td style={{ padding: '0.875rem 1.25rem' }}>
                    <span style={{ backgroundColor: 'var(--bg-app)', padding: '0.25rem 0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', fontSize: '0.8125rem' }}>
                      {emp.department_name}
                    </span>
                  </td>
                  <td style={{ padding: '0.875rem 1.25rem', color: 'var(--text-secondary)' }}>{emp.designation}</td>
                  <td style={{ padding: '0.875rem 1.25rem' }}>
                    <span style={{
                      padding: '0.25rem 0.625rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 600,
                      backgroundColor: emp.status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                      color: emp.status === 'ACTIVE' ? 'var(--success)' : 'var(--danger)'
                    }}>
                      {emp.status}
                    </span>
                  </td>
                  <td style={{ padding: '0.875rem 1.25rem', textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '0.5rem' }}>
                      <button
                        onClick={() => { setSelectedEmployee(emp); setIsDetailModalOpen(true); }}
                        title="View Details"
                        style={{ padding: '0.375rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', cursor: 'pointer' }}
                      >
                        <Eye size={14} color="var(--text-secondary)" />
                      </button>

                      {isHRorAdmin && (
                        <>
                          <button
                            onClick={() => { setEmployeeToEdit(emp); setIsFormModalOpen(true); }}
                            title="Edit Employee"
                            style={{ padding: '0.375rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', cursor: 'pointer' }}
                          >
                            <Edit2 size={14} color="var(--primary)" />
                          </button>
                          <button
                            onClick={() => handleToggleStatus(emp)}
                            title={emp.status === 'ACTIVE' ? 'Suspend Employee' : 'Activate Employee'}
                            style={{
                              padding: '0.375rem', backgroundColor: 'var(--bg-app)', border: '1px solid var(--border)',
                              borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                              color: emp.status === 'ACTIVE' ? 'var(--danger)' : 'var(--success)'
                            }}
                          >
                            <Power size={14} />
                          </button>
                        </>
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
      <DepartmentManagementModal
        isOpen={isDeptModalOpen}
        onClose={() => setIsDeptModalOpen(false)}
        onDepartmentChange={() => { loadDepartments(); loadEmployees(); }}
      />

      <EmployeeFormModal
        isOpen={isFormModalOpen}
        onClose={() => setIsFormModalOpen(false)}
        employeeToEdit={employeeToEdit}
        departments={departments}
        onEmployeeSaved={() => {
          setSuccess('Employee record successfully updated.');
          loadEmployees();
          setTimeout(() => setSuccess(null), 3000);
        }}
      />

      <EmployeeDetailModal
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        employee={selectedEmployee}
      />
    </div>
  );
}

