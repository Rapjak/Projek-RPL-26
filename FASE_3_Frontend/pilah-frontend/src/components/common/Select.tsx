import React from 'react';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
}

export function Select({ label, error, className = '', children, ...props }: SelectProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <div className="relative rounded-md shadow-sm">
        <select
          className={`block w-full rounded-lg border-gray-300 focus:ring-emerald-500 focus:border-emerald-500 sm:text-sm ${error ? 'border-red-300 focus:ring-red-500 focus:border-red-500' : ''} ${className}`}
          {...props}
        >
          {children}
        </select>
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
