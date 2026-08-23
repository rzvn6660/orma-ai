import React, { useRef, useState, useEffect, useCallback } from 'react';
import { motion, useScroll, useTransform, useSpring, useMotionValueEvent } from 'framer-motion';
import { Mic, BrainCircuit, Pill, Users, Sparkles, ArrowRight, ChevronLeft, ChevronRight } from 'lucide-react';

export default function OrmaPlatformPillars() {
  const containerRef = useRef(null);
  const viewportRef = useRef(null);
  const trackRef = useRef(null);
  const mobileScrollRef = useRef(null);

  const [isMobile, setIsMobile] = useState(false);
  const [isReducedMotion, setIsReducedMotion] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [mobileIndex, setMobileIndex] = useState(0);

  const scrollRangeRef = useRef({ startX: 0, endX: 0 });

  const pillars = [
    {
      id: "voice",
      number: "01",
      icon: Mic,
      title: "Talk naturally with ORMA",
      subtitle: "Voice Assistant",
      desc: "Speak naturally and receive helpful, reassuring responses in familiar languages including Malayalam and English.",
      tag: "Natural Speech AI",
      gradient: "from-cyan-500/10 via-slate-900/80 to-slate-950",
      accentBorder: "border-cyan-500/40 group-hover:border-cyan-500/60 shadow-[0_0_30px_rgba(6,182,212,0.15)]",
      iconBg: "bg-cyan-500/15 text-cyan-400 border-cyan-500/30",
      highlight: "Zero learning curve for seniors with hands-free voice recognition."
    },
    {
      id: "memory",
      number: "02",
      icon: BrainCircuit,
      title: "ORMA remembers what matters",
      subtitle: "AI Memory",
      desc: "Important memories, daily routines, personal context, and past conversations stay organized seamlessly.",
      tag: "Contextual Recall",
      gradient: "from-purple-500/10 via-slate-900/80 to-slate-950",
      accentBorder: "border-purple-500/40 group-hover:border-purple-500/60 shadow-[0_0_30px_rgba(168,85,247,0.15)]",
      iconBg: "bg-purple-500/15 text-purple-400 border-purple-500/30",
      highlight: "Persistent context ensures conversations feel continuous and familiar."
    },
    {
      id: "reminders",
      number: "03",
      icon: Pill,
      title: "Stay on track with reminders",
      subtitle: "Smart Reminders",
      desc: "Receive calm, timely reminders for important medications, doctor visits, and daily health routines.",
      tag: "Voice-Verified Care",
      gradient: "from-emerald-500/10 via-slate-900/80 to-slate-950",
      accentBorder: "border-emerald-500/40 group-hover:border-emerald-500/60 shadow-[0_0_30px_rgba(16,185,129,0.15)]",
      iconBg: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
      highlight: "Voice confirmation records actual adherence without complex app menus."
    },
    {
      id: "family",
      number: "04",
      icon: Users,
      title: "Keep family connected",
      subtitle: "Family Connect",
      desc: "Caregivers can stay informed about important care activity, adherence trends, and safety in real time.",
      tag: "Caregiver Telemetry",
      gradient: "from-blue-500/10 via-slate-900/80 to-slate-950",
      accentBorder: "border-blue-500/40 group-hover:border-blue-500/60 shadow-[0_0_30px_rgba(59,130,246,0.15)]",
      iconBg: "bg-blue-500/15 text-blue-400 border-blue-500/30",
      highlight: "Role-isolated dashboard provides peace of mind across distances."
    }
  ];

  // Dynamic geometry measurement for centering Card 01 to Card 04
  const updateMeasurements = useCallback(() => {
    if (!viewportRef.current || !trackRef.current) return;
    const viewportWidth = viewportRef.current.clientWidth;
    const cards = trackRef.current.children;
    if (!cards || cards.length === 0) return;

    const firstCard = cards[0];
    const lastCard = cards[cards.length - 1];

    const firstCardCenter = firstCard.offsetLeft + firstCard.offsetWidth / 2;
    const lastCardCenter = lastCard.offsetLeft + lastCard.offsetWidth / 2;

    const startX = viewportWidth / 2 - firstCardCenter;
    const endX = viewportWidth / 2 - lastCardCenter;

    scrollRangeRef.current = { startX, endX };
  }, []);

  useEffect(() => {
    const checkResponsive = () => {
      setIsMobile(window.innerWidth < 768);
      setIsReducedMotion(window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    };

    checkResponsive();
    updateMeasurements();

    const resizeObserver = new ResizeObserver(() => {
      checkResponsive();
      updateMeasurements();
    });

    if (viewportRef.current) resizeObserver.observe(viewportRef.current);
    if (trackRef.current) resizeObserver.observe(trackRef.current);

    window.addEventListener('resize', checkResponsive);
    window.addEventListener('resize', updateMeasurements);

    // Run measurement again after next paint to guarantee DOM element positions
    const rafId = requestAnimationFrame(() => {
      updateMeasurements();
    });

    return () => {
      cancelAnimationFrame(rafId);
      resizeObserver.disconnect();
      window.removeEventListener('resize', checkResponsive);
      window.removeEventListener('resize', updateMeasurements);
    };
  }, [updateMeasurements]);

  // Framer Motion Scroll Progression
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });

  // Silky-smooth spring physics for vertical-to-horizontal transformation
  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 120,
    damping: 26,
    mass: 0.2,
    restDelta: 0.0005
  });

  // Dynamic translation: Moves strictly from FIRST_CARD_CENTERED to LAST_CARD_CENTERED
  const x = useTransform(smoothProgress, (p) => {
    const { startX, endX } = scrollRangeRef.current;
    if (startX === 0 && endX === 0) return 0;
    if (p <= 0.05) return startX;
    if (p >= 0.95) return endX;
    const norm = (p - 0.05) / 0.9;
    return startX + norm * (endX - startX);
  });

  // Track active pillar index for indicators and highlights without 60fps re-renders
  useMotionValueEvent(smoothProgress, "change", (latest) => {
    const norm = Math.max(0, Math.min(1, (latest - 0.05) / 0.9));
    const newIdx = Math.min(pillars.length - 1, Math.max(0, Math.round(norm * (pillars.length - 1))));
    setActiveIndex(newIdx);
  });

  // Interactive Pillar Navigation: smoothly scrolls to center the selected pillar
  const scrollToPillar = (index) => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const rect = container.getBoundingClientRect();
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const containerTop = rect.top + scrollTop;
    const scrollableDistance = container.offsetHeight - window.innerHeight;

    const targetProgress = pillars.length > 1 
      ? 0.05 + (index / (pillars.length - 1)) * 0.90 
      : 0;

    const targetScrollY = containerTop + targetProgress * scrollableDistance;

    window.scrollTo({
      top: targetScrollY,
      behavior: 'smooth'
    });
  };

  // Mobile scroll handler for swipe tracking
  const handleMobileScroll = () => {
    if (!mobileScrollRef.current) return;
    const el = mobileScrollRef.current;
    const scrollLeft = el.scrollLeft;
    const cardWidth = el.firstElementChild ? el.firstElementChild.offsetWidth + 16 : 300;
    const idx = Math.round(scrollLeft / cardWidth);
    setMobileIndex(Math.min(pillars.length - 1, Math.max(0, idx)));
  };

  const scrollToMobileCard = (idx) => {
    if (!mobileScrollRef.current) return;
    const el = mobileScrollRef.current;
    const cardWidth = el.firstElementChild ? el.firstElementChild.offsetWidth + 16 : 300;
    el.scrollTo({
      left: idx * cardWidth,
      behavior: 'smooth'
    });
  };

  // Accessible Reduced Motion View: Static Grid
  if (isReducedMotion) {
    return (
      <section className="py-20 px-6 max-w-7xl mx-auto z-10 relative">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-300 text-xs font-semibold tracking-wide mb-3">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>One ORMA · Many Ways to Care</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
            Core Platform Pillars
          </h2>
          <p className="text-slate-400 text-sm max-w-xl mx-auto mt-2">
            Explore the four foundational pillars that make ORMA AI a calm, trustworthy care companion.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {pillars.map((item) => (
            <div
              key={item.id}
              className={`p-7 rounded-3xl bg-slate-900/80 border ${item.accentBorder} shadow-xl relative overflow-hidden backdrop-blur-xl`}
            >
              <div className="flex items-center justify-between mb-5">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border shadow-inner ${item.iconBg}`}>
                  <item.icon className="w-6 h-6" />
                </div>
                <span className="text-xs font-mono font-bold text-slate-500 uppercase tracking-widest">{item.number}</span>
              </div>
              <span className="text-xs font-bold uppercase tracking-wider text-blue-400 mb-1.5 block">{item.subtitle}</span>
              <h3 className="text-xl font-bold text-white mb-2.5">{item.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed mb-4">{item.desc}</p>
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-white/5 mb-4">
                <p className="text-xs text-slate-400 leading-relaxed">
                  💡 <span className="text-slate-200 font-medium">{item.highlight}</span>
                </p>
              </div>
              <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs text-slate-400">
                <span className="font-semibold text-slate-300">{item.tag}</span>
                <span className="flex items-center gap-1 text-blue-400 font-semibold">
                  Connected to ORMA <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>
    );
  }

  // Mobile Touch-Friendly Swipe Carousel (< 768px)
  if (isMobile) {
    return (
      <section className="py-16 px-4 z-10 relative overflow-hidden">
        <div className="text-center mb-8 px-2">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-300 text-xs font-semibold tracking-wide mb-3">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            <span>One ORMA · Many Ways to Care</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Core Platform Pillars
          </h2>
          <p className="text-slate-400 text-xs sm:text-sm max-w-sm mx-auto mt-1.5">
            Swipe horizontally to explore how ORMA AI supports seniors and families.
          </p>
        </div>

        {/* Mobile Swipe Container with CSS Scroll Snap */}
        <div 
          ref={mobileScrollRef}
          onScroll={handleMobileScroll}
          className="flex gap-4 overflow-x-auto snap-x snap-mandatory px-4 pb-4 pt-1"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {pillars.map((item, idx) => (
            <div
              key={item.id}
              className={`w-[85vw] max-w-[340px] shrink-0 snap-center p-6 rounded-3xl bg-gradient-to-b ${item.gradient} border ${
                mobileIndex === idx ? item.accentBorder : 'border-slate-800'
              } shadow-2xl relative overflow-hidden backdrop-blur-xl transition-all`}
            >
              <div className="flex items-center justify-between mb-5">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border shadow-inner ${item.iconBg}`}>
                  <item.icon className="w-6 h-6" />
                </div>
                <span className="text-xs font-mono font-bold text-slate-500 uppercase tracking-widest">{item.number}</span>
              </div>
              <span className="text-xs font-bold uppercase tracking-wider text-blue-400 mb-1 block">{item.subtitle}</span>
              <h3 className="text-lg font-bold text-white mb-2 leading-snug">{item.title}</h3>
              <p className="text-xs text-slate-300 leading-relaxed mb-4">{item.desc}</p>
              
              <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-white/5 mb-4">
                <p className="text-xs text-slate-400 leading-relaxed">
                  💡 <span className="text-slate-200 font-medium">{item.highlight}</span>
                </p>
              </div>

              <div className="pt-3 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
                <span className="font-semibold text-slate-300 text-[11px]">{item.tag}</span>
                <span className="flex items-center gap-1 text-blue-400 font-semibold text-[11px]">
                  Connected to ORMA <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Mobile Interactive Pagination Dots & Counter */}
        <div className="flex items-center justify-between px-4 mt-4 max-w-sm mx-auto">
          <div className="flex items-center gap-2">
            {pillars.map((_, idx) => (
              <button
                key={idx}
                onClick={() => scrollToMobileCard(idx)}
                className={`h-1.5 rounded-full transition-all cursor-pointer ${
                  mobileIndex === idx ? 'w-6 bg-blue-400' : 'w-2 bg-slate-700 hover:bg-slate-600'
                }`}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>
          <div className="text-xs font-mono text-slate-500">
            <span className="text-blue-400 font-bold">{pillars[mobileIndex]?.number || '01'}</span> / 04
          </div>
        </div>
      </section>
    );
  }

  // Desktop & Tablet (>= 768px): Vertical-Scroll-Driven Sticky Horizontal Storytelling
  return (
    <section ref={containerRef} className="relative h-[320vh] z-10 w-full">
      <div 
        ref={viewportRef}
        className="sticky top-16 h-[calc(100vh-4rem)] flex flex-col justify-center overflow-hidden w-full max-w-full"
      >
        
        {/* Section Header */}
        <div className="max-w-7xl mx-auto px-6 w-full mb-6 lg:mb-8 shrink-0">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 text-blue-300 text-xs font-semibold tracking-wide mb-3">
                <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                <span>One ORMA · Many Ways to Care</span>
              </div>
              <h2 className="text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
                Core Platform Pillars
              </h2>
              <p className="text-slate-400 text-sm md:text-base mt-1">
                Scroll vertically to walk through how ORMA AI supports seniors and families.
              </p>
            </div>

            {/* Interactive Pillar Step Indicators & Live Counter */}
            <div className="flex items-center gap-3">
              {/* Step Pills */}
              <div className="flex items-center gap-1 p-1 rounded-2xl bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl shadow-lg">
                {pillars.map((p, idx) => {
                  const isActive = activeIndex === idx;
                  return (
                    <button
                      key={p.id}
                      onClick={() => scrollToPillar(idx)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                        isActive 
                          ? 'bg-blue-600/30 text-white border border-blue-500/40 shadow-[0_0_15px_rgba(59,130,246,0.2)]' 
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                      }`}
                      title={`Jump to ${p.subtitle}`}
                    >
                      <span className={`font-mono text-[11px] ${isActive ? 'text-blue-400 font-bold' : 'text-slate-500'}`}>
                        {p.number}
                      </span>
                      <span className="hidden lg:inline">{p.subtitle}</span>
                    </button>
                  );
                })}
              </div>

              {/* Step Progress Number Indicator */}
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-2xl bg-slate-900/80 border border-slate-800/80 text-xs font-mono text-slate-400 shadow-lg">
                <span className="text-blue-400 font-bold">{pillars[activeIndex]?.number || '01'}</span>
                <span className="text-slate-600">/</span>
                <span>04</span>
              </div>
            </div>
          </div>
        </div>

        {/* Horizontal Moving Cards Track Container (Strictly clipped with zero page overflow) */}
        <div className="w-full overflow-hidden relative">
          <motion.div 
            ref={trackRef}
            style={{ x }} 
            className="flex gap-6 lg:gap-8 w-max py-4 will-change-transform"
          >
            {pillars.map((item, idx) => {
              const isActive = activeIndex === idx;
              return (
                <div
                  key={item.id}
                  className={`w-[400px] md:w-[460px] lg:w-[500px] shrink-0 p-7 sm:p-8 rounded-3xl bg-gradient-to-b ${item.gradient} border ${
                    isActive ? item.accentBorder : 'border-slate-800/80 hover:border-slate-700'
                  } shadow-2xl relative overflow-hidden backdrop-blur-2xl transition-all duration-300 group ${
                    isActive ? 'opacity-100' : 'opacity-75 hover:opacity-90'
                  }`}
                >
                  {/* Specular top highlight */}
                  <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-transparent pointer-events-none" />

                  <div className="flex items-center justify-between mb-6 relative z-10">
                    <div className={`w-13 h-13 sm:w-14 sm:h-14 rounded-2xl flex items-center justify-center border shadow-inner ${item.iconBg}`}>
                      <item.icon className="w-6 h-6 sm:w-7 sm:h-7" />
                    </div>
                    <div className="flex items-center gap-2">
                      {isActive && (
                        <span className="px-2 py-0.5 rounded-md bg-blue-500/20 text-blue-300 text-[10px] font-bold uppercase tracking-wider border border-blue-500/30">
                          Active Pillar
                        </span>
                      )}
                      <span className="text-sm font-mono font-bold text-slate-500 uppercase tracking-widest">{item.number}</span>
                    </div>
                  </div>

                  <div className="relative z-10">
                    <span className="text-xs font-bold uppercase tracking-widest text-blue-400 mb-2 block">{item.subtitle}</span>
                    <h3 className="text-2xl font-extrabold text-white tracking-tight mb-3">
                      {item.title}
                    </h3>
                    <p className="text-sm text-slate-300 leading-relaxed mb-6 font-normal">
                      {item.desc}
                    </p>

                    <div className="p-4 rounded-2xl bg-slate-950/60 border border-white/5 mb-6">
                      <p className="text-xs text-slate-400 leading-relaxed">
                        💡 <span className="text-slate-200 font-medium">{item.highlight}</span>
                      </p>
                    </div>

                    <div className="pt-4 border-t border-white/10 flex items-center justify-between text-xs text-slate-400">
                      <span className="font-semibold text-slate-300">{item.tag}</span>
                      <span className="flex items-center gap-1 text-blue-400 font-semibold group-hover:translate-x-0.5 transition-transform">
                        Connected to ORMA <ArrowRight className="w-3.5 h-3.5" />
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </motion.div>
        </div>

        {/* Bottom Context Bar */}
        <div className="max-w-7xl mx-auto px-6 w-full mt-4 lg:mt-6 shrink-0 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
            <span className="hidden sm:inline text-slate-400">Pillar {pillars[activeIndex]?.number}:</span>
            <span className="text-slate-300 font-semibold">{pillars[activeIndex]?.title}</span>
          </div>

          <div className="flex items-center gap-3">
            <div className="w-24 sm:w-32 h-1.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
              <motion.div 
                style={{ scaleX: smoothProgress }} 
                className="h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 origin-left"
              />
            </div>
            <span className="font-mono text-slate-400">{Math.round((activeIndex + 1) / pillars.length * 100)}%</span>
          </div>
        </div>

      </div>
    </section>
  );
}
