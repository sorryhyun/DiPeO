import React from "react";

type Props = { children: React.ReactNode; fallback?: React.ReactNode; onRetry?: () => void };

type State = { hasError: boolean; error?: Error };

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Basic logging for observability
    console.error("[DataListErrorBoundary]", error, info);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
    this.props.onRetry?.();
  };

  render() {
    const { children, fallback } = this.props;
    if (this.state.hasError) {
      return (
        <div role="alert" aria-label="Error">
          {fallback ?? (
            <div className="p-4 text-sm text-red-600">
              Something went wrong. <button onClick={this.handleRetry}>Retry</button>
            </div>
          )}
        </div>
      );
    }
    return <>{children}</>;
  }
}