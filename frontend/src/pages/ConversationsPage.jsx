import { motion } from 'framer-motion';
import { User, Volume2, Clock } from 'lucide-react';
import { tts } from '../services/tts';

export default function ConversationsPage({ messages, user }) {
  return (
    <div className="w-full max-w-4xl mx-auto h-[calc(100vh-120px)] flex flex-col">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Conversation History</h1>
        <p className="text-slate-400">Review your past interactions with Orma AI.</p>
      </div>

      <div className="flex-1 bg-slate-900 border border-slate-800 rounded-3xl p-6 overflow-y-auto custom-scrollbar flex flex-col gap-6">
        {messages.map((msg) => (
          <motion.div 
            key={msg.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex items-start gap-4 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
          >
            {/* Avatar */}
            <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${
              msg.sender === 'user' ? 'bg-blue-600' : 'bg-gradient-to-br from-indigo-500 to-purple-600'
            }`}>
              {msg.sender === 'user' ? <User className="w-5 h-5 text-white" /> : <span className="text-white font-bold">AI</span>}
            </div>
            
            {/* Message Bubble */}
            <div className={`flex flex-col gap-1 max-w-[80%] ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`px-5 py-3.5 rounded-2xl ${
                msg.sender === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-sm' 
                  : 'bg-slate-800 border border-slate-700/50 text-white rounded-tl-sm'
              }`}>
                <p className="text-lg leading-relaxed">{msg.text}</p>
              </div>
              
              <div className="flex items-center gap-3 mt-1">
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {msg.time}
                </span>
                
                {msg.sender === 'ai' && (
                  <button 
                    onClick={() => tts.speak(msg.text)}
                    className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1 transition-colors"
                  >
                    <Volume2 className="w-3 h-3" /> Replay
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
