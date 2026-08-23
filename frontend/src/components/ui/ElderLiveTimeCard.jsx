import React, { useState, useEffect } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Clock, Pill, Calendar, CheckCircle2, ChevronRight, Sparkles, AlertCircle } from 'lucide-react';
import { SlidingTimeDisplay } from './SlidingNumber';

/**
 * Helper to compute 12-hour time and formatted date according to user timezone.
 */
function getElderTimeInfo(userTimezone) {
  const now = new Date();
  
  // Format 12-hour time
  const timeOptions = {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    ...(userTimezone ? { timeZone: userTimezone } : {})
  };

  // Format full weekday and date (e.g. "Tuesday, August 18")
  const dateOptions = {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    ...(userTimezone ? { timeZone: userTimezone } : {})
  };

  // Format numeric hour for dynamic greeting calculation (0 - 23)
  const hourOptions = {
    hour: 'numeric',
    hour12: false,
    ...(userTimezone ? { timeZone: userTimezone } : {})
  };

  let hours = '12';
  let minutes = '00';
  let period = 'AM';
  let formattedDate = 'Today';
  let numericHour = now.getHours();

  try {
    const parts = new Intl.DateTimeFormat('en-US', timeOptions).formatToParts(now);
    for (const part of parts) {
      if (part.type === 'hour') hours = part.value;
      if (part.type === 'minute') minutes = part.value;
      if (part.type === 'dayPeriod') period = part.value.toUpperCase();
    }
    formattedDate = new Intl.DateTimeFormat('en-US', dateOptions).format(now);
    
    const hStr = new Intl.DateTimeFormat('en-US', hourOptions).format(now);
    numericHour = parseInt(hStr, 10);
  } catch (err) {
    // Fallback to local device time
    let h = now.getHours();
    numericHour = h;
    const m = now.getMinutes();
    period = h >= 12 ? 'PM' : 'AM';
    h = h % 12 || 12;
    hours = String(h);
    minutes = m < 10 ? `0${m}` : String(m);
    formattedDate = now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
  }

  // Dynamic greeting based on time of day
  let greeting = 'Good morning';
  if (numericHour >= 5 && numericHour < 12) {
    greeting = 'Good morning';
  } else if (numericHour >= 12 && numericHour < 17) {
    greeting = 'Good afternoon';
  } else if (numericHour >= 17 && numericHour < 21) {
    greeting = 'Good evening';
  } else {
    greeting = 'Good night';
  }

  return {
    hours,
    minutes,
    period,
    formattedDate,
    greeting
  };
}

/**
 * ElderLiveTimeCard
 * Calm, accessible, high-contrast live clock and daily context card for the Elder Home page.
 */
export default function ElderLiveTimeCard({
  user,
  nextMedicine,
  nextAppointment,
  onTakeMedicine,
  onViewSchedule,
  className = ''
}) {
  const shouldReduceMotion = useReducedMotion();
  const [timeInfo, setTimeInfo] = useState(() => getElderTimeInfo(user?.timezone));

  // Update clock every second or minute
  useEffect(() => {
    const updateTime = () => {
      setTimeInfo(getElderTimeInfo(user?.timezone));
    };

    updateTime();
    // Update every 10 seconds to catch minute transitions immediately
    const timer = setInterval(updateTime, 10000);
    return () => clearInterval(timer);
  }, [user?.timezone]);

  const userName = user?.name ? user.name.split(' ')[0] : 'Friend';

  return (
    <div 
      className={`relative overflow-hidden rounded-3xl bg-gradient-to-b from-slate-900/95 via-slate-900/90 to-[#070E22]/95 border border-blue-500/25 p-6 sm:p-8 shadow-[0_15px_35px_rgba(2,6,23,0.6)] backdrop-blur-xl text-white ${className}`}
    >
      {/* Background Subtle Accent Glow */}
      <div className="absolute top-0 right-1/4 w-80 h-48 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-60 h-40 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6 lg:gap-10">
        
        {/* ================================================================ */}
        {/* LEFT / HERO: Greeting, Date, and Large Sliding Clock             */}
        {/* ================================================================ */}
        <div className="flex flex-col space-y-3 shrink-0">
          
          {/* Greeting + Elder Name */}
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              {timeInfo.greeting}, <span className="text-cyan-300">{userName}</span>
            </h2>
          </div>

          {/* Day and Date */}
          <p className="text-sm sm:text-base font-semibold text-blue-200/90 tracking-wide">
            {timeInfo.formattedDate}
          </p>

          {/* Large Live Sliding Clock */}
          <div className="flex items-center gap-4 pt-1">
            <div className="flex items-baseline">
              <SlidingTimeDisplay
                hours={timeInfo.hours}
                minutes={timeInfo.minutes}
                period={timeInfo.period}
                className="text-4xl sm:text-5xl md:text-6xl font-black text-white"
                digitClassName="text-white drop-shadow-[0_2px_10px_rgba(255,255,255,0.15)]"
                periodClassName="text-sm sm:text-base md:text-lg font-black text-cyan-300 bg-cyan-950/70 border border-cyan-500/40 px-2.5 py-1 rounded-xl shadow-inner align-middle inline-block"
                colonClassName="text-cyan-400"
              />
            </div>

            {/* Subtle Live Pulse Badge */}
            <div 
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold text-emerald-300 bg-emerald-950/60 border border-emerald-500/30 select-none shadow-sm"
              title="Real-time synchronized clock"
            >
              <span 
                className={`w-2 h-2 rounded-full bg-emerald-400 ${
                  shouldReduceMotion ? '' : 'animate-pulse'
                }`} 
              />
              <span>Live</span>
            </div>
          </div>
        </div>

        {/* ================================================================ */}
        {/* RIGHT: Meaningful Daily Context / Next Priority Action           */}
        {/* ================================================================ */}
        <div className="flex-1 lg:max-w-md w-full">
          <div className="rounded-2xl bg-slate-950/70 border border-white/10 p-4 sm:p-5 shadow-inner backdrop-blur-md">
            
            {/* Header: Next on Schedule */}
            <div className="flex items-center justify-between gap-2 mb-3">
              <span className="text-xs uppercase font-extrabold text-blue-400 tracking-wider flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-cyan-400" />
                <span>Next on your schedule</span>
              </span>
              {onViewSchedule && (
                <button
                  type="button"
                  onClick={onViewSchedule}
                  className="text-xs text-slate-400 hover:text-cyan-300 transition-colors font-medium flex items-center gap-1 cursor-pointer"
                >
                  <span>View day</span>
                  <ChevronRight className="w-3 h-3" />
                </button>
              )}
            </div>

            {/* Case 1: Upcoming Medicine */}
            {nextMedicine ? (
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0 mt-0.5">
                    <Pill className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base sm:text-lg font-bold text-white leading-tight">
                      {nextMedicine.medicine_name}
                    </h3>
                    <p className="text-xs sm:text-sm text-slate-300 mt-0.5 font-medium">
                      {nextMedicine.dosage ? `${nextMedicine.dosage} · ` : ''}
                      Scheduled for <span className="text-amber-400 font-bold">{nextMedicine.reminder_time}</span>
                    </p>
                  </div>
                </div>

                {onTakeMedicine && (
                  <button
                    type="button"
                    onClick={(e) => onTakeMedicine(nextMedicine.id, e)}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md shadow-emerald-600/25 transition-all flex items-center justify-center gap-1.5 cursor-pointer shrink-0 min-h-[44px] active:scale-95"
                    aria-label={`Mark ${nextMedicine.medicine_name} as taken`}
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Take Now</span>
                  </button>
                )}
              </div>
            ) : nextAppointment ? (
              /* Case 2: Upcoming Calendar Appointment */
              <div className="flex items-start gap-3 pt-1">
                <div className="w-10 h-10 rounded-xl bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-300 shrink-0 mt-0.5">
                  <Calendar className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base sm:text-lg font-bold text-white leading-tight">
                    {nextAppointment.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-300 mt-0.5 font-medium">
                    Scheduled at <span className="text-cyan-300 font-bold">{nextAppointment.reminder_time || nextAppointment.start_time || 'Today'}</span>
                  </p>
                </div>
              </div>
            ) : (
              /* Case 3: All caught up (Truthful Healthcare Empty State) */
              <div className="flex items-center gap-3 pt-1">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm sm:text-base font-bold text-white">
                    You're all caught up for now
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    No pending medicines or appointments due at this moment.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
