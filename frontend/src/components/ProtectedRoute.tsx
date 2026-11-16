import type { ReactNode, FC } from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { ShieldCheck, Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children?: ReactNode;
}

export const ProtectedRoute: FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-ink-base flex flex-col items-center justify-center gap-4 text-gray-200">
        <div className="flex items-center justify-center w-14 h-14 rounded-xl bg-brand/20 border border-brand/50 shadow-lg shadow-brand/10 animate-pulse">
          <ShieldCheck size={32} className="text-brand" />
        </div>
        <div className="flex items-center gap-2 text-sm font-semibold tracking-wide text-gray-300">
          <Loader2 size={18} className="animate-spin text-brand" />
          <span>Verifying Forensic Session...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute;
