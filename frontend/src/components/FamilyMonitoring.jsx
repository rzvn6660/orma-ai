import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Phone, MessageSquare, Info, UserCircle, Loader2, User } from 'lucide-react';
import { linkApi } from '../services/api';

export default function FamilyMonitoring() {
  const [caregivers, setCaregivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchCaregivers = async () => {
    try {
      setError(false);
      const data = await linkApi.getLinkedUsers();
      const list = data?.linked_caregivers || [];
      setCaregivers(list.slice(0, 3));
    } catch (err) {
      console.error("Failed to fetch linked caregivers", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCaregivers();

    const handleWsMessage = (e) => {
      const msgData = e.detail;
      const relevantTypes = [
        'caregiver_linked', 
        'caregiver_removed', 
        'caregiver_updated',
        'pending_request_approved'
      ];
      if (relevantTypes.includes(msgData.type)) {
        fetchCaregivers();
      }
    };

    window.addEventListener('orma_websocket_message', handleWsMessage);
    // Also poll every 60s as a fallback for sync
    const interval = setInterval(fetchCaregivers, 60000);

    return () => {
      window.removeEventListener('orma_websocket_message', handleWsMessage);
      clearInterval(interval);
    };
  }, []);

  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.6, delay: 0.3 }}
      className="orma-card p-6 border border-slate-700/50 shadow-xl rounded-[2rem]"
    >
      <div className="flex justify-between items-center mb-4 pb-3 border-b border-slate-700/50">
        <h3 className="text-[17px] font-medium text-white tracking-wide">
          Family Network
        </h3>
        {caregivers.length > 0 && !loading && (
          <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-widest bg-emerald-500/10 px-2 py-1 rounded-full border border-emerald-500/20">
            {caregivers.length} Linked
          </span>
        )}
      </div>

      <div className="space-y-4">
        {loading ? (
          <div className="flex justify-center p-4">
            <Loader2 className="w-5 h-5 text-slate-500 animate-spin" />
          </div>
        ) : error ? (
          <div className="text-center p-4">
             <p className="text-sm text-red-400 font-light mb-2">Unable to load caregivers.</p>
             <button onClick={fetchCaregivers} className="text-xs text-blue-400 hover:text-blue-300">Retry</button>
          </div>
        ) : caregivers.length > 0 ? (
          caregivers.map((cg, index) => {
            const hasPhone = !!cg.phone;
            const status = cg.is_online ? 'Online' : 'Offline';
            const lastActive = cg.last_active ? new Date(cg.last_active + "Z").toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'Just now';
            const roleTitle = index === 0 ? 'Primary Caregiver' : index === 1 ? 'Secondary Caregiver' : 'Emergency Contact';

            return (
              <div key={cg.id} className="flex flex-col p-4 bg-slate-800/40 rounded-2xl border border-slate-600/30 hover:bg-slate-800/60 transition-colors">
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-3">{roleTitle}</p>
                
                <div className="flex items-start gap-4 mb-4">
                  <div className="relative">
                    <div className="w-12 h-12 rounded-full bg-slate-700 flex items-center justify-center">
                       <UserCircle className="w-8 h-8 text-slate-400" />
                    </div>
                    <span className={`absolute bottom-0 right-0 w-3 h-3 border-2 border-slate-800 rounded-full ${cg.is_online ? 'bg-emerald-500' : 'bg-slate-400'}`}></span>
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <h4 className="text-[16px] font-medium text-white tracking-wide leading-tight truncate">{cg.name || 'Caregiver'}</h4>
                    <p className="text-[12px] text-slate-400 font-light mt-0.5 capitalize">{cg.relationship || 'Caregiver'}</p>
                    {hasPhone && <p className="text-[12px] text-slate-400 font-light mt-0.5 font-mono">{cg.phone}</p>}
                    <p className="text-[12px] text-slate-400 font-light mt-0.5 truncate">{cg.email}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between border-t border-slate-700/50 pt-3 mb-3">
                  <div className="flex items-center gap-2 text-slate-400">
                    <span className={`w-1.5 h-1.5 rounded-full ${cg.is_online ? 'bg-emerald-500' : 'bg-slate-500'}`}></span>
                    <span className="text-[11px] font-medium">{status}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-500">
                    <Info className="w-3 h-3" />
                    <span className="text-[10px] font-medium uppercase tracking-widest">Sync: {lastActive}</span>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <a 
                    href={hasPhone ? `tel:${cg.phone}` : '#'}
                    title={hasPhone ? `Call ${cg.phone}` : 'Phone number unavailable'}
                    onClick={(e) => { if (!hasPhone) e.preventDefault(); }}
                    className={`flex-1 py-2 flex items-center justify-center gap-2 rounded-xl text-[13px] font-medium transition-all ${
                      hasPhone 
                        ? 'bg-blue-600/90 hover:bg-blue-500 text-white shadow-md' 
                        : 'bg-slate-700/30 text-slate-500 cursor-not-allowed'
                    }`}
                  >
                    <Phone className="w-3.5 h-3.5" /> Call
                  </a>
                  <a 
                    href={hasPhone ? `sms:${cg.phone}` : '#'}
                    title={hasPhone ? `Message ${cg.phone}` : 'Phone number unavailable'}
                    onClick={(e) => { if (!hasPhone) e.preventDefault(); }}
                    className={`flex-1 py-2 flex items-center justify-center gap-2 rounded-xl text-[13px] font-medium transition-all ${
                      hasPhone 
                        ? 'bg-emerald-600/90 hover:bg-emerald-500 text-white shadow-md' 
                        : 'bg-slate-700/30 text-slate-500 cursor-not-allowed'
                    }`}
                  >
                    <MessageSquare className="w-3.5 h-3.5" /> Message
                  </a>
                  <button 
                    className="flex-1 py-2 flex items-center justify-center gap-2 rounded-xl text-[13px] font-medium transition-all bg-slate-700/50 hover:bg-slate-600 text-slate-200 shadow-sm"
                  >
                    <User className="w-3.5 h-3.5" /> Profile
                  </button>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center p-6 bg-slate-800/20 rounded-2xl border border-slate-700/30 border-dashed">
             <UserCircle className="w-10 h-10 text-slate-500 mx-auto mb-3 opacity-50" />
             <p className="text-sm text-slate-400 font-light">No caregiver connected yet.</p>
          </div>
        )}
      </div>
    </motion.div>
  );
}
