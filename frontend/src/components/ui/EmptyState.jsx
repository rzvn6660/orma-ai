import React from 'react';
import { motion } from 'framer-motion';
import { Plus } from 'lucide-react';

export default function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  actionIcon: ActionIcon = Plus,
  secondaryActionLabel,
  onSecondaryAction,
  className = ''
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={`p-8 sm:p-10 text-center border border-dashed border-white/10 rounded-3xl bg-slate-950/40 backdrop-blur-xl flex flex-col items-center justify-center max-w-lg mx-auto ${className}`}
    >
      {/* Featured Icon with Ambient Glow */}
      {Icon && (
        <div className="relative mb-4">
          <div className="absolute inset-0 bg-blue-500/20 rounded-2xl blur-xl" />
          <div className="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 relative z-10 shadow-lg">
            <Icon className="w-7 h-7" />
          </div>
        </div>
      )}

      {/* Title */}
      <h3 className="text-base sm:text-lg font-bold text-white tracking-tight mb-1.5">
        {title}
      </h3>

      {/* Description */}
      {description && (
        <p className="text-xs sm:text-sm text-slate-400 max-w-sm leading-relaxed mb-5">
          {description}
        </p>
      )}

      {/* Actions */}
      {(onAction || onSecondaryAction) && (
        <div className="flex items-center gap-3 flex-wrap justify-center">
          {onAction && actionLabel && (
            <button
              type="button"
              onClick={onAction}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs sm:text-sm font-bold transition-all shadow-md shadow-blue-600/25 inline-flex items-center gap-1.5 cursor-pointer"
            >
              {ActionIcon && <ActionIcon className="w-4 h-4" />}
              <span>{actionLabel}</span>
            </button>
          )}

          {onSecondaryAction && secondaryActionLabel && (
            <button
              type="button"
              onClick={onSecondaryAction}
              className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-white/10 text-slate-300 text-xs sm:text-sm font-bold transition-colors cursor-pointer"
            >
              {secondaryActionLabel}
            </button>
          )}
        </div>
      )}
    </motion.div>
  );
}
