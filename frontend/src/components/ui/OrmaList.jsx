import React from 'react';
import { motion } from 'framer-motion';
import EmptyState from './EmptyState';

export function OrmaList({
  items = [],
  renderItem,
  emptyIcon,
  emptyTitle = 'No items found',
  emptyDescription,
  emptyActionLabel,
  onEmptyAction,
  className = '',
  divider = true
}) {
  if (!items || items.length === 0) {
    return (
      <EmptyState
        icon={emptyIcon}
        title={emptyTitle}
        description={emptyDescription}
        actionLabel={emptyActionLabel}
        onAction={onEmptyAction}
        className={className}
      />
    );
  }

  return (
    <div className={`flex flex-col rounded-3xl border border-white/10 bg-slate-950/40 backdrop-blur-xl overflow-hidden ${className}`}>
      {items.map((item, index) => (
        <div key={item.id || index} className="w-full">
          {renderItem(item, index)}
          {divider && index < items.length - 1 && (
            <div className="h-[1px] bg-white/5 mx-4" />
          )}
        </div>
      ))}
    </div>
  );
}

export function OrmaListItem({
  icon: Icon,
  iconBg = 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  title,
  subtitle,
  meta,
  badge,
  badgeVariant = 'default', // 'default' | 'success' | 'warning' | 'info'
  actions,
  onClick,
  className = ''
}) {
  const badgeStyles = {
    default: 'bg-slate-800 text-slate-300 border-slate-700',
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20'
  };

  const Content = (
    <div className={`p-4 sm:p-5 flex items-center justify-between gap-4 transition-colors ${
      onClick ? 'hover:bg-white/5 cursor-pointer' : ''
    } ${className}`}>
      <div className="flex items-center gap-3.5 min-w-0">
        {Icon && (
          <div className={`w-10 h-10 rounded-2xl flex items-center justify-center border shrink-0 ${iconBg}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}

        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h4 className="text-sm font-bold text-white tracking-tight truncate">
              {title}
            </h4>
            {badge && (
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${badgeStyles[badgeVariant] || badgeStyles.default}`}>
                {badge}
              </span>
            )}
          </div>

          {subtitle && (
            <p className="text-xs text-slate-400 mt-0.5 truncate">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        {meta && (
          <span className="text-xs font-mono font-semibold text-slate-400 hidden sm:inline-block">
            {meta}
          </span>
        )}
        {actions}
      </div>
    </div>
  );

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className="w-full text-left focus:outline-none">
        {Content}
      </button>
    );
  }

  return Content;
}

export default OrmaList;
