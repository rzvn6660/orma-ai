import { Pill } from 'lucide-react';
import BrandLogo from '../BrandLogo';

export default function ReminderHeader({ userName }) {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  return (
    <div className="flex flex-col items-center text-center mb-6">
      <div className="mb-4">
        <BrandLogo layout="vertical" className="h-14" textClassName="text-lg" textColor="text-white" accentColor="text-blue-400" />
      </div>
      <h2 className="text-xs uppercase tracking-widest text-blue-400 font-bold mb-2 flex items-center justify-center gap-2">
        <Pill className="w-4 h-4" /> Medication Reminder
      </h2>
      <h1 id="reminder-title" className="text-2xl font-extrabold text-white mb-2">
        {getGreeting()}, {userName}
      </h1>
      <p className="text-slate-400 text-sm">It's time to take your medicine.</p>
    </div>
  );
}
