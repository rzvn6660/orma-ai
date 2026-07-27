import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  Pill, 
  Activity, 
  ShieldCheck, 
  Calendar, 
  Clock, 
  Heart, 
  Droplets, 
  Sparkles, 
  Mic, 
  CheckCircle2, 
  Lock,
  RotateCcw
} from 'lucide-react';
import SeniorDemoCharacter from './landing/SeniorDemoCharacter';
import DemoSpeechBubble from './landing/DemoSpeechBubble';

export default function DashboardPreviewShowcase() {
  // Deterministic Animation Sequence:
  // 'idle' | 'walking' | 'turning' | 'asking' | 'listening' | 'thinking' | 'responding' | 'highlighting' | 'acknowledging' | 'completed'
  const [step, setStep] = useState('idle');

  // DOM Refs for dynamic offset calculations
  const containerRef = useRef(null);
  const characterRef = useRef(null);
  const ormaCardRef = useRef(null);
  const timerRef = useRef([]);

  const [targetOffset, setTargetOffset] = useState({ x: 0, y: 0 });
  const [isMobile, setIsMobile] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  // Responsiveness and Reduced Motion listener
  useEffect(() => {
    const updateDimensions = () => {
      const mobileCheck = window.innerWidth < 1024;
      setIsMobile(mobileCheck);

      const motionCheck = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      setReducedMotion(motionCheck);
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Compute horizontal movement offset dynamically relative to DOM geometry
  const computeTargetOffset = () => {
    if (characterRef.current && ormaCardRef.current) {
      const charRect = characterRef.current.getBoundingClientRect();
      const ormaRect = ormaCardRef.current.getBoundingClientRect();
      
      // Horizontal offset stopping ~24px left of the ORMA companion card along baseline
      const deltaX = (ormaRect.left - charRect.left) - 24;
      setTargetOffset({ x: deltaX, y: 0 });
    }
  };

  // Helper to safely clear pending timers
  const clearAllTimers = () => {
    timerRef.current.forEach(clearTimeout);
    timerRef.current = [];
  };

  // Start Deterministic Interactive Demo Sequence
  const handleStartDemo = () => {
    if (step !== 'idle' && step !== 'completed') return;
    clearAllTimers();
    computeTargetOffset();

    setStep('walking');

    // Step 3: Turning / Settling at ORMA card
    const t1 = setTimeout(() => {
      setStep('turning');
    }, 2200);

    // Step 4: Asking Question (Speech bubble follows character)
    const t2 = setTimeout(() => {
      setStep('asking');
    }, 2700);

    // Step 5: ORMA Listening
    const t3 = setTimeout(() => {
      setStep('listening');
    }, 4000);

    // Step 6: ORMA Thinking (checking care plan)
    const t4 = setTimeout(() => {
      setStep('thinking');
    }, 5200);

    // Step 7: ORMA Responding
    const t5 = setTimeout(() => {
      setStep('responding');
    }, 6200);

    // Step 8: Highlighting Vitamin D care plan item
    const t6 = setTimeout(() => {
      setStep('highlighting');
    }, 7600);

    // Step 9: Grandfather Acknowledgment
    const t7 = setTimeout(() => {
      setStep('acknowledging');
    }, 9000);

    // Step 10: Completed
    const t8 = setTimeout(() => {
      setStep('completed');
    }, 10400);

    timerRef.current = [t1, t2, t3, t4, t5, t6, t7, t8];
  };

  // Clean Reset/Replay handler
  const handleReplay = () => {
    clearAllTimers();
    setStep('idle');
  };

  // Clean up timers on unmount
  useEffect(() => {
    return () => clearAllTimers();
  }, []);

  // Motion variants for initial viewport appearance
  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: [0.22, 1, 0.36, 1],
        staggerChildren: 0.06
      }
    }
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 12 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] }
    }
  };

  const isCarePlanHighlighted = step === 'highlighting' || step === 'acknowledging' || step === 'completed';
  const isOrmaResponding = step === 'responding' || step === 'highlighting' || step === 'acknowledging' || step === 'completed';

  return (
    <motion.div
      ref={containerRef}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-40px" }}
      variants={containerVariants}
      className="relative mx-auto max-w-5xl text-left"
    >
      {/* Browser Mockup Frame with 16:9 / 16:10 aspect ratio optimization */}
      <div className="rounded-2xl border border-slate-700/80 bg-slate-950 p-2 sm:p-3 shadow-2xl shadow-blue-950/30 ring-1 ring-white/5">
        <div className="rounded-xl border border-slate-800/90 bg-slate-950 overflow-hidden flex flex-col">
          
          {/* Browser Header Bar */}
          <div className="h-10 border-b border-slate-800/80 bg-slate-900/90 px-4 flex items-center justify-between gap-3 select-none">
            {/* Traffic Light Controls */}
            <div className="flex items-center gap-2 shrink-0" aria-hidden="true">
              <div className="w-3 h-3 rounded-full bg-red-500/80 border border-red-400/30" />
              <div className="w-3 h-3 rounded-full bg-amber-500/80 border border-amber-400/30" />
              <div className="w-3 h-3 rounded-full bg-emerald-500/80 border border-emerald-400/30" />
            </div>

            {/* Mock Browser Identifier */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-slate-950/80 border border-slate-800/80 rounded-full text-xs text-slate-400 max-w-xs w-full justify-center">
              <Lock className="w-3 h-3 text-slate-500 shrink-0" aria-hidden="true" />
              <span className="font-medium tracking-wide">ORMA AI • Product Preview</span>
            </div>

            {/* Single Global Demo Data Label */}
            <div className="flex items-center gap-1.5 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-xs text-blue-400 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse shrink-0" aria-hidden="true" />
              <span className="whitespace-nowrap">Product Preview • Example Data</span>
            </div>
          </div>

          {/* Browser Dashboard Body Content */}
          <div className="p-4 sm:p-5 md:p-6 bg-slate-950 bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(30,58,138,0.12),rgba(255,255,255,0))] relative">
            
            {/* Responsive grid: 2 columns on desktop (left ~60%, right ~40%), stacked on mobile */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-5">
              
              {/* LEFT COLUMN: Daily Overview + Today's Care Plan + Integrated Interaction Stage */}
              <div className="lg:col-span-7 flex flex-col gap-4 sm:gap-5 order-1 lg:order-1 relative">
                
                {/* 1. Daily Overview */}
                <motion.div 
                  variants={cardVariants}
                  className="p-4 sm:p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-md relative overflow-hidden"
                >
                  <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-2xl rounded-full pointer-events-none" aria-hidden="true" />

                  <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
                    <div>
                      <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight">Good Morning</h3>
                      <p className="text-xs sm:text-sm text-slate-400 mt-0.5">Here’s your day with ORMA.</p>
                    </div>

                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300 font-medium shrink-0">
                      <Calendar className="w-3.5 h-3.5 text-blue-400" aria-hidden="true" />
                      <span>Today</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2.5 sm:gap-3">
                    <div className="p-2.5 sm:p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center gap-2">
                      <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0">
                        <Pill className="w-3.5 h-3.5 text-blue-400" aria-hidden="true" />
                      </div>
                      <div>
                        <div className="text-sm sm:text-base font-bold text-white leading-tight">2</div>
                        <div className="text-[10px] sm:text-[11px] text-slate-400 font-medium">Medicines Today</div>
                      </div>
                    </div>

                    <div className="p-2.5 sm:p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center gap-2">
                      <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center shrink-0">
                        <Activity className="w-3.5 h-3.5 text-sky-400" aria-hidden="true" />
                      </div>
                      <div>
                        <div className="text-sm sm:text-base font-bold text-white leading-tight">1</div>
                        <div className="text-[10px] sm:text-[11px] text-slate-400 font-medium">Health Event</div>
                      </div>
                    </div>

                    <div className="p-2.5 sm:p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col sm:flex-row items-start sm:items-center gap-2">
                      <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0">
                        <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" aria-hidden="true" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white leading-tight">Reminders</div>
                        <div className="text-[10px] sm:text-[11px] text-emerald-400 font-medium">Ready</div>
                      </div>
                    </div>
                  </div>
                </motion.div>

                {/* 2. Today's Care Plan (Max 3 Items) */}
                <motion.div 
                  variants={cardVariants}
                  className="p-4 sm:p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-md flex-1 flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-blue-400" aria-hidden="true" />
                      <h4 className="text-base font-bold text-white">Today's Care Plan</h4>
                    </div>
                    <span className="text-xs text-slate-400 font-medium bg-slate-800/60 px-2.5 py-0.5 rounded-full border border-slate-700/50">
                      3 Scheduled
                    </span>
                  </div>

                  {/* Timeline list */}
                  <div className="relative pl-4 space-y-2.5 before:absolute before:left-1.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                    
                    {/* Item 1: Metformin */}
                    <div className="relative flex items-center justify-between gap-3 p-2.5 sm:p-3 rounded-xl bg-slate-950/50 border border-slate-800/60">
                      <div className="absolute -left-[1.375rem] top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-emerald-500 ring-4 ring-slate-950" aria-hidden="true" />
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="text-xs font-medium text-slate-400 w-16 shrink-0">08:00 AM</span>
                        <div className="min-w-0">
                          <div className="text-sm font-bold text-white truncate">Metformin 500 mg</div>
                          <div className="text-[11px] text-slate-400">Medicine Reminder</div>
                        </div>
                      </div>
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                        <CheckCircle2 className="w-3 h-3" aria-hidden="true" /> Completed
                      </span>
                    </div>

                    {/* Item 2: Vitamin D (TARGET HIGHLIGHT ROW FOR DEMO) */}
                    <div 
                      className={`relative flex items-center justify-between gap-3 p-2.5 sm:p-3 rounded-xl transition-all duration-500 ${
                        isCarePlanHighlighted 
                          ? 'bg-blue-950/70 border-2 border-blue-400 shadow-[0_0_25px_rgba(59,130,246,0.4)] ring-2 ring-blue-400/40 scale-[1.02] z-10' 
                          : 'bg-slate-950/50 border border-slate-800/60'
                      }`}
                    >
                      <div 
                        className={`absolute -left-[1.375rem] top-1/2 -translate-y-1/2 w-3 h-3 rounded-full ring-4 ring-slate-950 transition-colors ${
                          isCarePlanHighlighted ? 'bg-cyan-400 animate-ping' : 'bg-blue-500'
                        }`} 
                        aria-hidden="true" 
                      />
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="text-xs font-medium text-slate-400 w-16 shrink-0">01:00 PM</span>
                        <div className="min-w-0">
                          <div className="text-sm font-bold text-white truncate">Vitamin D</div>
                          <div className="text-[11px] text-slate-400">Medicine Reminder</div>
                        </div>
                      </div>
                      <span 
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium rounded-full shrink-0 transition-colors ${
                          isCarePlanHighlighted 
                            ? 'bg-cyan-400/20 text-cyan-300 border border-cyan-400/40 font-bold' 
                            : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                        }`}
                      >
                        <Clock className="w-3 h-3" aria-hidden="true" /> {isCarePlanHighlighted ? 'Next Up' : 'Upcoming'}
                      </span>
                    </div>

                    {/* Item 3: Doctor Appointment */}
                    <div className="relative flex items-center justify-between gap-3 p-2.5 sm:p-3 rounded-xl bg-slate-950/50 border border-slate-800/60">
                      <div className="absolute -left-[1.375rem] top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-indigo-500 ring-4 ring-slate-950" aria-hidden="true" />
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="text-xs font-medium text-slate-400 w-16 shrink-0">04:30 PM</span>
                        <div className="min-w-0">
                          <div className="text-sm font-bold text-white truncate">Dr. Smith</div>
                          <div className="text-[11px] text-slate-400">Doctor Appointment</div>
                        </div>
                      </div>
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0">
                        <Clock className="w-3 h-3" aria-hidden="true" /> Upcoming
                      </span>
                    </div>

                  </div>
                </motion.div>

                {/* GROUNDED INTERACTION STAGE CORRIDOR (NATURAL LOWER BASELINE) */}
                <div className="mt-1 pt-1 relative z-20 flex items-center justify-between">
                  <div 
                    ref={characterRef}
                    className="relative"
                  >
                    <SeniorDemoCharacter
                      step={step}
                      onStartDemo={handleStartDemo}
                      targetOffset={targetOffset}
                      isMobile={isMobile}
                      reducedMotion={reducedMotion}
                    />
                  </div>
                </div>

              </div>

              {/* RIGHT COLUMN: Health Snapshot + ORMA Companion */}
              <div className="lg:col-span-5 flex flex-col gap-4 sm:gap-5 order-2 lg:order-2">
                
                {/* 3. Health Snapshot */}
                <motion.div 
                  variants={cardVariants}
                  className="p-4 sm:p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-md"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <Activity className="w-4 h-4 text-cyan-400" aria-hidden="true" />
                    <h4 className="text-base font-bold text-white">Health Snapshot</h4>
                  </div>

                  <div className="space-y-2">
                    <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center shrink-0">
                          <Heart className="w-3.5 h-3.5 text-rose-400" aria-hidden="true" />
                        </div>
                        <span className="text-xs text-slate-300 font-medium">Blood Pressure</span>
                      </div>
                      <span className="text-xs sm:text-sm font-bold text-white">120/80 <span className="text-[10px] font-normal text-slate-400">mmHg</span></span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center shrink-0">
                          <Activity className="w-3.5 h-3.5 text-rose-400" aria-hidden="true" />
                        </div>
                        <span className="text-xs text-slate-300 font-medium">Heart Rate</span>
                      </div>
                      <span className="text-xs sm:text-sm font-bold text-white">74 <span className="text-[10px] font-normal text-slate-400">bpm</span></span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center shrink-0">
                          <Droplets className="w-3.5 h-3.5 text-cyan-400" aria-hidden="true" />
                        </div>
                        <span className="text-xs text-slate-300 font-medium">SpO₂</span>
                      </div>
                      <span className="text-xs sm:text-sm font-bold text-white">98%</span>
                    </div>
                  </div>
                </motion.div>

                {/* 4. ORMA Companion Target Card */}
                <motion.div 
                  ref={ormaCardRef}
                  variants={cardVariants}
                  className="p-4 sm:p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-md flex-1 flex flex-col justify-between relative overflow-hidden"
                >
                  <div className="flex items-center justify-between mb-3 relative z-10">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-blue-400" aria-hidden="true" />
                      <h4 className="text-base font-bold text-white">ORMA Companion</h4>
                    </div>

                    {/* Status Badge */}
                    <span 
                      className={`text-[11px] px-2.5 py-0.5 rounded-full border font-medium transition-colors ${
                        step === 'listening'
                          ? 'text-cyan-300 bg-cyan-500/20 border-cyan-400/50 animate-pulse'
                          : step === 'thinking'
                          ? 'text-indigo-300 bg-indigo-500/20 border-indigo-400/50 animate-pulse'
                          : 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20'
                      }`}
                    >
                      {step === 'listening' ? 'Listening...' : step === 'thinking' ? 'Checking care plan...' : 'Voice Companion'}
                    </span>
                  </div>

                  {/* AI Visualizer Container (Vertically Centered & Compact) */}
                  <div className="py-4 px-4 rounded-xl bg-slate-950/70 border border-slate-800/80 flex flex-col items-center justify-center text-center relative z-10 flex-1 my-auto">
                    {/* Mic Orb with Dynamic Pulse */}
                    <div className="relative mb-3 flex items-center justify-center">
                      {(step === 'listening' || step === 'thinking') && (
                        <div className="absolute w-14 h-14 rounded-full bg-cyan-400/30 animate-ping" />
                      )}
                      <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-blue-600 to-cyan-400 shadow-[0_0_20px_rgba(59,130,246,0.4)] flex items-center justify-center border-2 border-slate-900">
                        <Mic className="w-5 h-5 text-white" aria-hidden="true" />
                      </div>
                    </div>

                    {/* Prompt or Response */}
                    {!isOrmaResponding ? (
                      <p className="text-xs sm:text-sm font-medium text-white mb-2">
                        “How can I help you today?”
                      </p>
                    ) : (
                      <DemoSpeechBubble 
                        text="Your next medicine is Vitamin D at 1:00 PM."
                        subtitle="Care schedule synchronized"
                        variant="response"
                        className="w-full my-1 text-left"
                      />
                    )}

                    {/* Subtle voice waveform indicator */}
                    <div className="flex items-center justify-center gap-1.5 h-4 mt-2" aria-hidden="true">
                      <span className="w-1 h-2 rounded-full bg-blue-400 waveform-bar" />
                      <span className="w-1 h-4 rounded-full bg-cyan-400 waveform-bar" />
                      <span className="w-1 h-2 rounded-full bg-indigo-400 waveform-bar" />
                      <span className="w-1 h-4.5 rounded-full bg-blue-400 waveform-bar" />
                      <span className="w-1 h-3 rounded-full bg-cyan-400 waveform-bar" />
                      <span className="w-1 h-2 rounded-full bg-indigo-400 waveform-bar" />
                    </div>
                  </div>

                  {/* Completion & Replay Controller Bar */}
                  {step === 'completed' && (
                    <motion.div 
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-3 p-2.5 rounded-xl bg-blue-950/80 border border-blue-500/40 flex items-center justify-between gap-2 text-xs text-white z-20"
                    >
                      <span className="flex items-center gap-1.5 font-medium text-[11px] text-blue-200 truncate">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" aria-hidden="true" />
                        That's ORMA — your healthcare companion.
                      </span>
                      <button
                        onClick={handleReplay}
                        type="button"
                        aria-label="Replay ORMA medication reminder demonstration"
                        className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition-colors flex items-center gap-1 shrink-0 text-xs cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-300"
                      >
                        <RotateCcw className="w-3 h-3" aria-hidden="true" />
                        Replay Demo
                      </button>
                    </motion.div>
                  )}

                </motion.div>

              </div>

            </div>

          </div>

          {/* Browser Footer Status Bar */}
          <div className="h-8 border-t border-slate-800/80 bg-slate-900/90 px-4 flex items-center justify-between text-[11px] text-slate-500 select-none">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" aria-hidden="true" />
              <span>ORMA AI Healthcare Platform</span>
            </div>
            <div className="flex items-center gap-2">
              <span>Interactive Story Demonstration</span>
            </div>
          </div>

        </div>
      </div>
    </motion.div>
  );
}
