import React from 'react';

export default function BrandLogo({ 
  className = "h-10", 
  textClassName = "text-xl", 
  showText = true, 
  layout = "horizontal",
  textColor = "text-slate-800",
  accentColor = "text-blue-600",
  textOverride = null 
}) {
  // layout can be "horizontal" or "vertical"
  
  if (layout === "vertical") {
    return (
      <div className="flex flex-col items-center justify-center gap-3">
        <img 
          src="/logo-transparent.png" 
          alt="ORMA AI Logo" 
          className={`${className} w-auto object-contain`}
          style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
        />
        {showText && (
          <span className={`font-bold tracking-tight ${textColor} ${textClassName}`} style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}>
            {textOverride || <>Orma<span className={accentColor}>AI</span></>}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3.5" style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}>
      <img 
        src="/logo-transparent.png" 
        alt="ORMA AI Logo" 
        className={`${className} w-auto object-contain`}
        style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}
      />
      {showText && (
        <span className={`font-bold tracking-tight ${textColor} ${textClassName}`} style={{ border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent' }}>
          {textOverride || <>Orma<span className={accentColor}>AI</span></>}
        </span>
      )}
    </div>
  );
}
