import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, LayoutDashboard, LogOut, Home, Lock } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function UnauthorizedPage() {
  const navigate = useNavigate();
  const { user, logout, role } = useAuth();

  const getDashboardPath = () => {
    switch (role || user?.role) {
      case 'ADMIN':
        return '/dashboard/admin';
      case 'HR':
        return '/dashboard/hr';
      case 'EMPLOYEE':
      default:
        return '/dashboard/employee';
    }
  };

  const getDashboardLabel = () => {
    switch (role || user?.role) {
      case 'ADMIN':
        return 'Admin Dashboard';
      case 'HR':
        return 'HR Dashboard';
      case 'EMPLOYEE':
      default:
        return 'Employee Dashboard';
    }
  };

  const handleSafeBack = () => {
    // If user has history, check if navigating back is safe or falls back to dashboard
    if (window.history.length > 2) {
      navigate(-1);
    } else {
      navigate(getDashboardPath(), { replace: true });
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1120] flex items-center justify-center p-4 sm:p-6 text-slate-100 font-sans">
      <div className="max-w-md w-full bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl text-center space-y-6">
        
        {/* Shield Icon Badge */}
        <div className="inline-flex items-center justify-center p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 shadow-lg shadow-rose-500/10">
          <ShieldAlert className="w-10 h-10" />
        </div>

        {/* Title and Explanation */}
        <div className="space-y-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded-full border border-rose-500/20">
            HTTP 403 Forbidden
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-white pt-1">
            Access Restricted
          </h1>
          <p className="text-sm text-slate-400 leading-relaxed">
            You do not have the required security clearances to access this resource. This area is reserved for specific administrative roles.
          </p>
        </div>

        {/* User Identity Pill */}
        <div className="p-3.5 bg-slate-950/70 border border-slate-800 rounded-2xl flex items-center justify-between text-xs text-left">
          <div className="flex items-center gap-2.5 truncate">
            <div className="w-8 h-8 rounded-xl bg-slate-800 flex items-center justify-center text-slate-300 font-bold shrink-0">
              {user?.email?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="truncate">
              <div className="font-semibold text-slate-200 truncate">{user?.email || 'Authenticated User'}</div>
              <div className="text-[11px] text-slate-500">Active Session</div>
            </div>
          </div>
          <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0">
            {user?.role || 'GUEST'}
          </span>
        </div>

        {/* Actions */}
        <div className="space-y-3 pt-2">
          {/* Primary Action: Go to the user's role dashboard */}
          <Link
            to={getDashboardPath()}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm transition-all shadow-lg shadow-blue-600/25 group"
          >
            <LayoutDashboard className="w-4 h-4 group-hover:scale-110 transition-transform" />
            <span>Return to {getDashboardLabel()}</span>
          </Link>

          <div className="grid grid-cols-2 gap-2.5">
            {/* Safe Back / Homepage */}
            <button
              onClick={handleSafeBack}
              type="button"
              className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium border border-slate-700 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Go Back</span>
            </button>

            {/* Logout / Switch Account */}
            <button
              onClick={logout}
              type="button"
              className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 text-xs font-medium border border-rose-500/20 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Switch Account</span>
            </button>
          </div>
        </div>

        {/* Footer Note */}
        <p className="text-[11px] text-slate-500 pt-2 border-t border-slate-800/80">
          Need higher access? Contact your system administrator to elevate your role in User Administration.
        </p>

      </div>
    </div>
  );
}

