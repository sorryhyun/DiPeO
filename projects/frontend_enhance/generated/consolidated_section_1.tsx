import React, { Component, ReactNode } from 'react';

type ErrorBoundaryProps = {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
  className?: string;
  testId?: string;
};

type ErrorBoundaryState = {
  hasError: boolean;
  error?: Error;
  info?: string;
};

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: undefined,
      info: undefined,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render shows the fallback UI.
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // You can log the error to an error reporting service
    // eslint-disable-next-line no-console
    console.error('Uncaught error:', error, info);
    this.setState({ info: info.componentStack });
  }

  handleReset = () => {
    const { onReset } = this.props;
    this.setState({ hasError: false, error: undefined, info: undefined });
    if (typeof onReset === 'function') {
      onReset();
    }
  };

  render() {
    const { children, fallback, className = '', testId } = this.props;
    const { hasError, error, info } = this.state;

    if (!hasError) {
      return (
        <div className={className} data-testid={testId ?? 'error-boundary'}>
          {children}
        </div>
      );
    }

    // Render custom fallback if provided
    if (fallback) {
      return (
        <div className={`error-boundary ${className}`.trim()} data-testid={testId ?? 'error-boundary'}>
          {fallback}
          <button type="button" className="btn btn--primary" onClick={this.handleReset}>
            Try again
          </button>
        </div>
      );
    }

    // Default fallback UI
    return (
      <div className={`error-boundary ${className}`.trim()} data-testid={testId ?? 'error-boundary'}>
        <div role="alert" aria-live="polite" className="error-boundary__message">
          <strong>Something went wrong.</strong>
          {error && (
            <div className="error-boundary__details" aria-label="error-details">
              {error.message}
            </div>
          )}
          {info && (
            <details className="error-boundary__details" aria-label="error-info">
              <summary>Stack trace</summary>
              <pre>{info}</pre>
            </details>
          )}
        </div>
        <button type="button" className="btn btn--primary" onClick={this.handleReset}>
          Retry
        </button>
      </div>
    );
  }
}

export default ErrorBoundary;