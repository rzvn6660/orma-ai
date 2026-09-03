import { motion } from 'framer-motion';
import { User, Volume2, Clock, MessageSquare, Heart } from 'lucide-react';
import { tts } from '../services/tts';

export default function ConversationsPage({ messages = [], user }) {
  const safeMessages = Array.isArray(messages) ? messages.filter(Boolean) : [];

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col gap-6">
      <div>
        <h2 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
          Conversation History
        </h2>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">
          Review your recent voice and text interactions with ORMA.
        </p>
      </div>

      <div className="bg-slate-950/70 border border-white/10 rounded-3xl p-5 sm:p-6 flex flex-col gap-5 min-h-[300px]">
        {safeMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center text-slate-400">
            <MessageSquare className="w-10 h-10 text-slate-600 mb-3" />
            <p className="text-sm font-semibold text-slate-300">No past conversations yet</p>
            <p className="text-xs text-slate-500 mt-1">
              Tap the Voice Orb in the Live Companion to ask ORMA anything.
            </p>
          </div>
        ) : (
          safeMessages.map((msg, idx) => (
            <motion.div 
              key={msg.id || `hist_${idx}_${msg.sender}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex items-start gap-3.5 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
            >
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-md ${
                msg.sender === 'user' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-cyan-600/30 border border-cyan-400/50 text-cyan-300'
              }`}>
                {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Heart className="w-4 h-4" />}
              </div>
              
              {/* Message Bubble */}
              <div className={`flex flex-col gap-1 max-w-[85%] ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`px-4 py-3 rounded-2xl ${
                  msg.sender === 'user' 
                    ? 'bg-blue-600/25 border border-blue-500/30 text-white rounded-tr-sm' 
                    : 'bg-slate-900 border border-white/10 text-white rounded-tl-sm'
                }`}>
                  <p className="text-sm sm:text-base leading-relaxed">{msg.text}</p>
                </div>
                
                <div className="flex items-center gap-3 mt-0.5 px-1">
                  <span className="text-[11px] text-slate-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" /> {msg.time || 'Today'}
                  </span>
                  
                  {msg.sender === 'ai' && msg.text && (
                    <button 
                      type="button"
                      onClick={() => tts.speak(msg.text)}
                      className="text-[11px] text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1 transition-colors cursor-pointer"
                    >
                      <Volume2 className="w-3 h-3" /> Replay
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
