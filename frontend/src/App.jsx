import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './routes/ProtectedRoute';
import LoginPage from './pages/auth/LoginPage';
import UnauthorizedPage from './pages/auth/UnauthorizedPage';
import AdminDashboard from './pages/dashboard/AdminDashboard';
import HRDashboard from './pages/dashboard/HRDashboard';
import EmployeeDashboard from './pages/dashboard/EmployeeDashboard';
import EmployeeDirectoryPage from './pages/employees/EmployeeDirectoryPage';
import AttendanceManagementPage from './pages/attendance/AttendanceManagementPage';
import LeaveManagementPage from './pages/leaves/LeaveManagementPage';
import TaskManagementPage from './pages/tasks/TaskManagementPage';
import PerformanceManagementPage from './pages/performance/PerformanceManagementPage';
import ReportsPage from './pages/reports/ReportsPage';
import NotificationPage from './pages/notifications/NotificationPage';
import SettingsPage from './pages/settings/SettingsPage';
import UserManagementPage from './pages/admin/UserManagementPage';
import AuditLogPage from './pages/admin/AuditLogPage';
import SystemAdminPage from './pages/admin/SystemAdminPage';

// Helper component to redirect authenticated users to their respective role dashboard
function RootRedirect() {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        color: 'var(--text-secondary)'
      }}>
        Loading ESMS Platform...
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  switch (user.role) {
    case 'ADMIN':
      return <Navigate to="/dashboard/admin" replace />;
    case 'HR':
      return <Navigate to="/dashboard/hr" replace />;
    case 'EMPLOYEE':
    default:
      return <Navigate to="/dashboard/employee" replace />;
  }
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />

          {/* Root Redirect */}
          <Route path="/" element={<RootRedirect />} />

          {/* Protected Role Routes */}
          <Route
            path="/dashboard/admin"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/hr"
            element={
              <ProtectedRoute allowedRoles={['HR', 'ADMIN']}>
                <HRDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/dashboard/employee"
            element={
              <ProtectedRoute allowedRoles={['EMPLOYEE', 'HR', 'ADMIN']}>
                <EmployeeDashboard />
              </ProtectedRoute>
            }
          />

          {/* Module 1: Employee Management Directory */}
          <Route
            path="/employees"
            element={
              <ProtectedRoute allowedRoles={['EMPLOYEE', 'HR', 'ADMIN']}>
                <EmployeeDirectoryPage />
              </ProtectedRoute>
            }
          />

          {/* Module 2: Attendance Management */}
          <Route
            path="/attendance"
            element={
              <ProtectedRoute allowedRoles={['EMPLOYEE', 'HR', 'ADMIN']}>
                <AttendanceManagementPage />
              </ProtectedRoute>
            }
          />

          {/* Module 3: Leave Management */}
          <Route
            path="/leaves"
            element={
              <ProtectedRoute allowedRoles={['EMPLOYEE', 'HR', 'ADMIN']}>
                <LeaveManagementPage />
              </ProtectedRoute>
            }
          />

          {/* Module 4: Task Management */}
          <Route
            path="/tasks"
            element={
              <ProtectedRoute allowedRoles={['EMPLOYEE', 'HR', 'ADMIN']}>
                <TaskManagementPage />
              </ProtectedRoute>
            }
          />

          {/* Module 5: Performance Management */}
          <Route
            path="/performance"
            element={
              <ProtectedRoute allowedRoles={['EMPLOYEE', 'HR', 'ADMIN']}>
                <PerformanceManagementPage />
              </ProtectedRoute>
            }
          />

          {/* Module 7: Reports & Export Management */}
          <Route
            path="/reports"
            element={
              <ProtectedRoute allowedRoles={['EMPLOYEE', 'HR', 'ADMIN']}>
                <ReportsPage />
              </ProtectedRoute>
            }
          />

          {/* Module 8: Notifications & Reminders */}
          <Route
            path="/notifications"
            element={
              <ProtectedRoute allowedRoles={['EMPLOYEE', 'HR', 'ADMIN']}>
                <NotificationPage />
              </ProtectedRoute>
            }
          />

          {/* Module 9 / Phase 8: Settings & Organization Management */}
          <Route
            path="/settings"
            element={
              <ProtectedRoute allowedRoles={['EMPLOYEE', 'HR', 'ADMIN']}>
                <SettingsPage />
              </ProtectedRoute>
            }
          />

          {/* Phase 9: Security & System Administration */}
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <UserManagementPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/audit-logs"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <AuditLogPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/system"
            element={
              <ProtectedRoute allowedRoles={['ADMIN']}>
                <SystemAdminPage />
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
