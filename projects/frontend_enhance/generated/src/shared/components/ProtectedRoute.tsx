import React, { Suspense } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import ErrorBoundary from './ErrorBoundary';
import SuspenseFallback from './SuspenseFallback';

type ProtectedRouteProps = {
  children?: React.ReactNode;
  element?: React.ReactElement;
  requiredRole?: string;
};

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  element,
  requiredRole,
}) => {
  const location = useLocation();
  const { isAuthenticated, hasRole } = useAuth();

  // If user is not authenticated, redirect to login and preserve the intended destination
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If a specific role is required but the user does not have it, render an accessible 403 message
  if (requiredRole && !hasRole(requiredRole)) {
    return (
      <div aria-label="Access denied" role="alert" className="p-4">
        <div
          tabIndex={0}
          className="bg-red-50 border border-red-200 text-red-800 p-4 rounded"
        >
          <strong className="block mb-1">Access denied</strong>
          <span>You do not have permission to view this content.</span>
        </div>
      </div>
    );
  }

  // Content to render: prefer explicit element prop if provided, otherwise render children
  const content = element ?? children ?? null;

  return (
    <Suspense fallback={<SuspenseFallback />}>
      <ErrorBoundary>{content}</ErrorBoundary>
    </Suspense>
  );
};

export default ProtectedRoute;