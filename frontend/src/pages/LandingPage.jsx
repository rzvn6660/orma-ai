import { useEffect } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { 
  HeartPulse, 
  Mic, 
  Activity, 
  ShieldCheck, 
  BrainCircuit, 
  Users, 
  Pill, 
  Globe, 
  ChevronRight, 
  LockKeyhole, 
  Zap, 
  Sparkles, 
  CheckCircle2,
  ChevronDown
} from 'lucide-react';
import Lenis from 'lenis';
import BrandLogo from '../components/BrandLogo';
import DashboardPreviewShowcase from '../components/DashboardPreviewShowcase';
import OrmaPlatformPillars from '../components/landing/OrmaPlatformPillars';
import AnimatedHeroHeadline from '../components/landing/AnimatedHeroHeadline';
import TextReveal from '../components/ui/TextReveal';
import SparklesCore from '../components/ui/SparklesCore';

export default function LandingPage({ onTryDemo }) {
  // 1. Initialize Lenis Smooth Scroll (respecting reduced motion)
  useEffect(() => {
    const isReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (isReduced) return;

    const lenis = new Lenis({
      duration: 1.1,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
      wheelMultiplier: 0.95,
      touchMultiplier: 1.5,
      infinite: false,
    });

    let rafId;
    function raf(time) {
      lenis.raf(time);
      rafId = requestAnimationFrame(raf);
    }

    rafId = requestAnimationFrame(raf);

    return () => {
      cancelAnimationFrame(rafId);
      lenis.destroy();
    };
  }, []);

  // 2. Very Light Parallax on Decorative Ambient Glows (15–20px max)
  const { scrollYProgress } = useScroll();
  const bgGlowY1 = useTransform(scrollYProgress, [0, 1], [0, -25]);
  const bgGlowY2 = useTransform(scrollYProgress, [0, 1], [0, 25]);

  const features = [
    { icon: Mic, title: "Voice AI Companion", desc: "Hands-free, empathetic voice interaction tailored for elderly users with zero learning curve." },
    { icon: Globe, title: "Multilingual Support", desc: "Native regional language support including Malayalam, English, and auto dialect recognition." },
    { icon: Pill, title: "Smart Reminders", desc: "Intelligent medicine scheduling with voice verification and automated adherence logging." },
    { icon: Activity, title: "Emergency Alert Engine", desc: "Automated alert triggers based on speech cues, missed doses, and confusion detection." },
    { icon: HeartPulse, title: "Emotional Wellness", desc: "Cognitive sentiment tracking to identify early confusion or emotional distress." },
    { icon: ShieldCheck, title: "Caregiver Dashboard", desc: "Real-time remote monitoring for family members with secure role isolation." },
    { icon: BrainCircuit, title: "Contextual Memory System", desc: "Persistent memory recall for personal events, past conversations, and medical history." },
    { icon: LockKeyhole, title: "Clinical Governance", desc: "Role-based access control, encrypted logs, and strict privacy architecture." },
  ];

  const stack = [
    "React 19", "Vite 8", "FastAPI", "Faster-Whisper", "Groq / Gemini AI", "SQLAlchemy", "WebSockets", "Tesseract OCR", "TailwindCSS"
  ];

  const vision = [
    { title: "Offline Local Execution", desc: "On-device speech processing for zero latency and privacy isolation." },
    { title: "Smart Home Appliances", desc: "Hardware integration with Raspberry Pi and standalone speaker hubs." },
    { title: "Regional & Tribal Dialects", desc: "Expanding speech AI to specialized local linguistic groups." },
    { title: "IoT Smart Dispenser", desc: "Direct hardware telemetry connecting physical pill boxes to ORMA AI." }
  ];

  // Natural waveform heights mimicking speech activity
  const waveformHeights = [10, 18, 28, 16, 32, 22, 14, 26, 12];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 font-sans overflow-x-clip selection:bg-blue-500/30 selection:text-blue-200">
      
      {/* ==================================================================== */}
      {/* Subtle Background Ambient Depth Glows (with gentle 15-25px parallax) */}
      {/* ==================================================================== */}
      <motion.div 
        style={{ y: bgGlowY1 }}
        className="fixed top-[-15%] left-[-10%] w-[50%] h-[50%] rounded-full bg-gradient-to-br from-blue-900/20 via-indigo-900/10 to-transparent blur-[140px] pointer-events-none" 
      />
      <motion.div 
        style={{ y: bgGlowY2 }}
        className="fixed top-[25%] right-[-10%] w-[45%] h-[45%] rounded-full bg-gradient-to-tl from-purple-900/15 via-blue-950/15 to-transparent blur-[140px] pointer-events-none" 
      />

      {/* ==================================================================== */}
      {/* Navigation Header (Fixed Height 4rem / 64px)                         */}
      {/* ==================================================================== */}
      <nav className="fixed w-full z-50 top-0 h-16 border-b border-slate-800/60 bg-slate-950/85 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-full flex justify-between items-center">
          <BrandLogo 
            className="h-8 sm:h-9" 
            textClassName="text-xl sm:text-2xl font-bold tracking-tight" 
            textColor="text-white" 
            accentColor="text-blue-400" 
            animated={true}
          />
          <div className="flex items-center gap-3">
            <button 
              onClick={onTryDemo} 
              className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-5 py-2 rounded-full font-bold text-xs sm:text-sm shadow-md shadow-blue-500/20 hover:shadow-blue-500/40 transition-all hover:scale-[1.02] cursor-pointer flex items-center gap-1.5"
            >
              <span>Get Started</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </nav>

      {/* ==================================================================== */}
      {/* 🚨 HERO SECTION — EXACTLY PRESERVED AS REQUIRED                      */}
      {/* ==================================================================== */}
      <section className="relative mt-16 min-h-[calc(100svh-4rem)] lg:min-h-[calc(100vh-4rem)] flex flex-col justify-between pt-6 sm:pt-8 lg:pt-10 pb-6 sm:pb-8 px-6 max-w-7xl mx-auto z-10">
        {/* Subtle Background Sparkles Layer (21st.dev Manu Arora inspired, low density & calm) */}
        <div className="absolute inset-0 w-full h-full pointer-events-none -z-10 overflow-hidden">
          <SparklesCore
            id="hero-sparkles"
            background="transparent"
            minSize={0.4}
            maxSize={1.4}
            particleDensity={45}
            className="w-full h-full [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black_75%)]"
            particleColor="#38bdf8"
            speed={0.5}
          />
        </div>
        
        {/* Main Grid: Vertically Centered Content */}
        <div className="my-auto grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
          
          {/* Left Column: Headline, Subtitle, CTAs, Pillars */}
          <div className="lg:col-span-7 flex flex-col items-start text-left">
            <motion.div 
              initial={{ opacity: 0, y: 15 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ duration: 0.5 }}
            >
              {/* Product Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-300 text-xs font-semibold tracking-wide mb-4">
                <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                <span>AI Memory Assistant for Elderly Care</span>
              </div>

              {/* 21st.dev Animated Hero Headline */}
              <AnimatedHeroHeadline />

              {/* Subtitle */}
              <p className="text-sm sm:text-base text-slate-400 max-w-xl leading-relaxed mb-6 font-normal">
                ORMA AI helps elderly individuals remember daily medicines, communicate seamlessly in regional languages like Malayalam, and keeps caregivers informed in real time.
              </p>

              {/* Hero CTA Buttons */}
              <div className="flex flex-wrap items-center gap-3.5 mb-6">
                <button 
                  onClick={onTryDemo} 
                  className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-6 py-3 rounded-xl font-bold text-sm sm:text-base shadow-[0_0_25px_rgba(59,130,246,0.3)] transition-all hover:scale-[1.02] flex items-center justify-center gap-2 cursor-pointer"
                >
                  <span>Try ORMA Demo</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
                <a 
                  href="#pillars" 
                  className="px-6 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700/70 text-slate-200 font-semibold text-sm sm:text-base transition-all hover:border-slate-500 flex items-center gap-1.5"
                >
                  Explore Features
                </a>
              </div>

              {/* Genuine Capability Feature Tags (Stable) */}
              <div className="pt-4 border-t border-slate-800/80 w-full">
                <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-2.5">Core Platform Pillars</p>
                <div className="flex flex-wrap gap-2">
                  <span className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-xs font-medium flex items-center gap-1.5">
                    <Mic className="w-3.5 h-3.5 text-cyan-400" /> Voice Assistant
                  </span>
                  <span className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-xs font-medium flex items-center gap-1.5">
                    <BrainCircuit className="w-3.5 h-3.5 text-purple-400" /> AI Memory
                  </span>
                  <span className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-xs font-medium flex items-center gap-1.5">
                    <Pill className="w-3.5 h-3.5 text-emerald-400" /> Smart Reminders
                  </span>
                  <span className="px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 text-xs font-medium flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5 text-blue-400" /> Family Connect
                  </span>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Right Column: Visually Stable Companion Card */}
          <div className="lg:col-span-5 relative">
            <div className="relative rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950 border border-slate-800/80 p-5 sm:p-6 shadow-2xl backdrop-blur-xl">
              
              {/* Top Bar Status — STABLE */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/70 mb-4">
                <div className="flex items-center gap-2.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                  <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400">ORMA Live Companion Active</span>
                </div>
                <span className="text-[11px] font-medium text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded-md">Asia/Kolkata</span>
              </div>

              {/* Central Interaction Area — STABLE MICROPHONE + ONLY ANIMATED WAVEFORM */}
              <div className="flex flex-col items-center justify-center py-2 text-center">
                
                {/* Microphone Orb — STABLE (Static soft glow) */}
                <div className="relative mb-3">
                  <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-slate-900 via-blue-950 to-slate-900 border-2 border-cyan-400/40 shadow-[0_0_20px_rgba(34,211,238,0.2)] flex items-center justify-center">
                    <Mic className="w-8 h-8 text-cyan-400" />
                  </div>
                </div>

                {/* 🚨 ONLY ANIMATED ELEMENT: Voice Waveform / Audio Visualizer */}
                <div className="h-7 flex items-center gap-1 mb-3 justify-center overflow-hidden select-none" aria-label="Live Voice Activity Waveform">
                  {waveformHeights.map((h, i) => (
                    <motion.div 
                      key={i}
                      animate={{ height: [8, h, 8] }}
                      transition={{ 
                        duration: 1.1, 
                        repeat: Infinity, 
                        repeatType: "reverse", 
                        delay: i * 0.12, 
                        ease: "easeInOut" 
                      }}
                      className="w-1 rounded-full bg-gradient-to-t from-blue-500 to-cyan-400 opacity-90 motion-reduce:animate-none"
                      style={{ minHeight: '6px' }}
                    />
                  ))}
                </div>

                {/* Question & Malayalam Response — STABLE */}
                <p className="text-slate-200 font-semibold text-sm mb-1">"Did I take my morning medicine?"</p>
                <p className="text-cyan-400 text-xs sm:text-sm font-medium">"അതെ, നിങ്ങളുടെ Amlodipine കഴിച്ചിട്ടുണ്ട്."</p>
              </div>

              {/* Live Widgets — STABLE */}
              <div className="mt-4 space-y-2.5">
                
                {/* Medicine Status Widget — STABLE */}
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 shrink-0">
                      <Pill className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-white leading-none mb-1">Amlodipine 5mg</p>
                      <p className="text-[10px] text-slate-400 leading-none">Confirmed at 08:00 AM</p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-bold tracking-wider">TAKEN</span>
                </div>

                {/* Caregiver Telemetry Widget — STABLE */}
                <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-400 shrink-0">
                      <Users className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-white leading-none mb-1">Caregiver Telemetry</p>
                      <p className="text-[10px] text-slate-400 leading-none">Linked to Family Dashboard</p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 text-[10px] font-bold tracking-wider">ONLINE</span>
                </div>

              </div>

            </div>
          </div>

        </div>

        {/* Subtle Ambient Section Transition Boundary */}
        <div className="pt-4 flex flex-col items-center justify-center pointer-events-none select-none">
          <a href="#pillars" className="pointer-events-auto flex flex-col items-center text-slate-500 hover:text-blue-400 transition-colors group">
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500 group-hover:text-blue-400 transition-colors mb-1">Explore Ecosystem</span>
            <ChevronDown className="w-4 h-4 animate-bounce text-slate-500 group-hover:text-blue-400" />
          </a>
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 2. MAIN SPECIAL EFFECT: ORMA PLATFORM PILLARS (HORIZONTAL SCROLL)    */}
      {/* ==================================================================== */}
      <div id="pillars">
        <OrmaPlatformPillars />
      </div>

      {/* ==================================================================== */}
      {/* 3. ALL FEATURES GRID (Subtle Section Reveal)                          */}
      {/* ==================================================================== */}
      <section 
        id="features" 
        className="py-20 relative z-10 bg-slate-900/40 border-y border-slate-800/60"
      >
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-14">
            <TextReveal>
              <h2 className="text-3xl md:text-4xl font-extrabold text-white mb-4">Complete AI Healthcare Ecosystem</h2>
            </TextReveal>
            <p className="text-slate-400 max-w-2xl mx-auto text-base">
              Designed specifically to bridge senior independence with reliable caregiver oversight.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feat, idx) => (
              <div 
                key={idx} 
                className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800 hover:border-blue-500/40 hover:bg-slate-900/90 transition-all group shadow-lg"
              >
                <div className="w-11 h-11 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
                  <feat.icon className="w-5 h-5 text-blue-400" />
                </div>
                <h3 className="text-base font-bold text-white mb-2">{feat.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 4. LIVE AI COMPANION (Subtle Section Reveal)                          */}
      {/* ==================================================================== */}
      <section className="py-20 relative z-10 max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-block px-3 py-1 bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-bold rounded-full uppercase tracking-wider mb-4">
              Elderly Accessibility
            </div>
            <TextReveal>
              <h2 className="text-3xl md:text-4xl font-extrabold text-white mb-5 leading-tight">
                Calm, Empathetic Voice Experience
              </h2>
            </TextReveal>
            <p className="text-base text-slate-400 mb-6 leading-relaxed">
              No complex buttons or confusing UI elements. Seniors can simply talk naturally. ORMA AI listens, understands emotional sentiment, and answers concise medical facts.
            </p>
            <div className="space-y-3 text-sm">
              <div className="flex items-center gap-3 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Hands-Free Speech Interaction</span>
              </div>
              <div className="flex items-center gap-3 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Regional Language Support (Malayalam & Manglish)</span>
              </div>
              <div className="flex items-center gap-3 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Cognitive Confusion Detection & Reassurance</span>
              </div>
              <div className="flex items-center gap-3 text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Contextual Memory Recall</span>
              </div>
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-0 bg-blue-500/10 blur-[100px] rounded-full pointer-events-none" />
            <div className="relative p-7 rounded-3xl bg-slate-900/90 border border-slate-800 shadow-2xl overflow-hidden text-center">
               <div className="flex flex-col items-center justify-center gap-4 py-6">
                 <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-600 to-cyan-500 shadow-[0_0_30px_rgba(34,211,238,0.3)] flex items-center justify-center border-4 border-slate-950">
                    <Mic className="w-9 h-9 text-white" />
                 </div>
                 <div>
                    <p className="text-cyan-400 font-bold text-base">Listening Mode</p>
                    <p className="text-slate-400 text-sm mt-1">"When is my next appointment?"</p>
                 </div>
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 5. CAREGIVER DASHBOARD SHOWCASE (Subtle Section Reveal)               */}
      {/* ==================================================================== */}
      <section className="py-16 relative z-10 bg-slate-900/40 border-y border-slate-800/60">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="inline-block px-3 py-1 bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold rounded-full uppercase tracking-wider mb-4">
            Remote Monitoring
          </div>
          <TextReveal>
            <h2 className="text-3xl md:text-4xl font-extrabold text-white mb-3">Real-Time Family Caregiver Dashboard</h2>
          </TextReveal>
          <p className="text-base text-slate-400 max-w-3xl mx-auto mb-8">
            Monitor adherence trends, missed medicine alerts, and wellness reports from anywhere with secure role-based access.
          </p>
          
          <DashboardPreviewShowcase />
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 6. PRODUCTION TECHNOLOGY STACK                                       */}
      {/* ==================================================================== */}
      <section className="py-16 relative z-10 max-w-7xl mx-auto px-6 text-center">
        <TextReveal>
          <h2 className="text-3xl md:text-4xl font-extrabold text-white mb-8">Production Architecture</h2>
        </TextReveal>
        <div className="flex flex-wrap justify-center gap-2.5 max-w-4xl mx-auto">
          {stack.map((tech, idx) => (
            <div key={idx} className="px-4 py-2 rounded-full bg-slate-900 border border-slate-800 text-slate-300 font-medium text-xs sm:text-sm">
              {tech}
            </div>
          ))}
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 7. FUTURE HARDWARE & SOFTWARE VISION                                 */}
      {/* ==================================================================== */}
      <section className="py-16 relative z-10 bg-slate-900/40 border-t border-slate-800/60">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <TextReveal>
              <h2 className="text-3xl md:text-4xl font-extrabold text-white mb-3">Future Hardware & Software Vision</h2>
            </TextReveal>
            <p className="text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">ORMA AI is building towards an offline-capable hardware hub and IoT ecosystem.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {vision.map((item, idx) => (
              <div key={idx} className="p-5 rounded-2xl bg-slate-950 border border-slate-800">
                <Zap className="w-6 h-6 text-indigo-400 mb-3" />
                <h3 className="text-base font-bold text-white mb-1.5">{item.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ==================================================================== */}
      {/* 8. FINAL CTA (Liquid Glass Card + Text Reveal)                       */}
      {/* ==================================================================== */}
      <section className="py-20 relative z-10 max-w-7xl mx-auto px-6">
        <div className="relative p-10 md:p-14 rounded-3xl bg-slate-900/70 border border-white/10 shadow-2xl backdrop-blur-2xl text-center overflow-hidden">
          {/* Specular top highlight */}
          <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-transparent pointer-events-none" />
          
          <div className="max-w-2xl mx-auto relative z-10">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-300 text-xs font-semibold tracking-wide mb-4">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              <span>Experience ORMA AI Today</span>
            </div>
            
            <TextReveal>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-4">
                Peace of Mind for Families, <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-purple-400">
                  Independence for Seniors.
                </span>
              </h2>
            </TextReveal>
            
            <p className="text-slate-400 text-sm sm:text-base leading-relaxed mb-8">
              Start your journey with ORMA AI and experience calm, voice-first care management.
            </p>
            <div className="flex justify-center items-center gap-4">
              <button
                type="button"
                onClick={onTryDemo}
                className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-8 py-3.5 rounded-2xl font-bold text-base shadow-[0_0_25px_rgba(59,130,246,0.3)] transition-all hover:scale-[1.02] flex items-center gap-2 cursor-pointer"
              >
                <span>Try ORMA Demo</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-6 border-t border-slate-800/60 text-center text-slate-500 text-xs relative z-10">
        <p>© 2026 ORMA AI. AI Memory Assistant for Senior Care & Family Health.</p>
      </footer>
    </div>
  );
}
