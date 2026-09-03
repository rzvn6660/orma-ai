import { Pill } from 'lucide-react';
import BrandLogo from '../BrandLogo';
import { getGreetingText, getReminderStrings, getLocalizedHeadline, isRTL } from '../../utils/reminderLocalization';
import { DEFAULT_REMINDER_LANGUAGE } from '../../config/reminderLanguages';

export default function ReminderHeader({ userName, currentCount, totalCount, user, medicineName = '' }) {
  const prefs = user?.notification_preferences || {};
  const reminderLang = prefs.reminder_language || localStorage.getItem('orma_reminder_language') || DEFAULT_REMINDER_LANGUAGE;
  const strings = getReminderStrings(reminderLang);
  const greeting = getGreetingText(reminderLang);
  const rtl = isRTL(reminderLang);

  const isMulti = totalCount && totalCount > 1;
  const progressText = (strings.progressOf || "{current} of {total}")
    .replace('{current}', currentCount)
    .replace('{total}', totalCount);

  const headline = isMulti
    ? (strings.multipleMedicinesLabel || "Medicines to take at this time:")
    : getLocalizedHeadline(reminderLang, medicineName);

  return (
    <div className={`flex flex-col items-center text-center mb-3 sm:mb-4 space-y-1 sm:space-y-1.5 shrink-0 ${rtl ? 'rtl' : 'ltr'}`} dir={rtl ? 'rtl' : 'ltr'}>
      <div className="mb-0.5">
        <BrandLogo layout="vertical" className="h-8 sm:h-9" textClassName="text-sm" textColor="text-white" accentColor="text-blue-400" />
      </div>
      
      <div className="px-3 py-0.5 rounded-full bg-blue-500/15 border border-blue-500/30 text-blue-400 font-extrabold text-[11px] tracking-wider uppercase flex items-center justify-center gap-1.5 shadow-sm">
        <Pill className="w-3.5 h-3.5 text-blue-400" />
        <span>{strings.reminderTitle}</span>
        {isMulti && (
          <span className="text-slate-300 font-bold border-l border-blue-500/30 pl-2">
            {progressText}
          </span>
        )}
      </div>

      <h1 id="reminder-title" className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
        {greeting}, {userName || 'Friend'}
      </h1>
      
      <p className="text-slate-200 text-xs sm:text-sm font-semibold">{headline}</p>
    </div>
  );
}
