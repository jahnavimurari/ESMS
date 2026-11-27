import React, { useState, useRef, useEffect } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Users, Clock, Calendar, CheckSquare, 
  Award, FileBarChart, Settings, ShieldAlert, LogOut, 
  Menu, X, ChevronDown, Activity, UserCog, MoreHorizontal
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import NotificationBell from '../components/notifications/NotificationBell';

export default function AppLayout({ children }) {
  const { user, logout, role } = useAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [adminMenuOpen, setAdminMenuOpen] = useState(false);
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const adminRef = useRef(null);
  const moreRef = useRef(null);

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (adminRef.current && !adminRef.current.contains(event.target)) {
        setAdminMenuOpen(false);
      }
      if (moreRef.current && !moreRef.current.contains(event.target)) {
        setMoreMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close menus on route change
  useEffect(() => {
    setMobileMenuOpen(false);
    setAdminMenuOpen(false);
    setMoreMenuOpen(false);
  }, [location.pathname]);

  const getDashboardPath = () => {
    switch (role) {
      case 'ADMIN': return '/dashboard/admin';
      case 'HR': return '/dashboard/hr';
      case 'EMPLOYEE':
      default: return '/dashboard/employee';
    }
  };

  // Primary navigation items (always visible on desktop)
  const primaryNavItems = [
    { label: 'Dashboard', path: getDashboardPath(), icon: LayoutDashboard },
    { label: 'Employees', path: '/employees', icon: Users },
    { label: 'Attendance', path: '/attendance', icon: Clock },
    { label: 'Leaves', path: '/leaves', icon: Calendar },
    { label: 'Tasks', path: '/tasks', icon: CheckSquare },
  ];

  // Secondary navigation items (visible on xl+, grouped under "More" on lg)
  const secondaryNavItems = [
    { label: 'Performance', path: '/performance', icon: Award },
    { label: 'Reports', path: '/reports', icon: FileBarChart },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  const adminItems = [
    { label: 'User Management', path: '/admin/users', icon: UserCog },
    { label: 'Audit Trail', path: '/admin/audit-logs', icon: Activity },
    { label: 'System Telemetry', path: '/admin/system', icon: ShieldAlert },
  ];

  const getRoleBadgeColor = (r) => {
    switch (r) {
      case 'ADMIN': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'HR': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      default: return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    }
  };

  const isMoreActive = secondaryNavItems.some(item => location.pathname.startsWith(item.path));

  return (
    <div className="min-h-screen bg-[#0b1120] text-slate-100 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-50 bg-[#0f172a]/95 backdrop-blur-md border-b border-slate-800 shadow-xl">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 gap-3">
            
            {/* Left: Brand Logo & Title */}
            <NavLink 
              to={getDashboardPath()} 
              className="flex items-center gap-2.5 shrink-0 group"
            >
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center shadow-md shadow-blue-500/20 group-hover:scale-105 transition-transform">
                <Award className="w-5 h-5 text-white" />
              </div>
              <div className="flex flex-col">
                <span className="text-base font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent leading-none">
                  ESMS
                </span>
                <span className="hidden sm:block text-[9px] uppercase tracking-wider text-slate-400 font-semibold mt-0.5">
                  Employee Success
                </span>
              </div>
            </NavLink>

            {/* Middle: Desktop Main Navigation Links */}
            <nav className="hidden lg:flex items-center gap-1 min-w-0">
              {/* Primary Tabs */}
              {primaryNavItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname.startsWith(item.path);
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/25'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}

              {/* Secondary Tabs on 2xl / xl+ */}
              <div className="hidden xl:flex items-center gap-1">
                {secondaryNavItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname.startsWith(item.path);
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
                        isActive
                          ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/25'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      <span>{item.label}</span>
                    </NavLink>
                  );
                })}
              </div>

              {/* "More" Dropdown on lg to xl screens */}
              <div className="relative xl:hidden" ref={moreRef}>
                <button
                  type="button"
                  onClick={() => setMoreMenuOpen(!moreMenuOpen)}
                  className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    isMoreActive
                      ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <MoreHorizontal className="w-4 h-4" />
                  <span>More</span>
                  <ChevronDown className="w-3 h-3 opacity-70" />
                </button>

                {moreMenuOpen && (
                  <div className="absolute left-0 mt-2 w-48 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-1.5 z-50 backdrop-blur-xl">
                    {secondaryNavItems.map((item) => {
                      const Icon = item.icon;
                      const isActive = location.pathname.startsWith(item.path);
                      return (
                        <NavLink
                          key={item.path}
                          to={item.path}
                          onClick={() => setMoreMenuOpen(false)}
                          className={`flex items-center gap-2.5 px-3.5 py-2 text-xs font-medium transition-colors ${
                            isActive 
                              ? 'bg-blue-600 text-white' 
                              : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                          }`}
                        >
                          <Icon className="w-4 h-4" />
                          <span>{item.label}</span>
                        </NavLink>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Admin Submenu Dropdown */}
              {role === 'ADMIN' && (
                <div className="relative" ref={adminRef}>
                  <button
                    type="button"
                    onClick={() => setAdminMenuOpen(!adminMenuOpen)}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
                      location.pathname.startsWith('/admin')
                        ? 'bg-rose-600/20 text-rose-300 border border-rose-500/30'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                    }`}
                  >
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                    <span>Administration</span>
                    <ChevronDown className="w-3 h-3 opacity-70" />
                  </button>

                  {adminMenuOpen && (
                    <div className="absolute left-0 mt-2 w-52 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-1.5 z-50 backdrop-blur-xl">
                      {adminItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;
                        return (
                          <NavLink
                            key={item.path}
                            to={item.path}
                            onClick={() => setAdminMenuOpen(false)}
                            className={`flex items-center gap-2.5 px-3.5 py-2 text-xs font-medium transition-colors ${
                              isActive 
                                ? 'bg-rose-500/15 text-rose-300' 
                                : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                            }`}
                          >
                            <Icon className="w-4 h-4 text-rose-400" />
                            <span>{item.label}</span>
                          </NavLink>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </nav>

            {/* Right: Notifications, User Profile & Logout */}
            <div className="flex items-center gap-2 sm:gap-3 shrink-0">
              {/* Notification Bell Widget */}
              <div className="flex items-center">
                <NotificationBell />
              </div>

              {/* User Identity Pill */}
              <div className="hidden sm:flex items-center gap-2 pl-2.5 border-l border-slate-800">
                <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-blue-400">
                  {user?.email?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div className="flex flex-col text-left">
                  <span className="text-xs font-semibold text-slate-200 max-w-[110px] xl:max-w-[140px] truncate leading-tight">
                    {user?.email}
                  </span>
                  <span className={`text-[9px] font-semibold px-1 py-0.2 rounded border w-fit leading-none mt-0.5 ${getRoleBadgeColor(role)}`}>
                    {role || 'USER'}
                  </span>
                </div>
              </div>

              {/* Logout Button */}
              <button
                type="button"
                onClick={logout}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-slate-800 hover:border-rose-500/20 transition-all"
                title="Logout"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden md:inline">Logout</span>
              </button>

              {/* Mobile Menu Toggle */}
              <button
                type="button"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>

          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="lg:hidden bg-slate-900 border-b border-slate-800 px-4 pt-2 pb-4 space-y-1">
            {[...primaryNavItems, ...secondaryNavItems].map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.path);
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium ${
                    isActive 
                      ? 'bg-blue-600 text-white' 
                      : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}

            {role === 'ADMIN' && (
              <div className="pt-2 border-t border-slate-800 mt-2 space-y-1">
                <div className="px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Administration
                </div>
                {adminItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white"
                    >
                      <Icon className="w-4 h-4 text-rose-400" />
                      <span>{item.label}</span>
                    </NavLink>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </header>

      {/* Main Page Content Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {children}
      </main>

      {/* Professional Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0c1222] py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Employee Success Management System (ESMS) &bull; Enterprise Edition</span>
          <span>Status: <strong className="text-emerald-400 font-medium">Operational</strong> &bull; v1.0.0</span>
        </div>
      </footer>
    </div>
  );
}
