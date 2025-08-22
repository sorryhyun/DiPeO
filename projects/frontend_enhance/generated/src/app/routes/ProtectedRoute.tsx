import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../features/auth/hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, user, refreshToken, isTokenNearExpiry } = useAuth();
  const location = useLocation();

  // Auto-refresh token if near expiry when accessing protected route
  useEffect(() => {
    if (isAuthenticated && isTokenNearExpiry() && refreshToken) {
      refreshToken().catch((error) => {
        console.warn('Token refresh failed:', error);
      });
    }
  }, [isAuthenticated, isTokenNearExpiry, refreshToken, location.pathname]);

  // Redirect to signin if not authenticated, preserving intended destination
  if (!isAuthenticated || !user) {
    return (
      <Navigate
        to="/signin"
        replace
        state={{ from: location }}
      />
    );
  }

  // Render protected content
  return <>{children}</>;
};

export default ProtectedRoute;