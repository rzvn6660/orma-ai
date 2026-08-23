import { Pill } from 'lucide-react';
import BrandLogo from '../BrandLogo';
import { getGreetingText, getReminderStrings, isRTL } from '../../utils/reminderLocalization';
import { DEFAULT_REMINDER_LANGUAGE } from '../../config/reminderLanguages';

export default function ReminderHeader({ userName, currentCount, totalCount, user }) {
  const prefs = user?.notification_preferences || {};
  const reminderLang = prefs.reminder_language || localStorage.getItem('orma_reminder_language') || DEFAULT_REMINDER_LANGUAGE;
  const strings = getReminderStrings(reminderLang);
  const greeting = getGreetingText(reminderLang);
  const rtl = isRTL(reminderLang);

  const isMulti = totalCount && totalCount > 1;
  const progressText = (strings.progressOf || "{current} of {total}")
    .replace('{current}', currentCount)
    .replace('{total}', totalCount);

  return (
    <div className={`flex flex-col items-center text-center mb-5 space-y-2 ${rtl ? 'rtl' : 'ltr'}`} dir={rtl ? 'rtl' : 'ltr'}>
      <div className="mb-2">
        <BrandLogo layout="vertical" className="h-12" textClassName="text-base" textColor="text-white" accentColor="text-blue-400" />
      </div>
      
      <div className="px-3.5 py-1 rounded-full bg-blue-500/15 border border-blue-500/30 text-blue-400 font-extrabold text-xs tracking-wider uppercase flex items-center justify-center gap-2 shadow-sm">
        <Pill className="w-4 h-4 text-blue-400" />
        <span>{strings.reminderTitle}</span>
        {isMulti && (
          <span className="text-slate-300 font-bold border-l border-blue-500/30 pl-2">
            {progressText}
          </span>
        )}
      </div>

      <h1 id="reminder-title" className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
        {greeting}, {userName || 'Friend'}
      </h1>
      
      <p className="text-slate-300 text-sm font-medium">{strings.reminderHeadline}</p>
    </div>
  );
}
