/**
 * Password Strength Indicator Component
 * Shows real-time password strength validation
 */

'use client';

import { useMemo } from 'react';

interface PasswordStrengthIndicatorProps {
  password: string;
  showRequirements?: boolean;
}

interface PasswordRequirement {
  label: string;
  met: boolean;
  regex?: RegExp;
  minLength?: number;
}

export default function PasswordStrengthIndicator({
  password,
  showRequirements = true,
}: PasswordStrengthIndicatorProps) {
  const requirements: PasswordRequirement[] = useMemo(() => {
    return [
      {
        label: 'At least 8 characters',
        met: password.length >= 8,
        minLength: 8,
      },
      {
        label: 'Contains a letter',
        met: /[a-zA-Z]/.test(password),
        regex: /[a-zA-Z]/,
      },
      {
        label: 'Contains a number',
        met: /\d/.test(password),
        regex: /\d/,
      },
      {
        label: 'Contains uppercase letter (recommended)',
        met: /[A-Z]/.test(password),
        regex: /[A-Z]/,
      },
      {
        label: 'Contains special character (recommended)',
        met: /[!@#$%^&*(),.?":{}|<>]/.test(password),
        regex: /[!@#$%^&*(),.?":{}|<>]/,
      },
    ];
  }, [password]);

  const requiredMet = requirements.slice(0, 3).every((req) => req.met);
  const recommendedMet = requirements.slice(3).every((req) => req.met);
  const metCount = requirements.filter((req) => req.met).length;

  const strength = useMemo(() => {
    if (password.length === 0) return { level: 0, label: '', color: '' };
    if (metCount <= 2) return { level: 1, label: 'Weak', color: 'bg-red-500' };
    if (metCount === 3) return { level: 2, label: 'Fair', color: 'bg-yellow-500' };
    if (metCount === 4) return { level: 3, label: 'Good', color: 'bg-blue-500' };
    return { level: 4, label: 'Strong', color: 'bg-green-500' };
  }, [metCount, password.length]);

  if (password.length === 0) return null;

  return (
    <div className="space-y-2">
      {/* Strength Bar */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-gray-600">Password Strength</span>
          <span className={`text-xs font-semibold ${
            strength.level === 1 ? 'text-red-600' :
            strength.level === 2 ? 'text-yellow-600' :
            strength.level === 3 ? 'text-blue-600' :
            'text-green-600'
          }`}>
            {strength.label}
          </span>
        </div>
        <div className="flex space-x-1">
          {[1, 2, 3, 4].map((level) => (
            <div
              key={level}
              className={`h-2 flex-1 rounded-full transition-all ${
                level <= strength.level
                  ? strength.color
                  : 'bg-gray-200'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Requirements List */}
      {showRequirements && (
        <div className="space-y-1">
          <p className="text-xs font-semibold text-gray-700">Requirements:</p>
          {requirements.map((req, idx) => (
            <div
              key={idx}
              className="flex items-center space-x-2 text-xs"
            >
              <span className={`${
                req.met ? 'text-green-600' : 'text-gray-400'
              }`}>
                {req.met ? '✓' : '○'}
              </span>
              <span className={`${
                req.met ? 'text-gray-700' : 'text-gray-500'
              }`}>
                {req.label}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Validation Message */}
      {!requiredMet && password.length > 0 && (
        <p className="text-xs text-red-600">
          ⚠️ Password must meet all required criteria
        </p>
      )}
      {requiredMet && !recommendedMet && (
        <p className="text-xs text-blue-600">
          💡 Consider adding uppercase letters and special characters for better security
        </p>
      )}
      {requiredMet && recommendedMet && (
        <p className="text-xs text-green-600">
          ✓ Strong password!
        </p>
      )}
    </div>
  );
}
