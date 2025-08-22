import React, { useState, useCallback, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '../../../shared/components/Button';
import { Card } from '../../../shared/components/Card';
import { useAuth } from '../hooks/useAuth';
import { logger } from '../../../shared/utils/logger';

interface FormData {
  email: string;
  password: string;
}

interface FormErrors {
  email?: string;
  password?: string;
  general?: string;
}


export const SignIn: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  
  const [formData, setFormData] = useState<FormData>({
    email: '',
    password: ''
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [touched, setTouched] = useState<Record<keyof FormData, boolean>>({
    email: false,
    password: false
  });

  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const errorRef = useRef<HTMLDivElement>(null);

  const validateEmail = useCallback((email: string): string | undefined => {
    if (!email) {
      return t('auth.validation.emailRequired', 'Email is required');
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return t('auth.validation.emailInvalid', 'Please enter a valid email address');
    }
    return undefined;
  }, [t]);

  const validatePassword = useCallback((password: string): string | undefined => {
    if (!password) {
      return t('auth.validation.passwordRequired', 'Password is required');
    }
    if (password.length < 6) {
      return t('auth.validation.passwordTooShort', 'Password must be at least 6 characters');
    }
    return undefined;
  }, [t]);

  const validateForm = useCallback((): FormErrors => {
    return {
      email: validateEmail(formData.email),
      password: validatePassword(formData.password)
    };
  }, [formData, validateEmail, validatePassword]);

  const handleInputChange = useCallback((field: keyof FormData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear field-specific error on change
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
    
    // Clear general error on any input change
    if (errors.general) {
      setErrors(prev => ({ ...prev, general: undefined }));
    }
  }, [errors]);

  const handleBlur = useCallback((field: keyof FormData) => () => {
    setTouched(prev => ({ ...prev, [field]: true }));
    
    // Validate field on blur if it's been touched
    const fieldError = field === 'email' 
      ? validateEmail(formData[field])
      : validatePassword(formData[field]);
    
    setErrors(prev => ({ ...prev, [field]: fieldError }));
  }, [formData, validateEmail, validatePassword]);

  // Removed storeAuthToken - now handled by AuthContext

  const handleSubmit = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();
    
    // Mark all fields as touched
    setTouched({ email: true, password: true });
    
    const validationErrors = validateForm();
    const hasErrors = Object.values(validationErrors).some(Boolean);
    
    if (hasErrors) {
      setErrors(validationErrors);
      // Focus first field with error
      if (validationErrors.email) {
        emailRef.current?.focus();
      } else if (validationErrors.password) {
        passwordRef.current?.focus();
      }
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      // Use the login method from useAuth which includes mock authentication
      await login(formData.email, formData.password);
      
      // Redirect to intended destination or dashboard
      const from = (location.state as any)?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
      
    } catch (error: any) {
      logger.error('Login failed', { error: error.message, email: formData.email });
      
      const errorMessage = error.message || 
        t('auth.errors.loginFailed', 'Login failed. Please check your credentials.');
      
      setErrors({ general: errorMessage });
      
      // Focus error message for screen readers
      setTimeout(() => {
        errorRef.current?.focus();
      }, 100);
      
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, validateForm, login, navigate, location.state, t]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !isSubmitting) {
      handleSubmit(event as any);
    }
  }, [handleSubmit, isSubmitting]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
            {t('auth.signIn.title', 'Sign in to your account')}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            {t('auth.signIn.subtitle', 'Enter your credentials to access your dashboard')}
          </p>
        </div>

        <Card className="py-8 px-6">
          <form onSubmit={handleSubmit} className="space-y-6" noValidate>
            {errors.general && (
              <div
                ref={errorRef}
                className="rounded-md bg-red-50 dark:bg-red-900/20 p-4"
                role="alert"
                aria-live="polite"
                tabIndex={-1}
              >
                <div className="text-sm text-red-800 dark:text-red-200">
                  {errors.general}
                </div>
              </div>
            )}

            <div>
              <label 
                htmlFor="email" 
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                {t('auth.fields.email', 'Email address')}
              </label>
              <div className="mt-1">
                <input
                  ref={emailRef}
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleInputChange('email')}
                  onBlur={handleBlur('email')}
                  onKeyDown={handleKeyDown}
                  aria-invalid={touched.email && errors.email ? 'true' : 'false'}
                  aria-describedby={errors.email ? 'email-error' : undefined}
                  className={`
                    appearance-none rounded-md relative block w-full px-3 py-2 
                    border placeholder-gray-500 dark:placeholder-gray-400 
                    text-gray-900 dark:text-white bg-white dark:bg-gray-800
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
                    focus:z-10 sm:text-sm transition-colors
                    ${touched.email && errors.email 
                      ? 'border-red-300 dark:border-red-600' 
                      : 'border-gray-300 dark:border-gray-600'
                    }
                  `}
                  placeholder={t('auth.placeholders.email', 'Enter your email')}
                  disabled={isSubmitting}
                />
              </div>
              {touched.email && errors.email && (
                <p id="email-error" className="mt-2 text-sm text-red-600 dark:text-red-400" role="alert">
                  {errors.email}
                </p>
              )}
            </div>

            <div>
              <label 
                htmlFor="password" 
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                {t('auth.fields.password', 'Password')}
              </label>
              <div className="mt-1">
                <input
                  ref={passwordRef}
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={handleInputChange('password')}
                  onBlur={handleBlur('password')}
                  onKeyDown={handleKeyDown}
                  aria-invalid={touched.password && errors.password ? 'true' : 'false'}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                  className={`
                    appearance-none rounded-md relative block w-full px-3 py-2 
                    border placeholder-gray-500 dark:placeholder-gray-400 
                    text-gray-900 dark:text-white bg-white dark:bg-gray-800
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
                    focus:z-10 sm:text-sm transition-colors
                    ${touched.password && errors.password 
                      ? 'border-red-300 dark:border-red-600' 
                      : 'border-gray-300 dark:border-gray-600'
                    }
                  `}
                  placeholder={t('auth.placeholders.password', 'Enter your password')}
                  disabled={isSubmitting}
                />
              </div>
              {touched.password && errors.password && (
                <p id="password-error" className="mt-2 text-sm text-red-600 dark:text-red-400" role="alert">
                  {errors.password}
                </p>
              )}
            </div>

            <div>
              <Button
                type="submit"
                variant="primary"
                size="lg"
                disabled={isSubmitting}
                className="w-full flex justify-center"
                aria-describedby={isSubmitting ? 'signin-loading' : undefined}
              >
                {isSubmitting ? (
                  <>
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    <span id="signin-loading">
                      {t('auth.signIn.signingIn', 'Signing in...')}
                    </span>
                  </>
                ) : (
                  t('auth.signIn.submit', 'Sign in')
                )}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
};