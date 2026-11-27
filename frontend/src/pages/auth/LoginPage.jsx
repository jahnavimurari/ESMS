import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ShieldCheck, Lock, Mail, AlertCircle, ArrowRight } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError('Please provide both email and password.');
      return;
    }

    setSubmitting(true);
    try {
      const user = await login(email, password);
      const role = user?.role || 'EMPLOYEE';
      const from = location.state?.from?.pathname;

      const getRoleDashboard = (r) => {
        switch (r) {
          case 'ADMIN': return '/dashboard/admin';
          case 'HR': return '/dashboard/hr';
          case 'EMPLOYEE':
          default: return '/dashboard/employee';
        }
      };

      const isPathAllowedForRole = (targetPath, userRole) => {
        if (!targetPath || targetPath === '/login' || targetPath === '/unauthorized') return false;
        if (targetPath.startsWith('/admin') || targetPath === '/dashboard/admin') {
          return userRole === 'ADMIN';
        }
        if (targetPath === '/dashboard/hr') {
          return userRole === 'HR' || userRole === 'ADMIN';
        }
        if (targetPath === '/dashboard/employee') {
          return true;
        }
        // General common modules: /attendance, /leaves, /tasks, /performance, /reports, /settings, /employees
        return true;
      };

      if (from && isPathAllowedForRole(from, role)) {
        navigate(from, { replace: true });
      } else {
        navigate(getRoleDashboard(role), { replace: true });
      }
    } catch (err) {
      const msg = err.response?.data?.error?.message || err.message || 'Authentication failed.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem',
      backgroundColor: 'var(--bg-app)'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '420px',
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-lg)',
        padding: '2.25rem',
        boxShadow: 'var(--shadow-lg)'
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            padding: '0.875rem',
            borderRadius: '9999px',
            marginBottom: '1rem'
          }}>
            <ShieldCheck size={36} color="var(--primary)" />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: '0.375rem' }}>
            ESMS Portal
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            Employee Success Management System
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.625rem',
            backgroundColor: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem 1rem',
            marginBottom: '1.5rem',
            color: 'var(--danger)',
            fontSize: '0.875rem'
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem', color: 'var(--text-primary)' }}>
              Work Email
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                required
                style={{
                  width: '100%',
                  padding: '0.625rem 0.875rem 0.625rem 2.625rem',
                  backgroundColor: 'var(--bg-app)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem',
                  outline: 'none'
                }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1.75rem' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 500, marginBottom: '0.375rem', color: 'var(--text-primary)' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: '100%',
                  padding: '0.625rem 0.875rem 0.625rem 2.625rem',
                  backgroundColor: 'var(--bg-app)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--text-primary)',
                  fontSize: '0.875rem',
                  outline: 'none'
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              backgroundColor: 'var(--primary)',
              color: '#ffffff',
              padding: '0.75rem',
              borderRadius: 'var(--radius-md)',
              fontWeight: 600,
              fontSize: '0.875rem',
              border: 'none',
              cursor: submitting ? 'not-allowed' : 'pointer',
              opacity: submitting ? 0.7 : 1,
              transition: 'background 0.15s ease'
            }}
          >
            {submitting ? 'Authenticating...' : 'Sign In'}
            <ArrowRight size={16} />
          </button>
        </form>

        {/* Security Notice */}
        <p style={{ marginTop: '1.75rem', textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Protected by JWT authentication and Neon PostgreSQL security policies.
        </p>
      </div>
    </div>
  );
}

