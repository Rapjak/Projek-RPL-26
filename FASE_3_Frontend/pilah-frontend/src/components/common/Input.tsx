import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  rightElement?: React.ReactNode;
}

export function Input({
  label,
  error,
  rightElement,
  className = '',
  ...props
}: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <div className="relative rounded-md shadow-sm">
        <input
          className={`block w-full rounded-lg border-gray-300 focus:ring-emerald-500 focus:border-emerald-500 sm:text-sm ${error ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : ''} ${rightElement ? 'pr-10' : ''} ${className}`}
          {...props}
        />
        {rightElement && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            {rightElement}
          </div>
        )}
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
