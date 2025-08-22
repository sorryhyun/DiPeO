import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { login } from 'src/shared/utils/api';
import { useAuth } from 'src/features/auth/hooks/useAuthProvider';

type LoginResponse = {
  token?: string;
  // other fields can exist but are not relied upon here
};

function isTokenNearExpiry(token: string, minutes: number = 5): boolean {
  try {
    const parts = token.split('.');
    if (parts.length < 2) return false;
    const payload = JSON.parse(
      decodeBase64Url(parts[1])
    );
    const exp = payload?.exp;
    if (typeof exp !== 'number') return false;
    const now = Math.floor(Date.now() / 1000);
    return exp - now <= minutes * 60;
  } catch {
    return false;
  }
}

function decodeBase64Url(str: string): string {
  // Convert base64url to base64
  const base64 = str.replace(/-/g, '+').replace(/_/g, '/');
  // Pad string
  const padding = '='.repeat((4 - (base64.length % 4)) % 4);
  const base64Padded = base64 + padding;
  // Decode
  if (typeof window !== 'undefined' && typeof window.atob === 'function') {
    return window.atob(base64Padded);
  }
  // Fallback (shouldn't happen in browsers)
  return atob(base64Padded);
}

const SignIn: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const authContext: any = useAuth ? (useAuth() as any) : null;

  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [emailError, setEmailError] = useState<string | undefined>();
  const [passwordError, setPasswordError] = useState<string | undefined>();
  const [formError, setFormError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const emailRef = useRef<HTMLInputElement | null>(null);

  // Redirect target after login
  const fromPath = (location.state as any)?.from?.pathname || '/dashboard';

  useEffect(() => {
    emailRef.current?.focus();
  }, []);

  // Basic client-side validation
  const validate = (): boolean => {
    let valid = true;

    if (!email) {
      setEmailError('Email is required.');
      valid = false;
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailError('Please enter a valid email address.');
      valid = false;
    } else {
      setEmailError(undefined);
    }

    if (!password) {
      setPasswordError('Password is required.');
      valid = false;
    } else if (password.length < 6) {
      setPasswordError('Password must be at least 6 characters.');
      valid = false;
    } else {
      setPasswordError(undefined);
    }

    return valid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!validate()) {
      return;
    }

    setLoading(true);
    try {
      const res: LoginResponse = await login({ email, password });
      const token = res?.token;

      if (token) {
        // Persist token (fallback to localStorage; HttpOnly is preferable server-side)
        try {
          localStorage.setItem('token', token);
        } catch {
          // ignore if storage not available
        }

        // If an auth context exists, update it
        if (authContext && typeof authContext.setToken === 'function') {
          try {
            authContext.setToken(token);
          } catch {
            // ignore update errors
          }
        }

        // Optional: refresh token if expiry is near (best-effort, no hard dependency)
        try {
          if (token && isTokenNearExpiry(token) && authContext && typeof authContext.refreshToken === 'function') {
            await authContext.refreshToken();
          }
        } catch {
          // ignore refresh errors but token remains usable
        }

        // Redirect to intended path
        navigate(fromPath, { replace: true });
      } else {
        setFormError('Login failed. Please check your credentials.');
      }
    } catch (err: any) {
      const message =
        typeof err?.message === 'string'
          ? err.message
          : 'Login failed. Please check your credentials.';
      setFormError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <section
        aria-label="Sign in form"
        className="w-full max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 sm:p-8"
      >
        <h1 className="text-2xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
          Sign in
        </h1>

        {formError && (
          <div
            role="alert"
            aria-live="assertive"
            className="mb-4 p-3 rounded border border-red-400 bg-red-50 text-red-700"
          >
            {formError}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="mb-4">
            <label
              htmlFor="signin-email"
              className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1"
            >
              Email
            </label>
            <input
              id="signin-email"
              ref={emailRef}
              name="email"
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-invalid={Boolean(emailError)}
              aria-describedby={emailError ? 'signin-email-error' : undefined}
              className={`block w-full px-3 py-2 border rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 ${
                emailError ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {emailError && (
              <p id="signin-email-error" className="mt-2 text-sm text-red-600" role="alert">
                {emailError}
              </p>
            )}
          </div>

          <div className="mb-6">
            <label
              htmlFor="signin-password"
              className="block text-sm font-medium text-gray-700 dark:text-gray-200 mb-1"
            >
              Password
            </label>
            <input
              id="signin-password"
              name="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              aria-invalid={Boolean(passwordError)}
              aria-describedby={passwordError ? 'signin-password-error' : undefined}
              className={`block w-full px-3 py-2 border rounded-md bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 ${
                passwordError ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {passwordError && (
              <p id="signin-password-error" className="mt-2 text-sm text-red-600" role="alert">
                {passwordError}
              </p>
            )}
          </div>

          <button
            type="submit"
            className="w-full py-2 px-4 rounded-md bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 disabled:opacity-60"
            disabled={loading}
            aria-label="Sign in"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <p className="mt-4 text-sm text-gray-600">
          Don’t have an account?{' '}
          <Link to="/signup" className="text-blue-600 hover:underline">
            Create one
          </Link>
        </p>

        <div aria-live="polite" className="sr-only" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden' }}>
          {loading ? 'Signing in in progress' : ''}
        </div>
      </section>
    </div>
  );
};

export default SignIn;