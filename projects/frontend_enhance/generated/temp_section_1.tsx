import React, { useEffect, useMemo } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

type ProtectedRouteProps = {
  children: React.ReactNode;
};

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const location = useLocation();

  const isAuthenticated = useMemo(() => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return false;

      const parts = token.split('.');
      if (parts.length >= 2) {
        const payloadBase64 = parts[1];
        const payloadJson = typeof atob === 'function' ? JSON.parse(atob(payloadBase64)) : null;
        if (payloadJson && typeof payloadJson.exp === 'number') {
          const exp = payloadJson.exp;
          const now = Math.floor(Date.now() / 1000);
          return exp > now;
        }
      }
      // If token exists but no exp, assume it's valid
      return true;
    } catch {
      return false;
    }
  }, []);

  useEffect(() => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      const parts = token.split('.');
      if (parts.length >= 2) {
        const payloadJson = typeof atob === 'function' ? JSON.parse(atob(parts[1])) : null;
        if (payloadJson && typeof payloadJson.exp === 'number') {
          const exp = payloadJson.exp;
          const now = Math.floor(Date.now() / 1000);
          const diff = exp - now;
          const nearExpiryThreshold = 300; // 5 minutes
          if (diff < nearExpiryThreshold && typeof (window as any).refreshAuthToken === 'function') {
            (window as any).refreshAuthToken();
          }
        }
      }
    } catch {
      // ignore refresh errors
    }
  }, []);

  if (!isAuthenticated) {
    // Accessible live region to announce redirect
    return (
      <>
        <div
          aria-live="polite"
          aria-atomic="true"
          style={{
            position: 'absolute',
            width: 1,
            height: 1,
            marginLeft: '-1px',
            overflow: 'hidden',
            clip: 'rect(0 0 0 0)',
            whiteSpace: 'nowrap',
          }}
        >
          Redirecting to Sign In
        </div>
        <Navigate to="/signin" replace state={{ from: location }} />
      </>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;