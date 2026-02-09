import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { Dashboard } from "@/components/Dashboard";
import AuthPage from '@/pages/AuthPage';
import PortfolioPage from '@/pages/PortfolioPage';
import { ComparePage } from '@/pages/ComparePage';
import PerformancePage from '@/pages/PerformancePage'; // Added
import { Loader2 } from 'lucide-react';

const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
        <div className="h-screen w-screen flex items-center justify-center bg-background">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  return children;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="relative min-h-screen bg-background text-foreground antialiased selection:bg-primary/20 selection:text-primary overflow-hidden">
          {/* Dynamic Background Effects */}
          <div className="fixed inset-0 z-0 pointer-events-none">
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary/5 blur-[120px] animate-pulse-glow" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-secondary/5 blur-[120px] animate-pulse-glow" style={{ animationDelay: "1.5s" }} />
            <div className="absolute top-[20%] right-[10%] w-[20%] h-[20%] rounded-full bg-accent/5 blur-[80px] animate-float" />
          </div>

          {/* Grid Pattern Overlay */}
          <div className="fixed inset-0 z-0 pointer-events-none opacity-[0.03]" 
               style={{ backgroundImage: `radial-gradient(circle at 1px 1px, white 1px, transparent 0)`, backgroundSize: '24px 24px' }} 
          />

          <div className="relative z-10">
            <Routes>
                <Route path="/auth" element={<AuthPage />} />
                <Route path="/" element={
                    <ProtectedRoute>
                        <Dashboard />
                    </ProtectedRoute>
                } />
                <Route path="/portfolio" element={
                    <ProtectedRoute>
                        <PortfolioPage />
                    </ProtectedRoute>
                } />
                <Route path="/compare" element={
                    <ProtectedRoute>
                        <ComparePage />
                    </ProtectedRoute>
                } />
                <Route path="/performance" element={
                    <ProtectedRoute>
                        <PerformancePage />
                    </ProtectedRoute>
                } />
            </Routes>
          </div>
        </div>
      </Router>
                <Route path="/performance" element={
                    <ProtectedRoute>
                        <PerformancePage />
                    </ProtectedRoute>
                } />
            </Routes>
          </div>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
