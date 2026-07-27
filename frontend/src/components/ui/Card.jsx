
export function Card({ children, className = '', hover = false, compact = false, ...props }) {
  return (
    <div 
      className={`orma-card ${hover ? 'orma-card-hover' : ''} ${compact ? 'orma-card-compact' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
