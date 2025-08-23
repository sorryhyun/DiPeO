import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import Input from '../../../shared/components/Input';
import Button from '../../../shared/components/Button';
import { useAuth } from '../../../shared/hooks/useAuth';

/**
 * LoginForm Component
 * - Controlled form for user login
 * - Uses Zod for validation and react-hook-form for state management
 * - Integrates with AuthContext via useAuth
 * - Inline validation errors and a top-level authentication error banner
 * - Persists last-used email to localStorage in development mode
 */
type SignInFormInputs = z.infer<typeof SignInSchema>;

const SignInSchema = z.object({
  email: z.string().email({ message: 'Please enter a valid email address' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters' }),
});

const LAST_EMAIL_KEY = 'lastUsedEmail';

const LoginForm: React.FC = () => {
  const { signIn } = useAuth();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<SignInFormInputs>({
    resolver: zodResolver(SignInSchema),
    defaultValues: {
      email: '',
      password: '',
    },
    mode: 'onSubmit',
  });

  const [authError, setAuthError] = useState<string | null>(null);

  // Prefill email from localStorage if available (dev convenience)
  useEffect(() => {
    try {
      const savedEmail =
        typeof window !== 'undefined' ? window.localStorage.getItem(LAST_EMAIL_KEY) : null;
      if (savedEmail && savedEmail.length > 0) {
        reset({ email: savedEmail, password: '' });
      }
    } catch {
      // ignore localStorage errors
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reset]);

  const onSubmit = async (values: SignInFormInputs) => {
    setAuthError(null);
    try {
      await signIn(values.email, values.password);
      // Persist last used email in development for convenience
      if (process.env.NODE_ENV === 'development') {
        try {
          if (typeof window !== 'undefined' && window.localStorage) {
            window.localStorage.setItem(LAST_EMAIL_KEY, values.email);
          }
        } catch {
          // ignore localStorage write errors
        }
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Login failed. Please check your credentials.';
      setAuthError(message);
    }
  };

  return (
    <section aria-labelledby="login-form-title" className="w-full max-w-md mx-auto p-4">
      <h2 id="login-form-title" className="text-xl font-semibold mb-4">
        Sign in
      </h2>

      {authError && (
        <div role="alert" aria-live="assertive" className="mb-4">
          <div className="bg-red-50 border border-red-200 text-red-800 p-3 rounded" aria-label="Authentication error">
            <span className="block font-medium">{authError}</span>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        <Input
          id="email"
          label="Email"
          type="email"
          placeholder="name@example.com"
          autoComplete="username"
          aria-invalid={Boolean(errors.email)}
          error={errors.email?.message}
          {...register('email')}
        />

        <Input
          id="password"
          label="Password"
          type="password"
          placeholder="••••••••"
          autoComplete="current-password"
          aria-invalid={Boolean(errors.password)}
          error={errors.password?.message}
          {...register('password')}
        />

        <Button type="submit" disabled={isSubmitting} className="w-full">
          {isSubmitting ? (
            <span className="inline-flex items-center">
              <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent border-l-transparent rounded-full animate-spin" aria-label="loading" role="status" />
              <span className="ml-2">Signing in…</span>
            </span>
          ) : (
            'Sign in'
          )}
        </Button>
      </form>
    </section>
  );
};

export default LoginForm;