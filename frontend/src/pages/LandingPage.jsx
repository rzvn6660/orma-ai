import { motion } from 'framer-motion';
import { HeartPulse, Mic, Activity, ShieldCheck, BrainCircuit, Users, Pill, Globe, ChevronRight, Lock, Zap, Server, Cpu } from 'lucide-react';
import BrandLogo from '../components/BrandLogo';
import DashboardPreviewShowcase from '../components/DashboardPreviewShowcase';

export default function LandingPage({ onTryDemo }) {
  const features = [
    { icon: Mic, title: "Voice AI", desc: "Hands-free, companion-mode voice interaction for effortless communication." },
    { icon: Globe, title: "Multilingual Support", desc: "Native support for regional languages including Malayalam." },
    { icon: Pill, title: "Medicine Reminders", desc: "Smart tracking with voice and manual confirmation capabilities." },
    { icon: Activity, title: "Emergency Detection", desc: "Automated alert triggers based on speech and wellness patterns." },
    { icon: HeartPulse, title: "Emotion Monitoring", desc: "Advanced cognitive and sentiment analysis during interactions." },
    { icon: ShieldCheck, title: "Caregiver Dashboard", desc: "Secure role-based access for family members to monitor adherence." },
    { icon: BrainCircuit, title: "AI Memory System", desc: "Persistent contextual memory for fluid, natural follow-up conversations." },
  ];

  const stack = [
    "React", "FastAPI", "Whisper AI", "Llama 3", "SQLAlchemy", "WebSockets", "OCR Integration", "TailwindCSS"
  ];

  const vision = [
    { title: "Offline Mode", desc: "On-device processing for privacy and zero latency." },
    { title: "Raspberry Pi", desc: "Hardware integration for standalone home appliances." },
    { title: "Tribal Languages", desc: "Expanding inclusivity to highly marginalized linguistic groups." },
    { title: "IoT Pill Box", desc: "Direct hardware integration to detect physical pill dispensing." }
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 font-sans overflow-x-hidden selection:bg-blue-500/30 selection:text-blue-200">
      {/* Dynamic Backgrounds */}
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-900/20 blur-[120px] pointer-events-none" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-900/20 blur-[120px] pointer-events-none" />

      {/* Navbar */}
      <nav className="fixed w-full z-50 top-0 border-b border-slate-800/50 bg-slate-950/50 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <BrandLogo 
            className="h-10" 
            textClassName="text-2xl" 
            textColor="text-white" 
            accentColor="text-blue-400" 
          />
          <button onClick={onTryDemo} className="bg-white/10 hover:bg-white/20 text-white px-5 py-2 rounded-full font-medium transition-colors border border-white/10">
            Login / Signup
          </button>
        </div>
      </nav>

      {/* 1. Hero Section */}
      <section className="relative pt-40 pb-20 px-6 max-w-7xl mx-auto flex flex-col items-center text-center z-10">
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
          <div className="inline-block mb-4 px-4 py-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-400 text-sm font-bold tracking-wide uppercase">
            The Future of Assisted Care
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold text-white tracking-tight leading-tight mb-6">
            AI Memory Assistant <br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400">
              for Elderly Care
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-slate-400 max-w-3xl mx-auto mb-10 leading-relaxed">
            Voice-powered multilingual healthcare companion for elderly wellness and caregiver monitoring. Seamlessly bridging the gap between independence and medical safety.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button onClick={onTryDemo} className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-8 py-4 rounded-full font-bold text-lg shadow-[0_0_30px_rgba(59,130,246,0.4)] transition-all hover:scale-105 flex items-center justify-center gap-2">
              Try Demo <ChevronRight className="w-5 h-5" />
            </button>
            <a href="#features" className="orma-btn-secondary">
              View Features
            </a>
          </div>
        </motion.div>
      </section>

      {/* 2. Features Section */}
      <section id="features" className="py-24 relative z-10 bg-slate-900/50 border-y border-slate-800/50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Comprehensive Healthcare Ecosystem</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">Everything you need to ensure the safety and wellbeing of your loved ones, powered by state-of-the-art AI.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feat, idx) => (
              <motion.div key={idx} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: idx * 0.1 }} className="p-6 rounded-3xl bg-slate-800/40 border border-slate-700/50 hover:bg-slate-800/80 transition-colors group">
                <feat.icon className="w-10 h-10 text-blue-400 mb-4 group-hover:scale-110 transition-transform" />
                <h3 className="text-xl font-bold text-white mb-2">{feat.title}</h3>
                <p className="text-sm text-slate-400">{feat.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* 3. AI Voice Experience & 4. Benefits */}
      <section className="py-24 relative z-10 max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <motion.div initial={{ opacity: 0, x: -30 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }}>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">Live AI Companion Mode</h2>
            <p className="text-lg text-slate-400 mb-8">
              Transforming interaction with voice support. Simply tap the microphone to speak. The AI understands deep conversational context and responds with a calm, empathetic tone.
            </p>
            <ul className="space-y-4">
              <li className="flex items-center gap-3"><CheckBadge /> Conversational Interaction</li>
              <li className="flex items-center gap-3"><CheckBadge /> Multilingual Speech AI (Malayalam)</li>
              <li className="flex items-center gap-3"><CheckBadge /> Emotional Support & Companionship</li>
              <li className="flex items-center gap-3"><CheckBadge /> Contextual Memory Tracking</li>
            </ul>
          </motion.div>
          <motion.div initial={{ opacity: 0, x: 30 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} className="relative">
            <div className="absolute inset-0 bg-blue-500/20 blur-[100px] rounded-full" />
            <div className="relative p-8 rounded-3xl bg-slate-900/80 border border-slate-700/50 shadow-2xl overflow-hidden">
               <div className="flex flex-col items-center justify-center gap-6 py-10">
                 <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 animate-pulse shadow-[0_0_50px_rgba(34,211,238,0.5)] flex items-center justify-center border-4 border-slate-900">
                    <Mic className="w-12 h-12 text-white" />
                 </div>
                 <div className="text-center">
                    <p className="text-cyan-400 font-bold text-lg">Listening...</p>
                    <p className="text-slate-400 text-sm mt-1">"Did I take my pill today?"</p>
                 </div>
               </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* 5. Caregiver Dashboard Showcase */}
      <section className="py-12 md:py-16 relative z-10 bg-slate-900/50 border-y border-slate-800/50">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Real-Time Caregiver Dashboard</h2>
          <p className="text-base sm:text-lg text-slate-400 max-w-3xl mx-auto mb-10">
            Monitor adherence analytics, emergency alerts, and emotional wellness indicators from anywhere. Protect your family with secure, role-based linking.
          </p>
          
          <DashboardPreviewShowcase />
        </div>
      </section>

      {/* 6. Technology Stack */}
      <section className="py-24 relative z-10 max-w-7xl mx-auto px-6 text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-12">Production-Ready Technology</h2>
        <div className="flex flex-wrap justify-center gap-4">
          {stack.map((tech, idx) => (
            <div key={idx} className="px-6 py-3 rounded-full bg-slate-800/50 border border-slate-700/50 text-slate-300 font-medium">
              {tech}
            </div>
          ))}
        </div>
      </section>

      {/* 8. Future Vision */}
      <section className="py-24 relative z-10 bg-slate-900/50 border-t border-slate-800/50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">The Future Vision</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">Orma AI is evolving into a fully integrated hardware and software ecosystem.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {vision.map((item, idx) => (
              <div key={idx} className="p-6 rounded-2xl bg-slate-950 border border-slate-800">
                <Zap className="w-8 h-8 text-indigo-400 mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">{item.title}</h3>
                <p className="text-sm text-slate-400">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 border-t border-slate-800/50 text-center text-slate-500 relative z-10">
        <p>© 2026 Orma AI. Built for the future of healthcare.</p>
      </footer>
    </div>
  );
}

function CheckBadge() {
  return (
    <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0">
      <div className="w-2 h-2 rounded-full bg-emerald-400" />
    </div>
  );
}
