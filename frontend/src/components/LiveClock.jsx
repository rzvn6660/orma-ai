import { useState, useEffect } from 'react';
import { Clock, Globe } from 'lucide-react';
import { motion } from 'framer-motion';

export default function LiveClock({ timezone }) {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const timeString = currentTime.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: timezone || Intl.DateTimeFormat().resolvedOptions().timeZone
  });

  const displayTimezone = timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;

  return (
    <motion.div 
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col sm:flex-row items-center gap-4 bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-4 shadow-lg"
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
          <Clock className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Current Time</p>
          <p className="text-xl font-bold text-white">{timeString}</p>
        </div>
      </div>
      
      <div className="hidden sm:block w-px h-10 bg-slate-700/50"></div>
      
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center">
          <Globe className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Timezone</p>
          <p className="text-sm font-medium text-slate-200">{displayTimezone}</p>
        </div>
      </div>
    </motion.div>
  );
}
