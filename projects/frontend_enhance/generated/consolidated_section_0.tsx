import React, { FC, ReactNode, memo } from 'react';

type SectionCardProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  testId?: string;
};

const SectionCard: FC<SectionCardProps> = memo(
  ({
    title,
    subtitle,
    children,
    actions,
    className = '',
    loading = false,
    error = null,
    onRetry,
    testId,
  }) => {
    return (
      <section
        className={`section-card ${className}`.trim()}
        data-testid={testId ?? 'section-card'}
      >
        <header className="section-card__header">
          <div className="section-card__titleWrap">
            <h3 className="section-card__title">{title}</h3>
            {subtitle && <span className="section-card__subtitle">{subtitle}</span>}
          </div>
          <div className="section-card__actions">{actions}</div>
        </header>

        <div className="section-card__content">
          {loading ? (
            <div className="section-card__loading" aria-label="loading">
              Loading...
            </div>
          ) : error ? (
            <div className="section-card__error" role="alert" aria-live="polite">
              <div className="section-card__errorMessage">{error}</div>
              {onRetry && (
                <button
                  type="button"
                  className="btn btn--secondary"
                  onClick={onRetry}
                >
                  Retry
                </button>
              )}
            </div>
          ) : (
            <>{children}</>
          )}
        </div>
      </section>
    );
  }
);

SectionCard.displayName = 'SectionCard';

export default SectionCard;