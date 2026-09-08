import { motion } from 'framer-motion';
import { ShieldCheck, Link, ArrowRight, Users } from 'lucide-react';

/**
 * Shown to a caregiver who has zero approved linked elderly accounts.
 * Replaces the dashboard entirely — no patient data (real or fabricated) is rendered.
 */
export default function NoLinkedPatientEmptyState({ onViewChange }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="w-full max-w-2xl mx-auto flex flex-col items-center justify-center gap-8 py-20 px-4"
    >
      {/* Icon */}
      <div className="w-20 h-20 rounded-3xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shadow-inner">
        <Users className="w-10 h-10" />
      </div>

      {/* Heading */}
      <div className="text-center space-y-3">
        <h2 className="text-2xl font-extrabold text-white tracking-tight">
          No patient linked yet
        </h2>
        <p className="text-slate-400 text-sm max-w-md leading-relaxed">
          Your caregiver account is active, but you have not been approved to monitor
          any elderly account. Patient monitoring data will appear here once an elderly
          account accepts your connection request.
        </p>
      </div>

      {/* Steps */}
      <div className="w-full bg-slate-900/60 border border-white/8 rounded-3xl p-6 space-y-4">
        <p className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-2">How to connect</p>
        {[
          { step: '1', text: 'Ask the elderly person to open ORMA and go to Settings → Family Connections.' },
          { step: '2', text: 'They generate a connection code and share it with you.' },
          { step: '3', text: 'Go to Settings → Family Connections and enter the code.' },
          { step: '4', text: 'The elderly person approves your request — the dashboard unlocks immediately.' },
        ].map(({ step, text }) => (
          <div key={step} className="flex items-start gap-3">
            <div className="w-6 h-6 rounded-full bg-blue-500/15 border border-blue-500/25 flex items-center justify-center text-blue-400 text-[11px] font-bold shrink-0 mt-0.5">
              {step}
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">{text}</p>
          </div>
        ))}
      </div>

      {/* CTA */}
      <button
        id="cta-go-to-settings"
        onClick={() => onViewChange?.('settings')}
        className="flex items-center gap-2.5 px-6 py-3 rounded-2xl bg-blue-600 hover:bg-blue-500 active:scale-95 transition-all text-white font-bold text-sm shadow-lg shadow-blue-500/20"
      >
        <Link className="w-4 h-4" />
        Go to Family Connections
        <ArrowRight className="w-4 h-4" />
      </button>

      <p className="text-[11px] text-slate-600 text-center">
        Your caregiver account data is secure. No patient information is shared until you are approved.
      </p>
    </motion.div>
  );
}
