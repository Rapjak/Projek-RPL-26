import { XMarkIcon, CheckCircleIcon, ExclamationCircleIcon, InformationCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface AlertProps {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  onClose?: () => void;
  className?: string;
}

const icons = {
  success: CheckCircleIcon,
  error: ExclamationCircleIcon,
  warning: ExclamationTriangleIcon,
  info: InformationCircleIcon
};

const styles = {
  success: 'bg-green-50 text-green-800 border-green-200',
  error: 'bg-red-50 text-red-800 border-red-200',
  warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
  info: 'bg-blue-50 text-blue-800 border-blue-200'
};

const iconStyles = {
  success: 'text-green-500',
  error: 'text-red-500',
  warning: 'text-yellow-500',
  info: 'text-blue-500'
};

export function Alert({ type, message, onClose, className = '' }: AlertProps) {
  const Icon = icons[type];

  return (
    <div className={`flex items-start gap-3 p-4 rounded-lg border ${styles[type]} ${className}`}>
      <Icon className={`h-5 w-5 flex-shrink-0 ${iconStyles[type]}`} />
      <p className="flex-1 text-sm">{message}</p>
      {onClose && (
        <button onClick={onClose} className="flex-shrink-0 hover:opacity-70">
          <XMarkIcon className="h-5 w-5" />
        </button>
      )}
    </div>
  );
}
