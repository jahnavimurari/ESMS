import React, { useState, useEffect } from 'react';
import { 
  Settings, Building, Briefcase, Calendar, Clock, 
  FileText, Users, Sliders, Check, Save, Plus, Trash2, 
  Edit3, AlertCircle, ArrowLeft, RefreshCw 
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { settingsService } from '../../services/settingsService';

export default function SettingsPage() {
  const { user } = useAuth();
  const isAdminOrHR = user?.role === 'ADMIN' || user?.role === 'HR';

  const [activeTab, setActiveTab] = useState('organization');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  // 1. Organization State
  const [orgData, setOrgData] = useState({
    name: '',
    logo_url: '',
    address: '',
    contact_email: '',
    contact_phone: '',
    website: '',
    timezone: 'UTC',
    date_format: 'YYYY-MM-DD',
    time_format: '24H',
    daily_working_hours: 8,
    working_days: ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY']
  });

  // 2. Designations State
  const [designations, setDesignations] = useState([]);
  const [newDesig, setNewDesig] = useState({ name: '', code: '', description: '' });

  // 3. Holidays State
  const [holidays, setHolidays] = useState([]);
  const [holidayYear, setHolidayYear] = useState(new Date().getFullYear());
  const [newHoliday, setNewHoliday] = useState({ name: '', holiday_date: '', is_optional: false, description: '' });

  // 4. Shifts State
  const [shifts, setShifts] = useState([]);
  const [newShift, setNewShift] = useState({
    name: '', code: '', start_time: '09:00', end_time: '18:00',
    grace_period_minutes: 15, half_day_hours: 4.0, full_day_hours: 8.0, is_default: false
  });

  // 5. Leave Policies State
  const [leavePolicies, setLeavePolicies] = useState([]);

  // 6. Categories State
  const [categories, setCategories] = useState([]);
  const [newCategory, setNewCategory] = useState({ code: '', name: '', description: '' });

  // 7. User Preferences State
  const [userPref, setUserPref] = useState({
    theme: 'DARK',
    date_format: 'YYYY-MM-DD',
    time_format: '24H',
    email_notifications: true,
    in_app_notifications: true
  });

  useEffect(() => {
    loadTabData(activeTab);
  }, [activeTab]);

  const loadTabData = async (tab) => {
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      if (tab === 'organization') {
        const res = await settingsService.getOrganizationSettings();
        if (res?.success) setOrgData(res.data);
      } else if (tab === 'designations') {
        const res = await settingsService.getDesignations();
        if (res?.success) setDesignations(res.data);
      } else if (tab === 'holidays') {
        const res = await settingsService.getHolidays(holidayYear);
        if (res?.success) setHolidays(res.data);
      } else if (tab === 'shifts') {
        const res = await settingsService.getShifts();
        if (res?.success) setShifts(res.data);
      } else if (tab === 'leaves') {
        const res = await settingsService.getLeavePolicies();
        if (res?.success) setLeavePolicies(res.data);
      } else if (tab === 'categories') {
        const res = await settingsService.getCategories();
        if (res?.success) setCategories(res.data);
      } else if (tab === 'preferences') {
        const res = await settingsService.getUserPreferences();
        if (res?.success) setUserPref(res.data);
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to load settings data.');
    } finally {
      setLoading(false);
    }
  };

  // Organization update
  const handleSaveOrganization = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await settingsService.updateOrganizationSettings(orgData);
      if (res?.success) {
        setOrgData(res.data);
        setMessage('Organization profile & settings updated successfully.');
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to update organization settings.');
    } finally {
      setLoading(false);
    }
  };

  // Designation creation
  const handleCreateDesignation = async (e) => {
    e.preventDefault();
    try {
      const res = await settingsService.createDesignation(newDesig);
      if (res?.success) {
        setDesignations(prev => [...prev, res.data]);
        setNewDesig({ name: '', code: '', description: '' });
        setMessage('Designation created successfully.');
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to create designation.');
    }
  };

  const handleDeleteDesignation = async (id) => {
    if (!window.confirm('Are you sure you want to delete this designation?')) return;
    try {
      const res = await settingsService.deleteDesignation(id);
      if (res?.success) {
        setDesignations(prev => prev.filter(d => d.id !== id));
        setMessage('Designation deleted successfully.');
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to delete designation.');
    }
  };

  // Holiday creation
  const handleCreateHoliday = async (e) => {
    e.preventDefault();
    try {
      const res = await settingsService.createHoliday(newHoliday);
      if (res?.success) {
        setHolidays(prev => [...prev, res.data]);
        setNewHoliday({ name: '', holiday_date: '', is_optional: false, description: '' });
        setMessage('Holiday added to calendar.');
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to add holiday.');
    }
  };

  const handleDeleteHoliday = async (id) => {
    if (!window.confirm('Delete this holiday?')) return;
    try {
      const res = await settingsService.deleteHoliday(id);
      if (res?.success) {
        setHolidays(prev => prev.filter(h => h.id !== id));
        setMessage('Holiday deleted.');
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to delete holiday.');
    }
  };

  // Shift creation
  const handleCreateShift = async (e) => {
    e.preventDefault();
    try {
      const res = await settingsService.createShift(newShift);
      if (res?.success) {
        setShifts(prev => [...prev, res.data]);
        setNewShift({
          name: '', code: '', start_time: '09:00', end_time: '18:00',
          grace_period_minutes: 15, half_day_hours: 4.0, full_day_hours: 8.0, is_default: false
        });
        setMessage('Work shift created.');
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to create shift.');
    }
  };

  // Leave policy update
  const handleUpdateLeavePolicy = async (id, updatedFields) => {
    try {
      const res = await settingsService.updateLeavePolicy(id, updatedFields);
      if (res?.success) {
        setLeavePolicies(prev => prev.map(p => p.id === id ? res.data : p));
        setMessage('Leave policy entitlement updated.');
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to update leave policy.');
    }
  };

  // Category creation
  const handleCreateCategory = async (e) => {
    e.preventDefault();
    try {
      const res = await settingsService.createCategory(newCategory);
      if (res?.success) {
        setCategories(prev => [...prev, res.data]);
        setNewCategory({ code: '', name: '', description: '' });
        setMessage('Category created.');
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to create category.');
    }
  };

  // User preference update
  const handleSavePreferences = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await settingsService.updateUserPreferences(userPref);
      if (res?.success) {
        setUserPref(res.data);
        setMessage('Personal preferences saved.');
      }
    } catch (err) {
      setError(err?.response?.data?.error?.message || 'Failed to update preferences.');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'organization', label: 'Organization Profile', icon: Building },
    { id: 'designations', label: 'Designations', icon: Briefcase },
    { id: 'holidays', label: 'Holiday Calendar', icon: Calendar },
    { id: 'shifts', label: 'Shifts & Rules', icon: Clock },
    { id: 'leaves', label: 'Leave Policies', icon: FileText },
    { id: 'categories', label: 'Categories', icon: Users },
    { id: 'preferences', label: 'User Preferences', icon: Sliders },
  ];

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
              <Settings size={26} />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white">Settings & Organization</h1>
              <p className="text-xs text-slate-400">
                Configure corporate profile, job designations, holiday calendar, shifts, leave rules, and personal preferences.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => loadTabData(activeTab)}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-all disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Notifications / Alerts */}
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

      {/* Navigation Tabs (Smooth flex without horizontal scrollbars) */}
      <div className="flex flex-wrap gap-1.5 p-1.5 bg-slate-900/80 border border-slate-800 rounded-2xl">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/25'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Contents Card */}
      <div className="p-6 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-xl">
        
        {/* 1. Organization Profile */}
        {activeTab === 'organization' && (
          <form onSubmit={handleSaveOrganization} className="space-y-6">
            <div className="border-b border-slate-800 pb-4">
              <h2 className="text-lg font-bold text-white tracking-tight">Organization Profile & General Settings</h2>
              <p className="text-xs text-slate-400 mt-1">
                Corporate identification, contact details, operational timezone, and default hours.
              </p>
            </div>

            {!isAdminOrHR && (
              <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-amber-400">
                Note: You are viewing organization settings as an employee. Only administrators and HR managers can edit these settings.
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Company Name</label>
                <input
                  type="text"
                  value={orgData.name || ''}
                  onChange={e => setOrgData({ ...orgData, name: e.target.value })}
                  disabled={!isAdminOrHR}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm focus:border-blue-500 transition-colors disabled:opacity-60"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Contact Email</label>
                <input
                  type="email"
                  value={orgData.contact_email || ''}
                  onChange={e => setOrgData({ ...orgData, contact_email: e.target.value })}
                  disabled={!isAdminOrHR}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm focus:border-blue-500 transition-colors disabled:opacity-60"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Contact Phone</label>
                <input
                  type="text"
                  value={orgData.contact_phone || ''}
                  onChange={e => setOrgData({ ...orgData, contact_phone: e.target.value })}
                  disabled={!isAdminOrHR}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm focus:border-blue-500 transition-colors disabled:opacity-60"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Website</label>
                <input
                  type="text"
                  value={orgData.website || ''}
                  onChange={e => setOrgData({ ...orgData, website: e.target.value })}
                  disabled={!isAdminOrHR}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm focus:border-blue-500 transition-colors disabled:opacity-60"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Corporate Timezone</label>
                <input
                  type="text"
                  value={orgData.timezone || ''}
                  onChange={e => setOrgData({ ...orgData, timezone: e.target.value })}
                  disabled={!isAdminOrHR}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm focus:border-blue-500 transition-colors disabled:opacity-60"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Daily Standard Working Hours</label>
                <input
                  type="number"
                  step="0.5"
                  value={orgData.daily_working_hours || 8}
                  onChange={e => setOrgData({ ...orgData, daily_working_hours: parseFloat(e.target.value) })}
                  disabled={!isAdminOrHR}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm focus:border-blue-500 transition-colors disabled:opacity-60"
                />
              </div>

              <div className="md:col-span-2 lg:col-span-3">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Headquarters Address</label>
                <textarea
                  value={orgData.address || ''}
                  onChange={e => setOrgData({ ...orgData, address: e.target.value })}
                  disabled={!isAdminOrHR}
                  rows={2}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white placeholder-slate-500 text-sm focus:border-blue-500 transition-colors disabled:opacity-60"
                />
              </div>
            </div>

            {isAdminOrHR && (
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-md shadow-blue-500/20 transition-all disabled:opacity-50"
              >
                <Save size={16} /> Save Changes
              </button>
            )}
          </form>
        )}

        {/* 2. Designations */}
        {activeTab === 'designations' && (
          <div className="space-y-6">
            <div className="border-b border-slate-800 pb-4">
              <h2 className="text-lg font-bold text-white tracking-tight">Job Designations</h2>
              <p className="text-xs text-slate-400 mt-1">Company functional roles and operational titles.</p>
            </div>

            {isAdminOrHR && (
              <form onSubmit={handleCreateDesignation} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800">
                <input
                  type="text"
                  placeholder="Designation Name (e.g. Lead Engineer)"
                  value={newDesig.name}
                  onChange={e => setNewDesig({ ...newDesig, name: e.target.value })}
                  className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm"
                  required
                />
                <input
                  type="text"
                  placeholder="Code (e.g. LEAD_ENG)"
                  value={newDesig.code}
                  onChange={e => setNewDesig({ ...newDesig, code: e.target.value })}
                  className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm"
                  required
                />
                <input
                  type="text"
                  placeholder="Description (Optional)"
                  value={newDesig.description}
                  onChange={e => setNewDesig({ ...newDesig, description: e.target.value })}
                  className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm"
                />
                <button
                  type="submit"
                  className="flex items-center justify-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-semibold shadow-md transition-all"
                >
                  <Plus size={16} /> Add Designation
                </button>
              </form>
            )}

            <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-slate-800/60 border-b border-slate-800 text-slate-300 text-xs font-bold uppercase tracking-wider">
                    <th className="py-3 px-4">Name</th>
                    <th className="py-3 px-4">Code</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Status</th>
                    {isAdminOrHR && <th className="py-3 px-4 text-right">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {designations.length === 0 ? (
                    <tr><td colSpan={5} className="py-8 text-center text-slate-500">No designations defined.</td></tr>
                  ) : (
                    designations.map(d => (
                      <tr key={d.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4 font-semibold text-white">{d.name}</td>
                        <td className="py-3 px-4 font-mono text-xs text-slate-400">{d.code}</td>
                        <td className="py-3 px-4 text-slate-300">{d.department_name || 'General'}</td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium border ${
                            d.is_active ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-slate-800 text-slate-400 border-slate-700'
                          }`}>
                            {d.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        {isAdminOrHR && (
                          <td className="py-3 px-4 text-right">
                            <button
                              onClick={() => handleDeleteDesignation(d.id)}
                              className="text-slate-500 hover:text-rose-400 transition-colors"
                              title="Delete"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 3. Holidays */}
        {activeTab === 'holidays' && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-3">
              <div>
                <h2 className="text-lg font-bold text-white tracking-tight">Holiday Calendar ({holidayYear})</h2>
                <p className="text-xs text-slate-400 mt-1">Official corporate holidays and floating observances.</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Year:</span>
                <input
                  type="number"
                  value={holidayYear}
                  onChange={e => {
                    const y = parseInt(e.target.value) || new Date().getFullYear();
                    setHolidayYear(y);
                    settingsService.getHolidays(y).then(res => res?.success && setHolidays(res.data));
                  }}
                  className="w-24 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs font-mono"
                />
              </div>
            </div>

            {isAdminOrHR && (
              <form onSubmit={handleCreateHoliday} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800 items-center">
                <input
                  type="text"
                  placeholder="Holiday Name (e.g. Labor Day)"
                  value={newHoliday.name}
                  onChange={e => setNewHoliday({ ...newHoliday, name: e.target.value })}
                  className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm"
                  required
                />
                <input
                  type="date"
                  value={newHoliday.holiday_date}
                  onChange={e => setNewHoliday({ ...newHoliday, holiday_date: e.target.value })}
                  className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm"
                  required
                />
                <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newHoliday.is_optional}
                    onChange={e => setNewHoliday({ ...newHoliday, is_optional: e.target.checked })}
                    className="rounded border-slate-700 bg-slate-900"
                  />
                  <span>Optional / Floating</span>
                </label>
                <button
                  type="submit"
                  className="flex items-center justify-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-semibold shadow-md transition-all"
                >
                  <Plus size={16} /> Add Holiday
                </button>
              </form>
            )}

            <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-slate-800/60 border-b border-slate-800 text-slate-300 text-xs font-bold uppercase tracking-wider">
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4">Holiday Name</th>
                    <th className="py-3 px-4">Type</th>
                    {isAdminOrHR && <th className="py-3 px-4 text-right">Actions</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {holidays.length === 0 ? (
                    <tr><td colSpan={4} className="py-8 text-center text-slate-500">No holidays registered for {holidayYear}.</td></tr>
                  ) : (
                    holidays.map(h => (
                      <tr key={h.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-4 font-mono text-xs text-slate-300">{h.holiday_date}</td>
                        <td className="py-3 px-4 font-semibold text-white">{h.name}</td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                            h.is_optional ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                          }`}>
                            {h.is_optional ? 'Optional' : 'Mandatory'}
                          </span>
                        </td>
                        {isAdminOrHR && (
                          <td className="py-3 px-4 text-right">
                            <button
                              onClick={() => handleDeleteHoliday(h.id)}
                              className="text-slate-500 hover:text-rose-400 transition-colors"
                              title="Delete"
                            >
                              <Trash2 size={16} />
                            </button>
                          </td>
                        )}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 4. Shifts & Attendance Rules */}
        {activeTab === 'shifts' && (
          <div className="space-y-6">
            <div className="border-b border-slate-800 pb-4">
              <h2 className="text-lg font-bold text-white tracking-tight">Work Shifts & Attendance Timings</h2>
              <p className="text-xs text-slate-400 mt-1">Daily shift intervals, grace periods, and minimum work thresholds.</p>
            </div>

            {isAdminOrHR && (
              <form onSubmit={handleCreateShift} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800 items-end">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Shift Name</label>
                  <input
                    type="text"
                    placeholder="Regular Day Shift"
                    value={newShift.name}
                    onChange={e => setNewShift({ ...newShift, name: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Shift Code</label>
                  <input
                    type="text"
                    placeholder="REGULAR"
                    value={newShift.code}
                    onChange={e => setNewShift({ ...newShift, code: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Start Time</label>
                  <input
                    type="time"
                    value={newShift.start_time}
                    onChange={e => setNewShift({ ...newShift, start_time: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">End Time</label>
                  <input
                    type="time"
                    value={newShift.end_time}
                    onChange={e => setNewShift({ ...newShift, end_time: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm"
                    required
                  />
                </div>
                <button
                  type="submit"
                  className="sm:col-span-2 lg:col-span-4 flex items-center justify-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-semibold shadow-md transition-all mt-2"
                >
                  <Plus size={16} /> Create Work Shift
                </button>
              </form>
            )}

            <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-slate-800/60 border-b border-slate-800 text-slate-300 text-xs font-bold uppercase tracking-wider">
                    <th className="py-3 px-4">Shift Name</th>
                    <th className="py-3 px-4">Code</th>
                    <th className="py-3 px-4">Hours</th>
                    <th className="py-3 px-4">Grace Period</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {shifts.map(s => (
                    <tr key={s.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-semibold text-white">
                        {s.name} {s.is_default && <span className="ml-2 text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">Default</span>}
                      </td>
                      <td className="py-3 px-4 font-mono text-xs text-slate-400">{s.code}</td>
                      <td className="py-3 px-4 text-slate-300">{s.start_time} - {s.end_time}</td>
                      <td className="py-3 px-4 text-slate-400 text-xs">{s.grace_period_minutes} mins</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium border ${
                          s.is_active ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}>
                          {s.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 5. Leave Policies */}
        {activeTab === 'leaves' && (
          <div className="space-y-6">
            <div className="border-b border-slate-800 pb-4">
              <h2 className="text-lg font-bold text-white tracking-tight">Leave Types & Annual Entitlements</h2>
              <p className="text-xs text-slate-400 mt-1">Configurable annual quotas, payment status, and leave types.</p>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-slate-800/60 border-b border-slate-800 text-slate-300 text-xs font-bold uppercase tracking-wider">
                    <th className="py-3 px-4">Leave Type</th>
                    <th className="py-3 px-4">Code</th>
                    <th className="py-3 px-4">Days / Year</th>
                    <th className="py-3 px-4">Paid Status</th>
                    <th className="py-3 px-4">Active</th>
                    {isAdminOrHR && <th className="py-3 px-4 text-right">Configure</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {leavePolicies.map(p => (
                    <tr key={p.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-semibold text-white">{p.name}</td>
                      <td className="py-3 px-4 font-mono text-xs text-slate-400">{p.code}</td>
                      <td className="py-3 px-4 text-slate-300">{p.days_per_year} days</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium border ${
                          p.is_paid ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        }`}>
                          {p.is_paid ? 'Paid' : 'Unpaid'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-300">{p.is_active ? 'Yes' : 'No'}</td>
                      {isAdminOrHR && (
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => {
                              const newDays = prompt(`Enter annual entitlement days for ${p.name}:`, p.days_per_year);
                              if (newDays !== null && !isNaN(parseInt(newDays))) {
                                handleUpdateLeavePolicy(p.id, { days_per_year: parseInt(newDays) });
                              }
                            }}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium text-blue-400 hover:text-white bg-blue-500/10 hover:bg-blue-600 border border-blue-500/20 transition-all"
                          >
                            <Edit3 size={12} /> Edit Days
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 6. Categories */}
        {activeTab === 'categories' && (
          <div className="space-y-6">
            <div className="border-b border-slate-800 pb-4">
              <h2 className="text-lg font-bold text-white tracking-tight">Employee Categories</h2>
              <p className="text-xs text-slate-400 mt-1">Standard employment categories matching system employee contracts.</p>
            </div>

            {isAdminOrHR && (
              <form onSubmit={handleCreateCategory} className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800 items-center">
                <input
                  type="text"
                  placeholder="Category Code (e.g. CONSULTANT)"
                  value={newCategory.code}
                  onChange={e => setNewCategory({ ...newCategory, code: e.target.value })}
                  className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm"
                  required
                />
                <input
                  type="text"
                  placeholder="Category Name"
                  value={newCategory.name}
                  onChange={e => setNewCategory({ ...newCategory, name: e.target.value })}
                  className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm"
                  required
                />
                <button
                  type="submit"
                  className="flex items-center justify-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-semibold shadow-md transition-all"
                >
                  <Plus size={16} /> Add Category
                </button>
              </form>
            )}

            <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-slate-800/60 border-b border-slate-800 text-slate-300 text-xs font-bold uppercase tracking-wider">
                    <th className="py-3 px-4">Code</th>
                    <th className="py-3 px-4">Name</th>
                    <th className="py-3 px-4">Description</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {categories.map(c => (
                    <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 font-mono text-xs font-semibold text-white">{c.code}</td>
                      <td className="py-3 px-4 text-slate-200">{c.name}</td>
                      <td className="py-3 px-4 text-slate-400 text-xs">{c.description || '—'}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium border ${
                          c.is_active ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}>
                          {c.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 7. User Preferences */}
        {activeTab === 'preferences' && (
          <form onSubmit={handleSavePreferences} className="space-y-6">
            <div className="border-b border-slate-800 pb-4">
              <h2 className="text-lg font-bold text-white tracking-tight">Personal Preferences</h2>
              <p className="text-xs text-slate-400 mt-1">Configure your personal interface display formats and notifications.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Theme Mode</label>
                <select
                  value={userPref.theme}
                  onChange={e => setUserPref({ ...userPref, theme: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                >
                  <option value="DARK">Dark Theme</option>
                  <option value="LIGHT">Light Theme</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Date Display Format</label>
                <select
                  value={userPref.date_format}
                  onChange={e => setUserPref({ ...userPref, date_format: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                >
                  <option value="YYYY-MM-DD">YYYY-MM-DD (2026-11-26)</option>
                  <option value="DD/MM/YYYY">DD/MM/YYYY (26/11/2026)</option>
                  <option value="MM/DD/YYYY">MM/DD/YYYY (11/26/2026)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">Time Format</label>
                <select
                  value={userPref.time_format}
                  onChange={e => setUserPref({ ...userPref, time_format: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                >
                  <option value="24H">24 Hours (14:30)</option>
                  <option value="12H">12 Hours AM/PM (02:30 PM)</option>
                </select>
              </div>

              <div className="md:col-span-3 space-y-3 pt-2">
                <span className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">Notification Preferences</span>
                <div className="space-y-2">
                  <label className="flex items-center gap-2.5 text-xs text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={userPref.in_app_notifications}
                      onChange={e => setUserPref({ ...userPref, in_app_notifications: e.target.checked })}
                      className="rounded border-slate-700 bg-slate-950"
                    />
                    <span>Receive in-app bell notifications and real-time alerts</span>
                  </label>
                  <label className="flex items-center gap-2.5 text-xs text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={userPref.email_notifications}
                      onChange={e => setUserPref({ ...userPref, email_notifications: e.target.checked })}
                      className="rounded border-slate-700 bg-slate-950"
                    />
                    <span>Receive email notifications and summary digests</span>
                  </label>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-md shadow-blue-500/20 transition-all disabled:opacity-50"
            >
              <Save size={16} /> Save Preferences
            </button>
          </form>
        )}

      </div>
    </div>
  );
}
