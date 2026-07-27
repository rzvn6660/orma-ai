import { motion } from 'framer-motion';
import { AlertOctagon, PhoneCall, ShieldAlert, HeartPulse } from 'lucide-react';
import EmergencyAlert from '../components/EmergencyAlert';

export default function EmergencyPage({ user }) {
  return (
    <div className="max-w-4xl mx-auto space-y-8 p-4 md:p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-white flex items-center gap-3">
          <AlertOctagon className="text-red-500 w-8 h-8" /> Emergency Center
        </h2>
        <p className="text-slate-400 mt-2 text-lg">Immediate access to medical assistance and family alerts.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col gap-6"
        >
          <div className="orma-card p-8 border-red-500/20 shadow-2xl h-full flex flex-col justify-center bg-red-950/20">
             <h3 className="text-xl font-bold text-white mb-6 text-center tracking-wide">SOS Trigger</h3>
             <EmergencyAlert />
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="flex flex-col gap-6"
        >
          <div className="orma-card p-6 border-slate-700/50">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
               <PhoneCall className="w-5 h-5 text-blue-400" /> Quick Contacts
            </h3>
            <ul className="space-y-3">
               <li className="flex justify-between items-center p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
                  <div>
                    <p className="text-white font-medium">Local Ambulance</p>
                    <p className="text-slate-400 text-sm">Medical Emergency</p>
                  </div>
                  <a href="tel:911" className="orma-btn-primary">
                    <PhoneCall className="w-4 h-4" />
                  </a>
               </li>
               <li className="flex justify-between items-center p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
                  <div>
                    <p className="text-white font-medium">Primary Caregiver</p>
                    <p className="text-slate-400 text-sm">Family Member</p>
                  </div>
                  <a href="#" className="bg-slate-700 hover:bg-slate-600 text-white p-2 rounded-lg transition-colors">
                    <PhoneCall className="w-4 h-4" />
                  </a>
               </li>
            </ul>
          </div>

          <div className="orma-card p-6 border-slate-700/50">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
               <ShieldAlert className="w-5 h-5 text-amber-400" /> Action Plan
            </h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              When the SOS button is triggered, Orma AI will immediately notify your linked caregivers, share your location, and can optionally dial emergency services. Please ensure your location permissions are enabled.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
