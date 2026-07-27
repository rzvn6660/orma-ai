import { motion } from 'framer-motion';
import { Mic } from 'lucide-react';

export default function HeroSection({ user }) {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const name = user?.name || user?.email?.split('@')[0] || 'Guest';

  return (
    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-6">
      
      {/* Title & Subtitle */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="flex-1"
      >
        <h1 className="text-4xl md:text-5xl font-extrabold text-white tracking-tight mb-2">
          {getGreeting()}, <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400">{name}</span>
        </h1>
        <p className="text-lg text-slate-400 font-medium">
          Orma AI Memory Assistant for Elderly Care
        </p>
      </motion.div>

    </div>
  );
}
