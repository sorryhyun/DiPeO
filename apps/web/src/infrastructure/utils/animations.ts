// Animation utilities and micro-interaction configs

export const springConfig = {
  stiffness: 300,
  damping: 30,
};

export const smoothConfig = {
  stiffness: 100,
  damping: 20,
};

// Framer Motion variants for common animations
export const fadeInVariants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { duration: 0.2 }
  },
  exit: { 
    opacity: 0,
    transition: { duration: 0.15 }
  }
};

export const slideInVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.3, ease: [0.4, 0, 0.2, 1] }
  },
  exit: { 
    opacity: 0, 
    y: -10,
    transition: { duration: 0.2 }
  }
};

export const scaleInVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: { duration: 0.2, ease: [0.4, 0, 0.2, 1] }
  },
  exit: { 
    opacity: 0, 
    scale: 0.95,
    transition: { duration: 0.15 }
  }
};

export const popInVariants = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: { 
      type: "spring",
      stiffness: 300,
      damping: 20
    }
  },
  exit: { 
    opacity: 0, 
    scale: 0.8,
    transition: { duration: 0.15 }
  }
};

// Stagger children animations
export const staggerContainerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1
    }
  }
};

export const staggerItemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 0.2, 1]
    }
  }
};

// Hover animations
export const hoverScaleVariants = {
  rest: { scale: 1 },
  hover: { 
    scale: 1.05,
    transition: {
      duration: 0.2,
      ease: "easeOut"
    }
  },
  tap: { scale: 0.98 }
};

export const hoverLiftVariants = {
  rest: { 
    y: 0,
    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)"
  },
  hover: { 
    y: -2,
    boxShadow: "0 20px 25px -5px rgb(0 0 0 / 0.1)",
    transition: {
      duration: 0.3,
      ease: "easeOut"
    }
  }
};

// Interaction feedback
export const rippleAnimation = {
  initial: { scale: 0, opacity: 0.5 },
  animate: { 
    scale: 4, 
    opacity: 0,
    transition: {
      duration: 0.6,
      ease: "easeOut"
    }
  }
};

// Loading animations
export const pulseAnimation = {
  animate: {
    scale: [1, 1.05, 1],
    opacity: [1, 0.8, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut"
    }
  }
};

export const shimmerAnimation = {
  animate: {
    backgroundPosition: ["200% 0", "-200% 0"],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: "linear"
    }
  }
};

// Notification animations
export const notificationVariants = {
  hidden: { 
    opacity: 0, 
    y: -20,
    scale: 0.9
  },
  visible: { 
    opacity: 1, 
    y: 0,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 200,
      damping: 20
    }
  },
  exit: { 
    opacity: 0, 
    x: 100,
    transition: {
      duration: 0.2
    }
  }
};

// Utility functions
export const createStaggerDelay = (index: number, baseDelay = 0.05) => ({
  transition: { delay: index * baseDelay }
});

export const createHoverAnimation = (scale = 1.05) => ({
  whileHover: { scale },
  whileTap: { scale: 0.98 },
  transition: { duration: 0.2 }
});

// CSS-based micro-interactions (for non-framer-motion components)
export const microInteractionClasses = {
  hoverLift: "hover:-translate-y-0.5 hover:shadow-lg transition-all duration-200",
  hoverGlow: "hover:shadow-glow-sm transition-shadow duration-300",
  pressable: "active:scale-[0.98] transition-transform duration-150",
  focusRing: "focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-all duration-200",
  fadeIn: "animate-fade-in",
  slideIn: "animate-slide-in",
  scaleIn: "animate-scale-in",
};

// Timing functions
export const easings = {
  easeOut: [0.4, 0, 0.2, 1],
  easeIn: [0.4, 0, 1, 1],
  easeInOut: [0.4, 0, 0.2, 1],
  spring: [0.175, 0.885, 0.32, 1.275],
};