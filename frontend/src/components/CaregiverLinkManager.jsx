import { useState, useEffect, useRef } from 'react';
import { linkApi } from '../services/api';
import { Key, Link as LinkIcon, Users, UserX, ShieldAlert, CheckCircle2, Loader2, Volume2, PlayCircle, Globe, MoreVertical, AlertTriangle, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { tts } from '../services/tts';

export default function CaregiverLinkManager({ user }) {
  const [code, setCode] = useState('');
  const [generatedCode, setGeneratedCode] = useState(null);
  const [linkedUsers, setLinkedUsers] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });
  const [volumeLevel, setVolumeLevel] = useState(tts.getVolumeLevel());
  const [langPref, setLangPref] = useState(localStorage.getItem('orma_language_pref') || 'auto');

  // Confirmation Modal state
  const [confirmModal, setConfirmModal] = useState({ isOpen: false, target: null, type: null, loading: false });
  // Menu dropdown state
  const [activeMenuId, setActiveMenuId] = useState(null);

  const modalCancelRef = useRef(null);

  const handleLangChange = (e) => {
    const newLang = e.target.value;
    setLangPref(newLang);
    localStorage.setItem('orma_language_pref', newLang);
    window.dispatchEvent(new Event('languageChange'));
  };

  const handleVolumeChange = (e) => {
    const newVol = e.target.value;
    setVolumeLevel(newVol);
    tts.setVolumeLevel(newVol);
  };
  
  const handleTestVoice = () => {
    tts.speak("This is a sample of my voice. I am Orma AI, your health assistant.");
  };

  const loadLinkedUsers = async () => {
    try {
      const data = await linkApi.getLinkedUsers();
      if (user.role === 'elderly') {
        setLinkedUsers(data.linked_caregivers || []);
        const pendingData = await linkApi.getPendingRequests();
        setPendingRequests(pendingData.pending_requests || []);
      } else {
        setLinkedUsers(data.linked_users || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadLinkedUsers();

    const handleWsMessage = (e) => {
      const data = e.detail;
      const relevantTypes = [
        'caregiver_linked', 
        'caregiver_removed', 
        'pending_request_created', 
        'pending_request_approved'
      ];
      
      if (relevantTypes.includes(data.type)) {
        loadLinkedUsers();
      }
    };

    window.addEventListener('orma_websocket_message', handleWsMessage);
    return () => window.removeEventListener('orma_websocket_message', handleWsMessage);
  }, [user.role]);

  const closeConfirmModal = () => {
    if (confirmModal.loading) return;
    setConfirmModal({ isOpen: false, target: null, type: null, loading: false });
  };

  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && confirmModal.isOpen && !confirmModal.loading) {
        closeConfirmModal();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [confirmModal]);

  // Focus trap focus on cancel button when modal opens
  useEffect(() => {
    if (confirmModal.isOpen && modalCancelRef.current) {
      modalCancelRef.current.focus();
    }
  }, [confirmModal.isOpen]);

  const handleGenerateCode = async () => {
    setLoading(true);
    setMessage({ text: '', type: '' });
    try {
      const data = await linkApi.generateCode();
      setGeneratedCode(data.code);
      setMessage({ text: 'Code generated. Share this with your trusted caregiver.', type: 'success' });
    } catch (err) {
      setMessage({ text: 'Failed to generate code.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleConnectCaregiver = async (e) => {
    e.preventDefault();
    if (!code) return;
    setLoading(true);
    setMessage({ text: '', type: '' });
    try {
      await linkApi.connectCaregiver(code);
      setMessage({ text: 'Successfully linked to user.', type: 'success' });
      setCode('');
      loadLinkedUsers();
    } catch (err) {
      setMessage({ text: err.response?.data?.detail || 'Failed to connect. Check code.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const openUnlinkModal = (target, type) => {
    setActiveMenuId(null);
    setConfirmModal({ isOpen: true, target, type, loading: false });
  };

  const executeRevokeAccess = async () => {
    if (!confirmModal.target) return;
    setConfirmModal(prev => ({ ...prev, loading: true }));
    setMessage({ text: '', type: '' });

    const targetId = confirmModal.target.id;
    const targetName = confirmModal.target.name;
    const isCaregiverRole = user.role === 'caregiver';

    try {
      await linkApi.revokeAccess(targetId);
      
      const updatedData = await linkApi.getLinkedUsers();
      const updatedList = isCaregiverRole ? (updatedData.linked_users || []) : (updatedData.linked_caregivers || []);
      setLinkedUsers(updatedList);

      if (isCaregiverRole) {
        setMessage({ text: 'Patient unlinked successfully.', type: 'success' });
        // Handle patient switcher state
        const currentSubject = localStorage.getItem('orma_subject_id');
        if (currentSubject === targetId) {
          if (updatedList.length > 0) {
            localStorage.setItem('orma_subject_id', updatedList[0].id);
          } else {
            localStorage.removeItem('orma_subject_id');
          }
          window.dispatchEvent(new Event('subjectChange'));
        }
      } else {
        setMessage({ text: 'Caregiver access removed.', type: 'success' });
      }

      setConfirmModal({ isOpen: false, target: null, type: null, loading: false });
    } catch (err) {
      const errMsg = err.response?.status === 403 
        ? "You don't have permission to change this relationship."
        : err.response?.status === 404
        ? "This connection no longer exists."
        : "Unable to update caregiver access. Please try again.";

      setMessage({ text: errMsg, type: 'error' });
      setConfirmModal(prev => ({ ...prev, loading: false }));
    }
  };

  const handleApprove = async (targetId) => {
    try {
      await linkApi.approveRequest(targetId);
      loadLinkedUsers();
      setMessage({ text: 'Request approved.', type: 'success' });
    } catch (err) {
      setMessage({ text: 'Failed to approve request.', type: 'error' });
    }
  };

  const handleDecline = async (targetId) => {
    try {
      await linkApi.declineRequest(targetId);
      loadLinkedUsers();
      setMessage({ text: 'Request declined.', type: 'success' });
    } catch (err) {
      setMessage({ text: 'Failed to decline request.', type: 'error' });
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <ShieldAlert className="text-indigo-400 w-6 h-6" /> Settings & Security Center
        </h2>
        <p className="text-slate-400">Manage device settings and data access.</p>
      </div>

      {message.text && (
        <div className={`p-4 rounded-xl border ${message.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
          {message.text}
        </div>
      )}

      {user.role === 'elderly' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="orma-card p-6 border-indigo-500/20">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Key className="w-5 h-5 text-indigo-400"/> Grant Caregiver Access</h3>
            <p className="text-sm text-slate-400 mb-6">Generate a secure one-time code to allow a trusted family member to monitor your wellness.</p>
            
            {generatedCode ? (
              <div className="bg-slate-900/80 p-4 rounded-xl border border-indigo-500/30 text-center mb-4 relative">
                <p className="text-xs text-slate-400 uppercase tracking-widest mb-1">Your secure code</p>
                <div className="flex items-center justify-center gap-4">
                  <p className="text-3xl font-mono font-bold text-white tracking-widest">{generatedCode}</p>
                  <button 
                    onClick={() => {
                      navigator.clipboard.writeText(generatedCode);
                      setMessage({ text: 'Code copied to clipboard!', type: 'success' });
                    }}
                    className="p-2 hover:bg-indigo-500/20 text-slate-400 hover:text-indigo-400 rounded-lg transition-colors cursor-pointer" 
                    title="Copy Code"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
              </div>
            ) : null}

            <button onClick={handleGenerateCode} disabled={loading} className="orma-btn-primary">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Generate New Code'}
            </button>
          </motion.div>

          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 }} className="orma-card p-6 border-emerald-500/20">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Users className="w-5 h-5 text-emerald-400"/> Authorized Caregivers</h3>
            <div className="space-y-4 mb-8">
              {linkedUsers.length === 0 ? (
                <p className="text-sm text-slate-500 italic">No caregivers linked yet.</p>
              ) : (
                linkedUsers.map(u => (
                  <div key={u.id} className="flex justify-between items-center bg-slate-800/50 p-3 rounded-xl border border-slate-700">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-white font-medium">{u.name}</p>
                        <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-widest bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">Connected</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">{u.email}</p>
                    </div>
                    <button 
                      onClick={() => openUnlinkModal(u, 'remove_caregiver')} 
                      className="px-3 py-1.5 hover:bg-red-500/20 text-slate-400 hover:text-red-400 rounded-lg transition-colors text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
                      title="Remove Access"
                    >
                      <UserX className="w-4 h-4" /> Remove Access
                    </button>
                  </div>
                ))
              )}
            </div>

            {pendingRequests.length > 0 && (
              <>
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><ShieldAlert className="w-5 h-5 text-amber-400"/> Pending Requests</h3>
                <div className="space-y-4">
                  {pendingRequests.map(u => (
                    <div key={u.id} className="bg-amber-900/10 p-4 rounded-xl border border-amber-500/30">
                      <p className="text-sm text-slate-300 mb-3"><strong className="text-white">{u.name}</strong> would like to connect as your caregiver.</p>
                      <div className="flex gap-3">
                        <button onClick={() => handleApprove(u.id)} className="orma-btn-success">
                          Approve
                        </button>
                        <button onClick={() => handleDecline(u.id)} className="flex-1 bg-slate-700 hover:bg-slate-600 text-white font-bold py-2 rounded-lg transition-all text-sm">
                          Decline
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </motion.div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="orma-card p-6 border-blue-500/20">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><LinkIcon className="w-5 h-5 text-blue-400"/> Link Elderly Account</h3>
            <p className="text-sm text-slate-400 mb-6">Enter the 6-character secure code generated by your parent's Orma AI assistant.</p>
            <form onSubmit={handleConnectCaregiver} className="space-y-4">
              <input 
                type="text" 
                value={code} 
                onChange={(e) => setCode(e.target.value.toUpperCase())} 
                placeholder="ORMA-XXXXXX" 
                className="w-full bg-slate-900/80 border border-slate-700 rounded-xl py-3 px-4 text-white font-mono uppercase tracking-widest focus:outline-none focus:border-blue-500 transition-colors" 
                maxLength={11}
              />
              <button type="submit" disabled={loading || !code} className="orma-btn-primary">
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Connect Securely'}
              </button>
            </form>
          </motion.div>
          
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 }} className="orma-card p-6 border-emerald-500/20">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2"><Users className="w-5 h-5 text-emerald-400"/> Linked Patients</h3>
            <div className="space-y-4">
              {linkedUsers.length === 0 ? (
                <p className="text-sm text-slate-500 italic">No patients linked yet.</p>
              ) : (
                linkedUsers.map(u => (
                  <div key={u.id} className="relative flex items-center justify-between bg-slate-800/50 p-3.5 rounded-xl border border-slate-700">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-white font-medium">{u.name}</p>
                          <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-widest bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">Connected</span>
                        </div>
                        <p className="text-xs text-slate-400">{u.email}</p>
                      </div>
                    </div>

                    <div className="relative">
                      <button 
                        onClick={() => setActiveMenuId(activeMenuId === u.id ? null : u.id)}
                        className="p-2 hover:bg-slate-700/50 text-slate-400 hover:text-white rounded-lg transition-colors cursor-pointer"
                        title="Patient Options"
                      >
                        <MoreVertical className="w-5 h-5" />
                      </button>

                      {activeMenuId === u.id && (
                        <div className="absolute right-0 top-full mt-1 w-44 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-40 overflow-hidden py-1">
                          <button
                            onClick={() => openUnlinkModal(u, 'unlink_patient')}
                            className="w-full text-left px-4 py-2.5 text-xs font-semibold text-red-400 hover:bg-red-500/10 flex items-center gap-2 transition-colors cursor-pointer"
                          >
                            <UserX className="w-4 h-4 text-red-400" /> Unlink Patient
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        </div>
      )}

      {/* RESTRAINED DESTRUCTIVE CONFIRMATION MODAL */}
      <AnimatePresence>
        {confirmModal.isOpen && confirmModal.target && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={closeConfirmModal}
              className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
            />

            {/* Modal Content */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              role="dialog"
              aria-modal="true"
              className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl z-10 space-y-6"
            >
              <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 shrink-0">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white leading-snug">
                      {confirmModal.type === 'unlink_patient' 
                        ? `Unlink ${confirmModal.target.name}?`
                        : `Remove ${confirmModal.target.name}'s access?`}
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">{confirmModal.target.email}</p>
                  </div>
                </div>
                <button
                  onClick={closeConfirmModal}
                  disabled={confirmModal.loading}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="text-sm text-slate-300 leading-relaxed space-y-3">
                <p>
                  {confirmModal.type === 'unlink_patient'
                    ? `You will no longer have access to ${confirmModal.target.name}'s health information, medicine adherence, reminders, reports, alerts, or other caregiver-only information.`
                    : `${confirmModal.target.name} will no longer be able to access your health information, medicine adherence, reminders, reports, alerts, or other caregiver-only information.`}
                </p>
                <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/50 text-xs text-slate-400">
                  <strong className="text-slate-200 block mb-0.5">Account & Health Data Safety:</strong>
                  {confirmModal.type === 'unlink_patient'
                    ? `${confirmModal.target.name}'s ORMA account and health records will NOT be deleted.`
                    : `Your ORMA account and health records will remain unchanged.`}
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  ref={modalCancelRef}
                  type="button"
                  onClick={closeConfirmModal}
                  disabled={confirmModal.loading}
                  className="flex-1 py-3 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded-2xl transition-colors text-sm cursor-pointer disabled:opacity-50"
                >
                  Cancel
                </button>

                <button
                  type="button"
                  onClick={executeRevokeAccess}
                  disabled={confirmModal.loading}
                  className="flex-1 py-3 px-4 bg-red-600 hover:bg-red-700 text-white font-bold rounded-2xl transition-colors text-sm flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-red-600/20 disabled:opacity-50"
                >
                  {confirmModal.loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Revoking...</span>
                    </>
                  ) : (
                    <span>
                      {confirmModal.type === 'unlink_patient' ? 'Unlink Patient' : 'Remove Access'}
                    </span>
                  )}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* LANGUAGE SETTINGS SECTION */}
      <div className="mt-12 mb-6 pt-6 border-t border-slate-800">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Globe className="text-blue-400 w-6 h-6" /> Language Preference
        </h2>
        <p className="text-slate-400">Choose your preferred language for Orma AI.</p>
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="orma-card p-6 border-blue-500/20 max-w-lg">
        <label className="text-lg font-bold text-white mb-4 block">Select Language</label>
        <select 
          value={langPref}
          onChange={handleLangChange}
          className="orma-input"
        >
          <option value="auto">Auto Detect</option>
          <option value="en">English</option>
          <option value="ml">Malayalam</option>
        </select>
      </motion.div>

      {/* VOICE SETTINGS SECTION */}
      <div className="mt-12 mb-6 pt-6 border-t border-slate-800">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Volume2 className="text-pink-400 w-6 h-6" /> Voice Output Settings
        </h2>
        <p className="text-slate-400">Adjust how loud Orma AI speaks.</p>
      </div>
      
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="orma-card p-6 border-pink-500/20 max-w-lg">
        <label className="text-lg font-bold text-white mb-4 block">Assistant Voice Volume</label>
        <select 
          value={volumeLevel}
          onChange={handleVolumeChange}
          className="orma-input"
        >
          <option value="Low">Low</option>
          <option value="Medium">Medium</option>
          <option value="High">High</option>
          <option value="Maximum">Maximum</option>
        </select>
        
        <button onClick={handleTestVoice} className="orma-btn-secondary">
          <PlayCircle className="w-5 h-5 text-pink-400" /> Test Voice
        </button>
      </motion.div>
    </div>
  );
}
