'use client';

import { useState, useEffect } from 'react';

const ONBOARDING_KEY = 'agentic-rag-onboarding-completed';

export function useOnboarding() {
  const [showWelcome, setShowWelcome] = useState(false);
  const [showTour, setShowTour] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user has completed onboarding
    const completed = localStorage.getItem(ONBOARDING_KEY);
    
    if (!completed) {
      setShowWelcome(true);
    }
    
    setIsLoading(false);
  }, []);

  const startTour = () => {
    setShowWelcome(false);
    setShowTour(true);
  };

  const skipWelcome = () => {
    setShowWelcome(false);
    markAsCompleted();
  };

  const completeTour = () => {
    setShowTour(false);
    markAsCompleted();
  };

  const skipTour = () => {
    setShowTour(false);
    markAsCompleted();
  };

  const markAsCompleted = () => {
    localStorage.setItem(ONBOARDING_KEY, 'true');
  };

  const resetOnboarding = () => {
    localStorage.removeItem(ONBOARDING_KEY);
    setShowWelcome(true);
  };

  return {
    showWelcome,
    showTour,
    isLoading,
    startTour,
    skipWelcome,
    completeTour,
    skipTour,
    resetOnboarding,
  };
}
