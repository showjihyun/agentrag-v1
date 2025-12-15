'use client';

import React from 'react';
import { motion, AnimatePresence, Variants } from 'framer-motion';
import { cn } from '@/lib/utils';

// Animation variants
export const fadeInUp: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

export const fadeInScale: Variants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
};

export const slideInRight: Variants = {
  initial: { opacity: 0, x: 50 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -50 },
};

export const slideInLeft: Variants = {
  initial: { opacity: 0, x: -50 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 50 },
};

export const staggerContainer: Variants = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

export const staggerItem: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
};

// Animated wrapper components
interface AnimatedDivProps {
  children: React.ReactNode;
  className?: string;
  variants?: Variants;
  initial?: string;
  animate?: string;
  exit?: string;
  transition?: any;
  delay?: number;
}

export function AnimatedDiv({
  children,
  className,
  variants = fadeInUp,
  initial = 'initial',
  animate = 'animate',
  exit = 'exit',
  transition,
  delay = 0,
}: AnimatedDivProps) {
  return (
    <motion.div
      className={className}
      variants={variants}
      initial={initial}
      animate={animate}
      exit={exit}
      transition={{ duration: 0.3, delay, ...transition }}
    >
      {children}
    </motion.div>
  );
}

// Animated card component
interface AnimatedCardProps extends AnimatedDivProps {
  hover?: boolean;
  tap?: boolean;
}

export function AnimatedCard({
  children,
  className,
  hover = true,
  tap = true,
  ...props
}: AnimatedCardProps) {
  return (
    <motion.div
      className={cn('cursor-pointer', className)}
      whileHover={hover ? { scale: 1.02, y: -2 } : undefined}
      whileTap={tap ? { scale: 0.98 } : undefined}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      variants={props.variants || fadeInUp}
      initial={props.initial || 'initial'}
      animate={props.animate || 'animate'}
      exit={props.exit || 'exit'}
    >
      {children}
    </motion.div>
  );
}

// Animated list container
interface AnimatedListProps {
  children: React.ReactNode;
  className?: string;
}

export function AnimatedList({ children, className }: AnimatedListProps) {
  return (
    <motion.div
      className={className}
      variants={staggerContainer}
      initial="initial"
      animate="animate"
    >
      {children}
    </motion.div>
  );
}

// Animated list item
export function AnimatedListItem({
  children,
  className,
  ...props
}: AnimatedDivProps) {
  return (
    <motion.div
      className={className}
      variants={staggerItem}
      transition={{ duration: 0.3 }}
      {...props}
    >
      {children}
    </motion.div>
  );
}

// Progress bar animation
interface AnimatedProgressProps {
  value: number;
  className?: string;
  barClassName?: string;
}

export function AnimatedProgress({ value, className, barClassName }: AnimatedProgressProps) {
  return (
    <div className={cn('w-full bg-gray-200 rounded-full h-2', className)}>
      <motion.div
        className={cn('bg-blue-600 h-2 rounded-full', barClassName)}
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      />
    </div>
  );
}

// Animated counter
interface AnimatedCounterProps {
  value: number;
  duration?: number;
  className?: string;
}

export function AnimatedCounter({ value, duration = 1, className }: AnimatedCounterProps) {
  return (
    <motion.span
      className={className}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <motion.span
        initial={{ scale: 0.8 }}
        animate={{ scale: 1 }}
        transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      >
        {value}
      </motion.span>
    </motion.span>
  );
}

// Pulse animation for live indicators
export function PulseIndicator({ className }: { className?: string }) {
  return (
    <motion.div
      className={cn('w-2 h-2 bg-green-500 rounded-full', className)}
      animate={{
        scale: [1, 1.2, 1],
        opacity: [1, 0.7, 1],
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    />
  );
}

// Floating animation for elements
export function FloatingElement({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <motion.div
      className={className}
      animate={{
        y: [0, -10, 0],
      }}
      transition={{
        duration: 3,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    >
      {children}
    </motion.div>
  );
}

// Slide transition for page changes
interface SlideTransitionProps {
  children: React.ReactNode;
  direction?: 'left' | 'right' | 'up' | 'down';
}

export function SlideTransition({ children, direction = 'right' }: SlideTransitionProps) {
  const variants = {
    left: slideInLeft,
    right: slideInRight,
    up: fadeInUp,
    down: { ...fadeInUp, initial: { opacity: 0, y: -20 }, animate: { opacity: 1, y: 0 } },
  };

  return (
    <AnimatePresence mode="wait">
      <motion.div
        variants={variants[direction]}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={{ duration: 0.3 }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

// Morphing shape for dynamic backgrounds
export function MorphingShape({ className }: { className?: string }) {
  return (
    <motion.div
      className={cn('absolute inset-0 opacity-10', className)}
      animate={{
        borderRadius: ['20% 80% 80% 20%', '80% 20% 20% 80%', '20% 80% 80% 20%'],
      }}
      transition={{
        duration: 8,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
    />
  );
}

// Typewriter effect
interface TypewriterProps {
  text: string;
  delay?: number;
  className?: string;
}

export function Typewriter({ text, delay = 0.05, className }: TypewriterProps) {
  return (
    <motion.span
      className={className}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      {text.split('').map((char, index) => (
        <motion.span
          key={index}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: index * delay }}
        >
          {char}
        </motion.span>
      ))}
    </motion.span>
  );
}