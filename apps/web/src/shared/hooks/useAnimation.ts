import React, { useRef, useCallback } from 'react';

// Custom hook for micro-interactions
export function useRippleEffect() {
  const rippleRef = useRef<HTMLDivElement>(null);

  const createRipple = useCallback((event: React.MouseEvent<HTMLElement>) => {
    const button = event.currentTarget;
    const rippleContainer = rippleRef.current;
    
    if (!rippleContainer) return;

    // Create ripple element
    const ripple = document.createElement('span');
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;

    // Calculate position
    const rect = button.getBoundingClientRect();
    const x = event.clientX - rect.left - radius;
    const y = event.clientY - rect.top - radius;

    // Apply styles
    ripple.style.width = ripple.style.height = `${diameter}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    ripple.classList.add('ripple');

    // Add to container
    rippleContainer.appendChild(ripple);

    // Remove after animation
    setTimeout(() => {
      ripple.remove();
    }, 600);
  }, []);

  return { rippleRef, createRipple };
}

// Hook for hover effects
export function useHoverEffect(
  onHoverStart?: () => void,
  onHoverEnd?: () => void
) {
  const isHovered = useRef(false);

  const handleMouseEnter = useCallback(() => {
    if (!isHovered.current) {
      isHovered.current = true;
      onHoverStart?.();
    }
  }, [onHoverStart]);

  const handleMouseLeave = useCallback(() => {
    if (isHovered.current) {
      isHovered.current = false;
      onHoverEnd?.();
    }
  }, [onHoverEnd]);

  return {
    onMouseEnter: handleMouseEnter,
    onMouseLeave: handleMouseLeave,
  };
}

// Hook for stagger animations
export function useStaggerAnimation(itemCount: number, baseDelay = 50) {
  const getDelay = useCallback(
    (index: number) => index * baseDelay,
    [baseDelay]
  );

  const getAnimationStyle = useCallback(
    (index: number) => ({
      animationDelay: `${getDelay(index)}ms`,
    }),
    [getDelay]
  );

  return { getDelay, getAnimationStyle };
}

// Hook for intersection observer animations
export function useInViewAnimation(threshold = 0.1) {
  const elementRef = useRef<HTMLElement>(null);
  const hasAnimated = useRef(false);

  const checkInView = useCallback(() => {
    if (!elementRef.current || hasAnimated.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasAnimated.current) {
            hasAnimated.current = true;
            entry.target.classList.add('animate-in');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold }
    );

    observer.observe(elementRef.current);

    return () => observer.disconnect();
  }, [threshold]);

  return { elementRef, checkInView };
}