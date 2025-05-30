// Shared error handling utilities
// Note: toast notification functions should be provided by the consuming module

export interface ToastNotifier {
  error: (message: string) => void;
  success?: (message: string) => void;
  info?: (message: string) => void;
}

// Default console-only notifier
const defaultNotifier: ToastNotifier = {
  error: (message: string) => console.error(message),
  success: (message: string) => console.log(message),
  info: (message: string) => console.info(message)
};

/**
 * Generic async error handler with optional default value and custom error handler
 * Factory function that takes toast dependency
 */
export const createAsyncErrorHandler = (toast: ToastNotifier) => async <T>(
  fn: () => Promise<T>,
  defaultValue?: T,
  errorHandler?: (error: Error) => void
): Promise<T | undefined> => {
  try {
    return await fn();
  } catch (error) {
    if (errorHandler) {
      errorHandler(error as Error);
    } else {
      console.error(error);
      toast.error((error as Error).message);
    }
    return defaultValue;
  }
};

/**
 * Creates a contextual error handler for consistent error reporting
 * Factory function that takes toast dependency
 */
export const createErrorHandlerFactory = (toast: ToastNotifier) => (context: string) => (error: Error) => {
  console.error(`[${context}]`, error);
  toast.error(`${context}: ${error.message}`);
};

/**
 * Backward compatible functions for existing code
 */
export const handleAsyncError = createAsyncErrorHandler(defaultNotifier);
export const createErrorHandler = createErrorHandlerFactory(defaultNotifier);

/**
 * Simplified error handler for sync operations
 */
export const handleError = (error: Error, context?: string, notifier: ToastNotifier = defaultNotifier): void => {
  const message = context ? `${context}: ${error.message}` : error.message;
  console.error(context ? `[${context}]` : '', error);
  notifier.error(message);
};

/**
 * Promise wrapper that automatically handles errors with toast notifications
 */
export const withErrorHandling = async <T>(
  promise: Promise<T>,
  context?: string,
  defaultValue?: T
): Promise<T | undefined> => {
  try {
    return await promise;
  } catch (error) {
    handleError(error as Error, context);
    return defaultValue;
  }
};

/**
 * Higher-order function that wraps async functions with error handling
 */
export const withAsyncErrorHandling = <TArgs extends any[], TReturn>(
  fn: (...args: TArgs) => Promise<TReturn>,
  context?: string
) => {
  return async (...args: TArgs): Promise<TReturn | undefined> => {
    try {
      return await fn(...args);
    } catch (error) {
      handleError(error as Error, context);
      return undefined;
    }
  };
};