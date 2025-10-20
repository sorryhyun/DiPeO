/**
 * Error Boundary Component
 *
 * Catches React errors and displays a fallback UI with recovery option
 */

import React, { Component, ReactNode } from 'react';
import { WidgetLayout } from './WidgetLayout';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Widget error:', error, errorInfo);
  }

  resetError = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <WidgetLayout error={this.state.error}>
          <div className="text-center space-y-3">
            <div className="text-sm text-gray-600">
              The widget encountered an error and could not render.
            </div>
            <button
              onClick={this.resetError}
              className="px-4 py-2 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
            >
              Try Again
            </button>
          </div>
        </WidgetLayout>
      );
    }

    return this.props.children;
  }
}
