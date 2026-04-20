import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import DashboardLayout from './layouts/DashboardLayout';
import EntryDashboardDemoPage from './pages/CallManagementDemoPage.tsx';
import TwilioCallManagementPage from './pages/TwilioCallManagementPage.tsx';
import TwilioDatabasePage from './pages/TwilioDatabasePage.tsx';
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
      { path: 'twilio-call-management', element: <TwilioCallManagementPage /> },
      { path: 'twilio-database', element: <TwilioDatabasePage /> },
      { path: 'entry-dashboard-demo', element: <EntryDashboardDemoPage /> },
      { path: 'admin-dashboard', element: <SystemHealthPage /> },
      { path: 'call-status-dashboard', element: <MetricsPage /> },
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
