import React from 'react';
import { 
  Check, 
  Clock, 
  AlertCircle, 
  AlertTriangle, 
  Sparkles, 
  Stethoscope, 
  Droplet, 
  Activity, 
  Calendar, 
  Building2,
  Bell
} from 'lucide-react';

const CHIP_VARIANTS = {
  // Medication Adherence States
  taken: {
    label: 'TAKEN',
    icon: Check,
    bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25',
    dot: 'bg-emerald-400'
  },
  upcoming: {
    label: 'UPCOMING',
    icon: Clock,
    bg: 'bg-blue-500/10 text-blue-400 border-blue-500/25',
    dot: 'bg-blue-400'
  },
  due: {
    label: 'DUE NEXT',
    icon: Bell,
    bg: 'bg-cyan-500/15 text-cyan-300 border-cyan-400/30 animate-pulse',
    dot: 'bg-cyan-400'
  },
  snoozed: {
    label: 'SNOOZED',
    icon: Clock,
    bg: 'bg-amber-500/10 text-amber-400 border-amber-500/25',
    dot: 'bg-amber-400'
  },
  missed: {
    label: 'MISSED',
    icon: AlertCircle,
    bg: 'bg-red-500/10 text-red-400 border-red-500/25',
    dot: 'bg-red-400'
  },
  active: {
    label: 'ACTIVE',
    icon: Check,
    bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    dot: 'bg-emerald-400'
  },
  paused: {
    label: 'PAUSED',
    icon: Clock,
    bg: 'bg-slate-800 text-slate-400 border-slate-700',
    dot: 'bg-slate-400'
  },

  // Appointment & Event Categories
  doctor: {
    label: 'DOCTOR',
    icon: Stethoscope,
    bg: 'bg-blue-500/10 text-blue-400 border-blue-500/25',
    dot: 'bg-blue-400'
  },
  test: {
    label: 'LAB TEST',
    icon: Droplet,
    bg: 'bg-amber-500/10 text-amber-400 border-amber-500/25',
    dot: 'bg-amber-400'
  },
  therapy: {
    label: 'THERAPY',
    icon: Activity,
    bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25',
    dot: 'bg-emerald-400'
  },
  followup: {
    label: 'FOLLOW-UP',
    icon: Calendar,
    bg: 'bg-purple-500/10 text-purple-400 border-purple-500/25',
    dot: 'bg-purple-400'
  },
  hospital: {
    label: 'HOSPITAL',
    icon: Building2,
    bg: 'bg-rose-500/10 text-rose-400 border-rose-500/25',
    dot: 'bg-rose-400'
  },
  default: {
    label: 'INFO',
    icon: Sparkles,
    bg: 'bg-slate-800 text-slate-300 border-slate-700',
    dot: 'bg-slate-400'
  }
};

export default function OrmaChip({
  variant = 'default',
  label,
  icon: CustomIcon,
  size = 'default', // 'small' | 'default' | 'large'
  showIcon = true,
  showDot = false,
  className = ''
}) {
  const config = CHIP_VARIANTS[variant.toLowerCase()] || CHIP_VARIANTS.default;
  const displayLabel = label || config.label;
  const Icon = CustomIcon || config.icon;

  const sizeClasses = {
    small: 'text-[10px] px-2 py-0.5 gap-1',
    default: 'text-xs px-2.5 py-1 gap-1.5',
    large: 'text-sm px-3.5 py-1.5 gap-2 font-extrabold'
  };

  const iconSizes = {
    small: 'w-3 h-3',
    default: 'w-3.5 h-3.5',
    large: 'w-4 h-4'
  };

  return (
    <span
      className={`inline-flex items-center rounded-full font-bold uppercase tracking-wider border backdrop-blur-md shadow-sm select-none ${
        config.bg
      } ${sizeClasses[size] || sizeClasses.default} ${className}`}
    >
      {showDot && (
        <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} aria-hidden="true" />
      )}
      {showIcon && Icon && (
        <Icon className={`${iconSizes[size] || iconSizes.default} shrink-0`} aria-hidden="true" />
      )}
      <span>{displayLabel}</span>
    </span>
  );
}
