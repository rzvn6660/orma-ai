import { useState } from 'react';
import { CheckCircle2, Clock, X, Loader2, ChevronLeft } from 'lucide-react';

export default function ReminderButtons({ onMarkTaken, onSnooze, onSkip, loading }) {
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);
  const [showSnoozeOptions, setShowSnoozeOptions] = useState(false);

  if (showSkipConfirm) {
    return (
      <div className="flex flex-col gap-3 w-full">
        <p className="text-center text-slate-300 font-medium mb-1">Skipping will not mark this medicine as taken.</p>
        <p className="text-center text-red-400 font-bold mb-1">Skip today's reminder?</p>
        <button 
          onClick={onSkip}
          disabled={loading}
          className="orma-btn-danger"
        >
          Skip Reminder
        </button>
        <button 
          onClick={() => setShowSkipConfirm(false)}
          disabled={loading}
          className="orma-btn-secondary"
        >
          Cancel
        </button>
      </div>
    );
  }

  if (showSnoozeOptions) {
    return (
      <div className="flex flex-col gap-2 w-full">
        <button 
          onClick={() => setShowSnoozeOptions(false)}
          className="flex items-center gap-1 text-slate-400 hover:text-white mb-2 text-sm font-medium"
        >
          <ChevronLeft className="w-4 h-4" /> Back
        </button>
        <div className="grid grid-cols-2 gap-2">
          {[5, 10, 15, 30].map(mins => (
            <button
              key={mins}
              onClick={() => onSnooze(mins)}
              disabled={loading}
              className="orma-btn-secondary"
            >
              <Clock className="w-4 h-4 text-blue-400" /> {mins} min
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 w-full">
      <button 
        onClick={onMarkTaken}
        disabled={loading}
        className="orma-btn-primary"
      >
        {loading ? <Loader2 className="w-6 h-6 animate-spin" /> : <CheckCircle2 className="w-6 h-6" />}
        {loading ? 'Marking Taken...' : 'Mark Taken'}
      </button>
      
      <div className="flex gap-3">
        <button 
          onClick={() => setShowSnoozeOptions(true)}
          disabled={loading}
          className="orma-btn-secondary"
        >
          <Clock className="w-5 h-5" /> Snooze
        </button>
        
        <button 
          onClick={() => setShowSkipConfirm(true)}
          disabled={loading}
          className="flex-1 py-4 bg-slate-900 border border-slate-700 hover:bg-slate-800 active:scale-[0.98] disabled:opacity-50 disabled:scale-100 text-slate-400 hover:text-white rounded-xl font-bold transition-all flex items-center justify-center gap-2 focus:ring-4 focus:ring-slate-500/50 outline-none"
        >
          <X className="w-5 h-5" /> Skip
        </button>
      </div>
    </div>
  );
}
