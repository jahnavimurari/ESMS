import React, { useState, useEffect } from 'react';
import { 
  Users, Search, Filter, ShieldCheck, UserX, UserCheck, 
  RefreshCw, AlertCircle, Check, ChevronLeft, ChevronRight, ArrowLeft 
} from 'lucide-react';
import { adminService } from '../../services/adminService';

export default function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    fetchUsers();
  }, [page, roleFilter, statusFilter]);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = { page, per_page: 10 };
      if (search.trim()) params.search = search.trim();
      if (roleFilter) params.role = roleFilter;
      if (statusFilter !== '') params.is_active = statusFilter;

      const res = await adminService.listUsers(params);
      if (res?.success) {
        setUsers(res.data.users);
        setTotal(res.data.total);
        setPages(res.data.pages);
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to load user roster.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const handleRoleChange = async (userId, newRole) => {
    setError(null);
    setMessage(null);
    try {
      const res = await adminService.updateUserRole(userId, newRole);
      if (res?.success) {
        setUsers(prev => prev.map(u => u.id === userId ? { ...u, role: newRole } : u));
        setMessage(`Role successfully updated to ${newRole}.`);
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to update user role.');
    }
  };

  const handleStatusToggle = async (userId, currentStatus) => {
    setError(null);
    setMessage(null);
    const newStatus = !currentStatus;
    try {
      const res = await adminService.updateUserStatus(userId, newStatus);
      if (res?.success) {
        setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: newStatus } : u));
        setMessage(`Account ${newStatus ? 'activated' : 'deactivated'} successfully.`);
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to update account status.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors mb-2"
          >
            <ArrowLeft size={14} /> Back
          </button>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Users size={26} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">User Administration</h1>
              <p className="text-xs text-slate-400">
                Manage registered accounts, assign RBAC access roles, and toggle account activation status.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={fetchUsers}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-all disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Messages */}
      {message && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-2.5 text-sm">
          <Check size={18} /> {message}
        </div>
      )}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-2.5 text-sm">
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* Filter / Search Bar */}
      <form onSubmit={handleSearchSubmit} className="flex gap-3 flex-wrap items-center">
        <div className="relative flex-1 min-w-[240px]">
          <Search size={16} className="absolute left-3.5 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search by email, name or employee code..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-white placeholder-slate-500 text-sm focus:border-blue-500 transition-colors"
          />
        </div>

        <select
          value={roleFilter}
          onChange={e => { setRoleFilter(e.target.value); setPage(1); }}
          className="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-sm focus:border-blue-500 transition-colors"
        >
          <option value="">All Roles</option>
          <option value="ADMIN">ADMIN</option>
          <option value="HR">HR</option>
          <option value="EMPLOYEE">EMPLOYEE</option>
        </select>

        <select
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(1); }}
          className="px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-sm focus:border-blue-500 transition-colors"
        >
          <option value="">All Statuses</option>
          <option value="true">Active Only</option>
          <option value="false">Inactive Only</option>
        </select>

        <button
          type="submit"
          className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-md shadow-blue-500/20 transition-all"
        >
          Search
        </button>
      </form>

      {/* Users Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="bg-slate-800/60 border-b border-slate-800 text-slate-300 text-xs font-bold uppercase tracking-wider">
                <th className="py-3.5 px-4">User Email</th>
                <th className="py-3.5 px-4">Employee Name</th>
                <th className="py-3.5 px-4">Role</th>
                <th className="py-3.5 px-4">Account Status</th>
                <th className="py-3.5 px-4">Last Login</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    <div className="flex items-center justify-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
                      <span>Loading accounts...</span>
                    </div>
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No users matching criteria.
                  </td>
                </tr>
              ) : (
                users.map(u => (
                  <tr key={u.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-white">
                      {u.email}
                    </td>
                    <td className="py-3.5 px-4 text-slate-300">
                      {u.employee ? (
                        <span>
                          <strong className="text-white font-medium">{u.employee.full_name}</strong>{' '}
                          <span className="text-xs text-slate-400">({u.employee.employee_code})</span>
                        </span>
                      ) : (
                        <span className="text-xs text-slate-500 italic">Unlinked Account</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <select
                        value={u.role}
                        onChange={e => handleRoleChange(u.id, e.target.value)}
                        className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition-all ${
                          u.role === 'ADMIN'
                            ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                            : u.role === 'HR'
                            ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                            : 'bg-blue-500/10 text-blue-300 border-blue-500/30'
                        }`}
                      >
                        <option value="ADMIN" className="bg-slate-900 text-rose-300">ADMIN</option>
                        <option value="HR" className="bg-slate-900 text-amber-300">HR</option>
                        <option value="EMPLOYEE" className="bg-slate-900 text-blue-300">EMPLOYEE</option>
                      </select>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                        u.is_active 
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      }`}>
                        {u.is_active ? 'Active' : 'Deactivated'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-400">
                      {u.last_login ? new Date(u.last_login).toLocaleString() : 'Never'}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => handleStatusToggle(u.id, u.is_active)}
                        className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                          u.is_active
                            ? 'bg-rose-500/10 text-rose-300 border-rose-500/25 hover:bg-rose-500/20'
                            : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25 hover:bg-emerald-500/20'
                        }`}
                      >
                        {u.is_active ? <UserX size={14} /> : <UserCheck size={14} />}
                        {u.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between p-4 border-t border-slate-800 text-xs text-slate-400 gap-3">
          <div>
            Total Accounts: <strong className="text-white font-semibold">{total}</strong> &bull; Page {page} of {pages}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-800/60 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft size={14} /> Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(pages, p + 1))}
              disabled={page >= pages}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-800/60 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              Next <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
