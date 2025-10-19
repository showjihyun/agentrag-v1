'use client';

import React, { useState } from 'react';
import { Sparkles, Zap, X } from 'lucide-react';

interface FirstVisitGuideProps {
  onComplete: () => void;
}

/**
 * First Visit Guide Component
 * 
 * Shows a friendly introduction to Smart Mode for first-time users.
 */
export default function FirstVisitGuide({ onComplete }: FirstVisitGuideProps) {
  const [step, setStep] = useState(0);

  const steps = [
    {
      icon: <Sparkles className="w-12 h-12 text-blue-500" />,
      title: "Welcome to Smart Mode! 🎉",
      description: "AI automatically selects the best processing mode for your questions.",
      tip: "No need to worry about settings - just ask your question!"
    },
    {
      icon: <Zap className="w-12 h-12 text-yellow-500" />,
      title: "How it works",
      description: "Simple questions get fast answers (~2s), complex questions get deep analysis (~10s).",
      tip: "The AI analyzes your question and picks the optimal mode."
    },
    {
      icon: <span className="text-4xl">⚙️</span>,
      title: "You're in control",
      description: "Want to choose manually? Just click 'Options' to see all modes.",
      tip: "Smart Mode is on by default, but you can turn it off anytime."
    }
  ];

  const currentStep = steps[step];
  const isLastStep = step === steps.length - 1;

  const handleNext = () => {
    if (isLastStep) {
      onComplete();
    } else {
      setStep(step + 1);
    }
  };

  const handleSkip = () => {
    onComplete();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full mx-4 p-6 animate-slideUp">
        {/* Close button */}
        <button
          onClick={handleSkip}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Content */}
        <div className="text-center space-y-4">
          {/* Icon */}
          <div className="flex justify-center">
            {currentStep.icon}
          </div>

          {/* Title */}
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {currentStep.title}
          </h2>

          {/* Description */}
          <p className="text-gray-600 dark:text-gray-400 text-base">
            {currentStep.description}
          </p>

          {/* Tip */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              💡 {currentStep.tip}
            </p>
          </div>

          {/* Progress dots */}
          <div className="flex justify-center gap-2 pt-2">
            {steps.map((_, index) => (
              <div
                key={index}
                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                  index === step
                    ? 'bg-blue-500 w-6'
                    : 'bg-gray-300 dark:bg-gray-600'
                }`}
              />
            ))}
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            {!isLastStep && (
              <button
                onClick={handleSkip}
                className="flex-1 px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
              >
                Skip
              </button>
            )}
            <button
              onClick={handleNext}
              className={`${
                isLastStep ? 'flex-1' : 'flex-1'
              } px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-all duration-200 shadow-md hover:shadow-lg`}
            >
              {isLastStep ? "Let's Go! 🚀" : 'Next'}
            </button>
          </div>
        </div>
      </div>

      {/* CSS Animations */}
      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }

        .animate-slideUp {
          animation: slideUp 0.4s ease-out;
        }
      `}</style>
    </div>
  );
}
