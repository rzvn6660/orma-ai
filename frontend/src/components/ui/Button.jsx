
export function Button({ children, variant = 'primary', className = '', ...props }) {
  let variantClasses = "";
  
  if (variant === 'primary') variantClasses = "orma-btn-primary";
  else if (variant === 'secondary') variantClasses = "orma-btn-secondary";
  else if (variant === 'danger') variantClasses = "orma-btn-danger";
  else if (variant === 'ghost') variantClasses = "orma-btn-ghost";
  else if (variant === 'icon') variantClasses = "orma-btn-icon";
  else variantClasses = "orma-btn-primary";

  return (
    <button className={`${variantClasses} ${className}`} {...props}>
      {children}
    </button>
  );
}
