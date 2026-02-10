import type { ReactElement } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { Dashboard } from "@/components/Dashboard";
import AuthPage from '@/pages/AuthPage';
import PortfolioPage from '@/pages/PortfolioPage';
import { ComparePage } from '@/pages/ComparePage';
import PerformancePage from '@/pages/PerformancePage';
import AlertsPage from '@/pages/AlertsPage';
import SchedulesPage from '@/pages/SchedulesPage';
import SettingsPage from '@/pages/SettingsPage';
import AppLayout from '@/components/layout/AppLayout';
import { Loader2 } from 'lucide-react';

const ProtectedRoute = ({ children }: { children: ReactElement }) => {
  const { token, isLoading } = useAuth();

  if (isLoading) {
    return (
        <div className="h-screen w-screen flex items-center justify-center bg-background">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
    );
  }

  // Check for token instead of user to avoid race condition during login
  if (!token) {
    return <Navigate to="/auth" replace />;
  }

  return children;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Auth page - no layout */}
          <Route path="/auth" element={<AuthPage />} />

          {/* Authenticated routes - use AppLayout */}
          <Route element={<AppLayout />}>
            <Route path="/" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/compare" element={
              <ProtectedRoute>
                <ComparePage />
              </ProtectedRoute>
            } />
            <Route path="/portfolio" element={
              <ProtectedRoute>
                <PortfolioPage />
              </ProtectedRoute>
            } />
            <Route path="/performance" element={
              <ProtectedRoute>
                <PerformancePage />
              </ProtectedRoute>
            } />
            <Route path="/alerts" element={
              <ProtectedRoute>
                <AlertsPage />
              </ProtectedRoute>
            } />
            <Route path="/schedules" element={
              <ProtectedRoute>
                <SchedulesPage />
              </ProtectedRoute>
            } />
            <Route path="/settings" element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            } />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
