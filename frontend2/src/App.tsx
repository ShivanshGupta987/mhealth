import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardLayout from './layouts/DashboardLayout';
import DatabaseManagementPage from './pages/DatabaseManagementPage';
import EntryDashboardDemoPage from './pages/CallManagementDemoPage.tsx';
import EntryDashboardPage from './pages/CallManagementPage.tsx';
import SystemHealthPage from './pages/SystemHealthPage.tsx';
import MetricsPage from './pages/CallStatusDashboard.tsx';
import LoginPage from './pages/LoginPage';
import AboutPage from './pages/AboutPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordWithTokenPage from './pages/ResetPasswordWithTokenPage';

const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/forgot-password',
    element: <ForgotPasswordPage />,
  },
  {
    path: '/reset-password/:token',
    element: <ResetPasswordWithTokenPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <AboutPage /> },
      { path: 'database', element: <DatabaseManagementPage /> },
      { path: 'entry-dashboard', element: <EntryDashboardPage /> },
      { path: 'entry-dashboard-demo', element: <EntryDashboardDemoPage /> },
      { path: 'system-health', element: <SystemHealthPage /> },
      { path: 'metrics', element: <MetricsPage /> },
      { path: 'reset-password', element: <ResetPasswordPage /> },
    ],
  },
]);

export default function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}
