import { Loader2 } from 'lucide-react';

export default function OrmaCardSwitch({
  icon: Icon,
  title,
  description,
  checked = false,
  isPending = false,
  disabled = false,
  onChange,
  ariaLabel
}) {
  const handleToggle = (e) => {
    e?.stopPropagation();
    if (disabled || isPending) return;
    onChange(!checked);
  };

  const handleKeyDown = (e) => {
    if (disabled || isPending) return;
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      onChange(!checked);
    }
  };

  return (
    <div
      onClick={handleToggle}
      className={`p-5 rounded-2xl border transition-all duration-200 flex items-center justify-between gap-4 cursor-pointer min-h-[72px] select-none ${
        disabled
          ? 'opacity-50 cursor-not-allowed bg-slate-900/40 border-slate-800/50'
          : isPending
          ? 'bg-slate-800/60 border-blue-500/40 cursor-wait'
          : checked
          ? 'bg-slate-800/60 border-slate-700 hover:border-slate-600'
          : 'bg-slate-900/40 border-slate-800/80 hover:border-slate-700'
      }`}
    >
      <div className="flex items-start gap-4">
        {Icon && (
          <div
            className={`p-3 rounded-xl shrink-0 mt-0.5 border transition-colors ${
              checked
                ? 'bg-blue-500/10 border-blue-500/25 text-blue-400'
                : 'bg-slate-800/80 border-slate-700/60 text-slate-400'
            }`}
          >
            <Icon className="w-5 h-5" />
          </div>
        )}
        <div className="space-y-1">
          <h3 className="font-extrabold text-sm sm:text-base text-white tracking-tight flex items-center gap-2">
            {title}
            {isPending && (
              <span className="text-xs font-semibold text-blue-400 flex items-center gap-1">
                <Loader2 className="w-3 h-3 animate-spin" />
                Saving...
              </span>
            )}
          </h3>
          {description && (
            <p className="text-xs text-slate-400 leading-relaxed font-medium max-w-xl">
              {description}
            </p>
          )}
        </div>
      </div>

      <div className="shrink-0 flex items-center gap-3">
        <button
          type="button"
          role="switch"
          aria-checked={checked}
          aria-busy={isPending}
          aria-disabled={disabled || isPending}
          disabled={disabled || isPending}
          aria-label={ariaLabel || title}
          onKeyDown={handleKeyDown}
          onClick={handleToggle}
          className={`relative inline-flex h-9 w-20 shrink-0 cursor-pointer items-center rounded-full p-1 border transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-slate-950 ${
            isPending
              ? 'bg-slate-800 border-blue-500/40 opacity-90'
              : checked
              ? 'bg-blue-600 border-blue-400 shadow-md shadow-blue-600/20'
              : 'bg-slate-800 border-slate-700'
          }`}
        >
          {/* Visual ON / OFF label inside the track for immediate understanding without color reliance */}
          <span
            className={`text-[10px] font-black uppercase tracking-wider transition-all select-none ${
              isPending
                ? 'text-blue-300 font-bold ml-1.5'
                : checked
                ? 'text-white pl-1.5'
                : 'text-slate-400 ml-auto pr-1.5'
            }`}
          >
            {isPending ? '...' : checked ? 'ON' : 'OFF'}
          </span>

          {/* Sliding Knob */}
          <span
            className={`pointer-events-none inline-block h-7 w-7 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out flex items-center justify-center ${
              checked ? 'translate-x-[calc(100%-28px)]' : 'translate-x-0'
            }`}
          >
            {isPending ? (
              <Loader2 className="w-3.5 h-3.5 text-blue-600 animate-spin" />
            ) : (
              <span
                className={`w-2 h-2 rounded-full ${
                  checked ? 'bg-blue-600' : 'bg-slate-400'
                }`}
              />
            )}
          </span>
        </button>
      </div>
    </div>
  );
}
