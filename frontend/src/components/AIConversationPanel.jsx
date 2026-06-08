import React, { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';

export default function AIConversationPanel({ isListening, isSpeaking, messages, isTranscribing, isThinking }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTranscribing, isThinking]);
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.3 }}
      className="glass-card flex flex-col h-[400px] md:h-[500px] overflow-hidden relative col-span-1 lg:col-span-2"
    >
      {/* Header */}
      <div className="p-5 border-b border-slate-700/50 flex justify-between items-center bg-slate-900/40">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Activity className="text-white w-5 h-5" />
            </div>
            {isListening && (
              <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-slate-900 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
            )}
            {isSpeaking && !isListening && (
              <span className="absolute bottom-0 right-0 w-3 h-3 bg-pink-500 border-2 border-slate-900 rounded-full animate-pulse shadow-[0_0_8px_rgba(236,72,153,0.6)]"></span>
            )}
          </div>
          <div>
            <h2 className="font-semibold text-white">Orma AI</h2>
            <p className="text-xs text-slate-400">
              {isListening ? 'Listening...' : isTranscribing ? 'Transcribing...' : isThinking ? 'Thinking...' : isSpeaking ? 'Speaking...' : 'Online'}
            </p>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div ref={scrollRef} className="flex-1 p-6 overflow-y-auto flex flex-col gap-6 scroll-smooth pb-24">
        {messages.map((msg) => (
          <motion.div 
            key={msg.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`p-4 rounded-2xl max-w-[80%] shadow-lg ${
              msg.sender === 'user' 
                ? 'bg-blue-600 text-white rounded-tr-sm shadow-blue-900/20' 
                : 'bg-slate-800 text-slate-200 rounded-tl-sm border border-slate-700/50'
            }`}>
              <p className="text-[15px] leading-relaxed">{msg.text}</p>
              <span className={`text-[11px] mt-2 block ${msg.sender === 'user' ? 'text-blue-200 text-right' : 'text-slate-400'}`}>
                {msg.time}
              </span>
            </div>
          </motion.div>
        ))}

        {/* Loading Bubble */}
        {(isTranscribing || isThinking) && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`flex ${isThinking ? 'justify-start' : 'justify-end'}`}
          >
            <div className={`p-4 rounded-2xl max-w-[80%] shadow-lg ${
              isThinking 
                ? 'bg-slate-800/50 text-slate-200 rounded-tl-sm border border-slate-700/50'
                : 'bg-blue-600/50 text-white rounded-tr-sm border border-blue-500/30'
            }`}>
              <div className="flex gap-2 items-center h-5">
                <div className={`w-2 h-2 rounded-full animate-bounce ${isThinking ? 'bg-slate-400' : 'bg-blue-200'}`}></div>
                <div className={`w-2 h-2 rounded-full animate-bounce ${isThinking ? 'bg-slate-400' : 'bg-blue-200'}`} style={{ animationDelay: '150ms' }}></div>
                <div className={`w-2 h-2 rounded-full animate-bounce ${isThinking ? 'bg-slate-400' : 'bg-blue-200'}`} style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Animated Waveform when listening or speaking */}
      {(isListening || isSpeaking) && (
        <div className="absolute bottom-0 left-0 w-full h-24 bg-gradient-to-t from-slate-900/80 to-transparent flex items-end justify-center pb-6 gap-1.5 pointer-events-none">
          {[...Array(8)].map((_, i) => (
            <motion.div 
              key={i} 
              animate={{ 
                height: [
                  `${Math.random() * 20 + 10}px`, 
                  `${Math.random() * 50 + 30}px`, 
                  `${Math.random() * 20 + 10}px`
                ] 
              }}
              transition={{ 
                duration: 0.4 + Math.random() * 0.4, 
                repeat: Infinity, 
                ease: "easeInOut",
                delay: Math.random() * 0.2
              }}
              className={`w-1.5 rounded-t-full ${isSpeaking ? 'bg-gradient-to-t from-purple-500 to-pink-400' : 'bg-gradient-to-t from-blue-600 to-cyan-400'}`} 
            />
          ))}
        </div>
      )}
    </motion.div>
  );
}
