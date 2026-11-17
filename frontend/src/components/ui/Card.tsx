import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  headerAction?: React.ReactNode;
  variant?: 'default' | 'evidence' | 'metrics';
  icon?: React.ReactNode;
}

export default function Card({ 
  children, 
  className = '', 
  title,
  headerAction,
  variant = 'default',
  icon
}: CardProps) {
  const variantClasses = {
    default: 'bg-white border border-[#E6E5F0]',
    evidence: 'bg-white border border-[#E6E5F0]',
    metrics: 'bg-white border border-[#E6E5F0]'
  };
  const contentSpacing = className.split(/\s+/).filter((name) => name.startsWith('space-y-')).join(' ');

  return (
    <div className={`ui-card ${variantClasses[variant]} rounded-2xl shadow-sm overflow-hidden flex flex-col ${className}`}>
      {title && (
        <div className="px-6 py-4 border-b border-[#E6E5F0] bg-white flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            {icon && <span className="text-violet-600">{icon}</span>}
            <h3 className="text-sm font-bold text-[#17172F] tracking-tight">{title}</h3>
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      <div className={`card-content flex-1 ${!title && !/(?:^|\s)p-\d/.test(className) ? 'p-6' : ''} ${contentSpacing}`}>
        {children}
      </div>
    </div>
  );
}
