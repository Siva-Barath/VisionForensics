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
    default: 'bg-ink-panel border border-ink-border',
    evidence: 'evidence-card',
    metrics: 'metric-card bg-ink-panel border border-ink-border'
  };
  const contentSpacing = className.split(/\s+/).filter((name) => name.startsWith('space-y-')).join(' ');

  return (
    <div className={`ui-card ${variantClasses[variant]} rounded-xl overflow-hidden flex flex-col ${className}`}>
      {title && (
        <div className="px-5 py-3 border-b border-ink-border bg-ink-base/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {icon && <span className="text-gray-500">{icon}</span>}
            <h3 className="text-xs font-semibold text-gray-200 uppercase tracking-widest">{title}</h3>
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      <div className={`card-content flex-1 ${!title && !/(?:^|\s)p-\d/.test(className) ? 'p-5' : ''} ${contentSpacing}`}>
        {children}
      </div>
    </div>
  );
}
