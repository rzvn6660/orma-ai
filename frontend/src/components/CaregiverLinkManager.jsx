import { useState, useEffect, useRef } from 'react';
import { linkApi } from '../services/api';
import { 
  Key, Link as LinkIcon, Users, UserX, ShieldAlert, 
  CheckCircle2, Loader2, Check, Copy, Clock, 
  MoreVertical, AlertTriangle, X, Info, Phone 
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const parseUtcDate = (dateStr) => {
  if (!dateStr) return null;
  if (dateStr instanceof Date) return dateStr;
  const s = String(dateStr).trim();
  if (!s) return null;
  const hasTimezone = /Z$/i.test(s) || /[+-]\d{2}(:?\d{2})?$/.test(s);
  const utcString = hasTimezone ? s : `${s}Z`;
  const d = new Date(utcString);
  return isNaN(d.getTime()) ? null : d;
};

const formatExpiryTime = (dateStr) => {
  const d = parseUtcDate(dateStr);
  if (!d) return '';
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

export default function CaregiverLinkManager({ user }) {
  const isCaregiver = user?.role === 'caregiver';
  const isElderly = !isCaregiver;

  const [code, setCode] = useState('');
  const [generatedCode, setGeneratedCode] = useState(null); // { code, expiresAt }
  const [linkedUsers, setLinkedUsers] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });
  const [timeLeft, setTimeLeft] = useState('');

  // Confirmation Modal state
  const [confirmModal, setConfirmModal] = useState({ isOpen: false, target: null, type: null, loading: false });
  // Menu dropdown state
  const [activeMenuId, setActiveMenuId] = useState(null);

  const modalCancelRef = useRef(null);

  const loadLinkedUsers = async () => {
    try {
      const data = await linkApi.getLinkedUsers();
      if (isElderly) {
        setLinkedUsers(data.linked_caregivers || []);
        const pendingData = await linkApi.getPendingRequests();
        setPendingRequests(pendingData.pending_requests || []);
      } else {
        setLinkedUsers(data.linked_users || []);
      }
    } catch (err) {
      console.error('Failed to load linked users:', err);
    }
  };

  const loadActiveCode = async () => {
    if (!isElderly) return;
    try {
      const data = await linkApi.getActiveCode();
      if (data?.code) {
        const expDate = parseUtcDate(data.expires_at);
        if (expDate && expDate.getTime() > Date.now()) {
          setGeneratedCode({ code: data.code, expiresAt: data.expires_at });
        }
      }
    } catch (err) {
      console.warn('Could not fetch active connection code:', err);
    }
  };

  useEffect(() => {
    loadLinkedUsers();
    if (isElderly) {
      loadActiveCode();
    }

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
  }, [user?.role]);

  // Expiration countdown timer for elderly connection code
  useEffect(() => {
    if (!generatedCode?.expiresAt) {
      setTimeLeft('');
      return;
    }

    const updateRemaining = () => {
      const expDate = parseUtcDate(generatedCode.expiresAt);
      if (!expDate) {
        setTimeLeft('');
        return;
      }
      const diff = expDate.getTime() - Date.now();

      if (diff <= 0) {
        setTimeLeft('Expired');
        return;
      }

      const minutes = Math.floor(diff / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);
      setTimeLeft(`${minutes}:${seconds < 10 ? '0' : ''}${seconds}`);
    };

    updateRemaining();
    const interval = setInterval(updateRemaining, 1000);
    return () => clearInterval(interval);
  }, [generatedCode?.expiresAt]);

  const closeConfirmModal = () => {
    if (confirmModal.loading) return;
    setConfirmModal({ isOpen: false, target: null, type: null, loading: false });
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && confirmModal.isOpen && !confirmModal.loading) {
        closeConfirmModal();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [confirmModal]);

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
      const codeValue = data?.code;
      const expiresValue = data?.expires_at || new Date(Date.now() + 15 * 60 * 1000).toISOString();
      setGeneratedCode({ code: codeValue, expiresAt: expiresValue });
      setMessage({ text: 'Connection code generated! Share this with your trusted caregiver.', type: 'success' });
    } catch (err) {
      setMessage({ text: err.response?.data?.detail || 'Failed to generate code.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = () => {
    if (!generatedCode?.code) return;
    navigator.clipboard.writeText(generatedCode.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleConnectCaregiver = async (e) => {
    e.preventDefault();
    if (!code) return;
    setLoading(true);
    setMessage({ text: '', type: '' });
    let formattedCode = code.trim().toUpperCase();
    if (formattedCode.length === 8 && !formattedCode.includes('-')) {
      formattedCode = `${formattedCode.slice(0, 4)}-${formattedCode.slice(4)}`;
    }
    try {
      await linkApi.connectCaregiver(formattedCode);
      setMessage({ text: 'Connection request submitted to elder for approval.', type: 'success' });
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
    try {
      await linkApi.revokeAccess(targetId);
      
      const updatedData = await linkApi.getLinkedUsers();
      const updatedList = isCaregiver ? (updatedData.linked_users || []) : (updatedData.linked_caregivers || []);
      setLinkedUsers(updatedList);

      if (isCaregiver) {
        setMessage({ text: 'Patient unlinked successfully.', type: 'success' });
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
        setMessage({ text: 'Caregiver access removed successfully.', type: 'success' });
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
      setMessage({ text: 'Caregiver request approved.', type: 'success' });
    } catch (err) {
      setMessage({ text: err.response?.data?.detail || 'Failed to approve request.', type: 'error' });
    }
  };

  const handleDecline = async (targetId) => {
    try {
      await linkApi.declineRequest(targetId);
      loadLinkedUsers();
      setMessage({ text: 'Caregiver request declined.', type: 'success' });
    } catch (err) {
      setMessage({ text: err.response?.data?.detail || 'Failed to decline request.', type: 'error' });
    }
  };

  return (
    <div className="w-full space-y-6 overflow-visible">
      <div className="orma-card p-5 sm:p-7 space-y-6 border border-white/10 shadow-2xl overflow-visible">
        <div className="flex items-center gap-3 border-b border-white/10 pb-4">
          <Users className="w-5 h-5 text-blue-400" />
          <div>
            <h2 className="text-xl font-extrabold text-white">Family Connections</h2>
            <p className="text-xs text-slate-400">
              {isCaregiver
                ? "Link and manage elderly family member profiles and care permissions."
                : "Manage caregiver access and generate secure connection codes for family members."}
            </p>
          </div>
        </div>

        {message.text && (
          <div className={`p-4 rounded-xl border ${message.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
            {message.text}
          </div>
        )}

        {isElderly ? (
          <div className="flex flex-col gap-6">
            {/* 1. GRANT CAREGIVER ACCESS (CODE GENERATION & SHOWCASE) */}
            <motion.div 
              initial={{ opacity: 0, y: 10 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="p-5 sm:p-6 rounded-2xl bg-slate-800/40 border border-indigo-500/30 space-y-4 shadow-xl overflow-visible"
            >
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2">
                  <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                    <Key className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Grant Caregiver Access</h3>
                    <p className="text-xs text-slate-400">Allow a trusted family member or caregiver to link with your account.</p>
                  </div>
                </div>

                {generatedCode?.code && timeLeft && (
                  <span className={`flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-full border ${
                    timeLeft === 'Expired'
                      ? 'text-amber-400 bg-amber-500/10 border-amber-500/30'
                      : 'text-indigo-300 bg-indigo-500/20 border-indigo-500/30 shadow-sm'
                  }`}>
                    <Clock className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{timeLeft === 'Expired' ? 'Code Expired' : `Expires in ${timeLeft}`}</span>
                  </span>
                )}
              </div>

              {generatedCode?.code ? (
                <div className="space-y-4 pt-1">
                  {/* PROMINENT CODE DISPLAY BOX */}
                  <div className="bg-slate-900/90 p-5 sm:p-6 rounded-2xl border border-indigo-500/40 text-center shadow-2xl relative">
                    <p className="text-[11px] font-extrabold text-indigo-300 uppercase tracking-widest mb-2">
                      Your Secure Connection Code
                    </p>
                    <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4 my-2">
                      <span className="text-3xl sm:text-4xl md:text-5xl font-mono font-black text-white tracking-[0.2em] sm:tracking-[0.25em] drop-shadow-md select-all">
                        {generatedCode.code}
                      </span>
                      <button 
                        type="button"
                        onClick={handleCopyCode}
                        className={`py-2.5 px-4 rounded-xl border font-bold text-xs flex items-center gap-2 transition-all cursor-pointer ${
                          copied 
                            ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400 shadow-md shadow-emerald-500/20' 
                            : 'bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-200 border-indigo-500/40 hover:text-white'
                        }`}
                        title="Copy Code"
                      >
                        {copied ? (
                          <>
                            <Check className="w-4 h-4 text-emerald-400" />
                            <span>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            <span>Copy Code</span>
                          </>
                        )}
                      </button>
                    </div>

                    {generatedCode.expiresAt && (
                      <div className="text-xs text-slate-400 mt-2 flex flex-wrap items-center justify-center gap-2">
                        <span className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-indigo-400" />
                          <span>Valid for 15 minutes • Expires at {formatExpiryTime(generatedCode.expiresAt)}</span>
                        </span>
                        {timeLeft && (
                          <span className={`font-bold px-2.5 py-0.5 rounded-full border text-[11px] ${
                            timeLeft === 'Expired' 
                              ? 'text-amber-400 bg-amber-500/10 border-amber-500/30' 
                              : 'text-indigo-300 bg-indigo-500/20 border-indigo-500/30'
                          }`}>
                            {timeLeft === 'Expired' ? 'Code Expired' : `Expires in ${timeLeft}`}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* ACTION AND STEP GUIDE */}
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-1">
                    <button 
                      type="button"
                      onClick={handleGenerateCode} 
                      disabled={loading} 
                      className="py-2.5 px-5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 font-bold text-xs flex items-center justify-center gap-2 transition-colors cursor-pointer disabled:opacity-50"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Generating...</span>
                        </>
                      ) : (
                        <>
                          <Key className="w-4 h-4 text-indigo-400" />
                          <span>Generate New Code</span>
                        </>
                      )}
                    </button>
                    <p className="text-[11px] text-slate-400 italic text-center sm:text-right">
                      Generating a new code immediately invalidates previous codes.
                    </p>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/60 text-xs space-y-2 text-slate-300">
                    <div className="flex items-center gap-1.5 text-indigo-300 font-bold">
                      <Info className="w-4 h-4 text-indigo-400 shrink-0" />
                      <span>How your caregiver connects:</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-slate-400 pt-1">
                      <div className="bg-slate-800/40 p-2.5 rounded-lg border border-slate-700/40">
                        <strong className="text-white block mb-0.5">1. Share Code</strong>
                        Give <span className="font-mono text-indigo-300 font-bold">{generatedCode.code}</span> to your caregiver.
                      </div>
                      <div className="bg-slate-800/40 p-2.5 rounded-lg border border-slate-700/40">
                        <strong className="text-white block mb-0.5">2. They Connect</strong>
                        They open ORMA → Settings → Family Connections.
                      </div>
                      <div className="bg-slate-800/40 p-2.5 rounded-lg border border-slate-700/40">
                        <strong className="text-white block mb-0.5">3. You Approve</strong>
                        Their request appears below for your confirmation.
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 pt-1">
                  <p className="text-xs text-slate-300 leading-relaxed">
                    Generate a secure, single-use 8-character connection code (formatted as ABCD-1234). Share this code with a family member or caregiver so they can link to your profile and assist with your care.
                  </p>
                  <button 
                    type="button"
                    onClick={handleGenerateCode} 
                    disabled={loading} 
                    className="py-3 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-sm transition-all cursor-pointer flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/25 disabled:opacity-50"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Generating Code...</span>
                      </>
                    ) : (
                      <>
                        <Key className="w-4 h-4" />
                        <span>Generate Connection Code</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </motion.div>

            {/* 2. AUTHORIZED CAREGIVERS & PENDING REQUESTS */}
            <motion.div 
              initial={{ opacity: 0, y: 10 }} 
              animate={{ opacity: 1, y: 0 }} 
              transition={{ delay: 0.05 }} 
              className="p-5 sm:p-6 rounded-2xl bg-slate-800/40 border border-emerald-500/30 space-y-4 shadow-xl overflow-visible"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                    <Users className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white">Authorized Caregivers</h3>
                    <p className="text-xs text-slate-400">Family members permitted to view your care information.</p>
                  </div>
                </div>
                <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                  {linkedUsers.length} Connected
                </span>
              </div>

              {/* Pending Requests Alert */}
              {pendingRequests.length > 0 && (
                <div className="space-y-3 pt-2">
                  <h4 className="text-xs font-bold text-amber-300 flex items-center gap-1.5 uppercase tracking-wider">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    <span>Pending Connection Requests ({pendingRequests.length})</span>
                  </h4>
                  {pendingRequests.map(u => (
                    <div key={u.id} className="bg-amber-950/20 p-4 rounded-xl border border-amber-500/40 space-y-3">
                      <div>
                        <p className="text-xs text-slate-300">
                          <strong className="text-white text-sm block font-bold">{u.name}</strong>
                          {u.email}
                        </p>
                        <p className="text-[11px] text-amber-300/90 mt-1">
                          Would like to connect as your caregiver.
                        </p>
                      </div>
                      <div className="flex gap-2.5">
                        <button 
                          type="button"
                          onClick={() => handleApprove(u.id)} 
                          className="flex-1 py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs transition-colors cursor-pointer"
                        >
                          Approve
                        </button>
                        <button 
                          type="button"
                          onClick={() => handleDecline(u.id)} 
                          className="flex-1 py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition-colors cursor-pointer border border-slate-700"
                        >
                          Decline
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Linked Caregivers List */}
              <div className="space-y-3 pt-1">
                {linkedUsers.length === 0 ? (
                  <div className="p-8 text-center rounded-xl bg-slate-900/40 border border-dashed border-slate-700/60">
                    <Users className="w-8 h-8 text-slate-500 mx-auto mb-2 opacity-50" />
                    <p className="text-sm font-semibold text-slate-300">No caregivers linked yet</p>
                    <p className="text-xs text-slate-500 mt-1">
                      Generate a connection code above to invite a family member.
                    </p>
                  </div>
                ) : (
                  linkedUsers.map(u => (
                    <div key={u.id} className="flex justify-between items-center bg-slate-900/80 p-3.5 rounded-xl border border-slate-700/60 hover:border-slate-600 transition-colors">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-bold text-white">{u.name}</p>
                          <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                            Connected
                          </span>
                        </div>
                        <p className="text-xs text-slate-400">{u.email}</p>
                        {u.phone && (
                          <p className="text-[11px] text-slate-500 flex items-center gap-1">
                            <Phone className="w-3 h-3" />
                            <span>{u.phone}</span>
                          </p>
                        )}
                      </div>
                      <button 
                        type="button"
                        onClick={() => openUnlinkModal(u, 'remove_caregiver')} 
                        className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer shrink-0"
                        title="Remove Caregiver Access"
                      >
                        <UserX className="w-3.5 h-3.5" />
                        <span>Remove Access</span>
                      </button>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </div>
        ) : (
          /* CAREGIVER VIEW */
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="p-6 rounded-2xl bg-slate-800/40 border border-blue-500/30 space-y-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <LinkIcon className="w-5 h-5 text-blue-400"/>
                <span>Link Elderly Account</span>
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Enter the secure connection code (formatted as ABCD-1234) generated from your parent or family member's ORMA screen.
              </p>
              <form onSubmit={handleConnectCaregiver} className="space-y-4 pt-2">
                <div>
                  <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                    Connection Code (e.g. ABCD-1234)
                  </label>
                  <input 
                    type="text" 
                    value={code} 
                    onChange={(e) => setCode(e.target.value.toUpperCase())} 
                    placeholder="ABCD-1234" 
                    className="w-full bg-slate-900/90 border border-slate-700 rounded-xl py-3 px-4 text-white font-mono uppercase tracking-widest text-lg text-center focus:outline-none focus:border-blue-500 transition-colors" 
                    maxLength={9}
                  />
                </div>
                <button 
                  type="submit" 
                  disabled={loading || !code.trim()} 
                  className="w-full py-3.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-sm transition-all cursor-pointer flex items-center justify-center gap-2 shadow-lg shadow-blue-600/20 disabled:opacity-50"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Connect Securely'}
                </button>
              </form>
            </motion.div>
            
            <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.05 }} className="p-6 rounded-2xl bg-slate-800/40 border border-emerald-500/30 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Users className="w-5 h-5 text-emerald-400"/>
                  <span>Linked Patients</span>
                </h3>
                <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                  {linkedUsers.length} Active
                </span>
              </div>

              <div className="space-y-3">
                {linkedUsers.length === 0 ? (
                  <div className="p-8 text-center rounded-xl bg-slate-900/40 border border-dashed border-slate-700/60">
                    <Users className="w-8 h-8 text-slate-500 mx-auto mb-2 opacity-50" />
                    <p className="text-sm font-semibold text-slate-300">No patients linked yet</p>
                    <p className="text-xs text-slate-500 mt-1">
                      Ask your family member to generate a connection code in their ORMA app.
                    </p>
                  </div>
                ) : (
                  linkedUsers.map(u => (
                    <div key={u.id} className="relative flex items-center justify-between bg-slate-900/80 p-3.5 rounded-xl border border-slate-700/60 hover:border-slate-600 transition-colors">
                      <div className="flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-bold text-white">{u.name}</p>
                            <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-widest bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                              Connected
                            </span>
                          </div>
                          <p className="text-xs text-slate-400">{u.email}</p>
                        </div>
                      </div>

                      <div className="relative">
                        <button 
                          type="button"
                          onClick={() => setActiveMenuId(activeMenuId === u.id ? null : u.id)}
                          className="p-2 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg transition-colors cursor-pointer"
                          title="Patient Options"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>

                        {activeMenuId === u.id && (
                          <div className="absolute right-0 top-full mt-1 w-44 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-40 overflow-hidden py-1">
                            <button
                              type="button"
                              onClick={() => openUnlinkModal(u, 'unlink_patient')}
                              className="w-full text-left px-4 py-2 text-xs font-semibold text-red-400 hover:bg-red-500/10 flex items-center gap-2 transition-colors cursor-pointer"
                            >
                              <UserX className="w-4 h-4 text-red-400" />
                              <span>Unlink Patient</span>
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
      </div>

      {/* CONFIRMATION REVOKE/UNLINK MODAL */}
      <AnimatePresence>
        {confirmModal.isOpen && confirmModal.target && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={closeConfirmModal}
              className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
            />

            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              role="dialog"
              aria-modal="true"
              className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl z-10 space-y-5"
            >
              <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 shrink-0">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-white leading-snug">
                      {confirmModal.type === 'unlink_patient' 
                        ? `Unlink ${confirmModal.target.name}?`
                        : `Remove ${confirmModal.target.name}'s access?`}
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">{confirmModal.target.email}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={closeConfirmModal}
                  disabled={confirmModal.loading}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg transition-colors cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="text-xs text-slate-300 leading-relaxed space-y-3">
                <p>
                  {confirmModal.type === 'unlink_patient'
                    ? `You will no longer have access to ${confirmModal.target.name}'s health information, medicine adherence, reminders, reports, or alerts.`
                    : `${confirmModal.target.name} will no longer be able to access your health information, medicine adherence, reminders, reports, or alerts.`}
                </p>
                <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/50 text-[11px] text-slate-400">
                  <strong className="text-slate-200 block mb-0.5">Account & Health Data Safety:</strong>
                  {confirmModal.type === 'unlink_patient'
                    ? `${confirmModal.target.name}'s ORMA account and health records will NOT be deleted.`
                    : `Your ORMA account and health records will remain safe and unchanged.`}
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  ref={modalCancelRef}
                  type="button"
                  onClick={closeConfirmModal}
                  disabled={confirmModal.loading}
                  className="flex-1 py-3 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold rounded-xl transition-colors text-xs cursor-pointer disabled:opacity-50"
                >
                  Cancel
                </button>

                <button
                  type="button"
                  onClick={executeRevokeAccess}
                  disabled={confirmModal.loading}
                  className="flex-1 py-3 px-4 bg-red-600 hover:bg-red-500 text-white font-bold rounded-xl transition-colors text-xs flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-red-600/20 disabled:opacity-50"
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
    </div>
  );
}
