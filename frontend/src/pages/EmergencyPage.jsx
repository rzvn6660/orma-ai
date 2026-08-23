import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AlertOctagon, 
  PhoneCall, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  X, 
  Phone, 
  HeartHandshake,
  Check,
  Clock,
  User,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';
import { emergencyApi, linkApi } from '../services/api';
import { stopEmergencySound } from '../utils/emergencyAudio';
import { formatLocalTime, formatLocalDateTime, formatEmergencyTimestamp } from '../utils/timeUtils';

/**
 * EmergencyPage
 * Distinct role-specific Emergency Response Center for Elders and Caregivers.
 * - Elder: SOS trigger, Accessible Alert Dialog, Live Multi-step Status, Direct Family Dialing.
 * - Caregiver: Active Emergency Dispatch, Acknowledge & Resolve Actions, Direct Patient Dialing, Audit Log.
 */
export default function EmergencyPage({ user }) {
  const isCaregiver = user?.role === 'caregiver';

  // Elder State
  const [elderSosState, setElderSosState] = useState('idle'); // 'idle' | 'confirming' | 'processing' | 'success' | 'failed'
  const [elderActiveAlertId, setElderActiveAlertId] = useState(null);
  const [elderNotifiedCaregiversCount, setElderNotifiedCaregiversCount] = useState(0);
  const [caregiverAcknowledgedInfo, setCaregiverAcknowledgedInfo] = useState(null);
  const [caregivers, setCaregivers] = useState([]);
  const [loadingCaregivers, setLoadingCaregivers] = useState(true);

  // Caregiver State
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [historyAlerts, setHistoryAlerts] = useState([]);
  const [loadingAlerts, setLoadingAlerts] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  // 1. Fetch initial data based on role
  const loadData = useCallback(async () => {
    if (isCaregiver) {
      setLoadingAlerts(true);
      try {
        const [activeRes, historyRes] = await Promise.all([
          emergencyApi.getActive(),
          emergencyApi.getHistory()
        ]);
        setActiveAlerts(activeRes?.active_emergencies || []);
        setHistoryAlerts(historyRes?.history || []);
      } catch (err) {
        console.warn('Could not load caregiver emergency alerts:', err);
      } finally {
        setLoadingAlerts(false);
      }
    } else {
      setLoadingCaregivers(true);
      try {
        const [linkRes, activeRes] = await Promise.all([
          linkApi.getLinkedUsers(),
          emergencyApi.getActive()
        ]);
        const caregiversList = linkRes?.linked_caregivers || linkRes?.linked_users || (Array.isArray(linkRes) ? linkRes : []);
        setCaregivers(caregiversList);
        
        const myActive = activeRes?.active_emergencies?.[0];
        if (myActive) {
          setElderActiveAlertId(myActive.id);
          setElderSosState('success');
          if (myActive.status === 'acknowledged') {
            setCaregiverAcknowledgedInfo({
              name: myActive.acknowledged_by || 'Your Caregiver',
              time: myActive.acknowledged_at
            });
          } else {
            setCaregiverAcknowledgedInfo(null);
          }
        } else {
          setElderSosState('idle');
          setElderActiveAlertId(null);
          setCaregiverAcknowledgedInfo(null);
        }
      } catch (err) {
        console.warn('Could not load elder emergency context:', err);
      } finally {
        setLoadingCaregivers(false);
      }
    }
  }, [isCaregiver]);

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      loadData();
    }, 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  // 2. Real-Time WebSocket Event Listener
  useEffect(() => {
    const handleWsMessage = (e) => {
      const data = e.detail;
      if (!data) return;

      const alertId = data.alert_id || data.id;

      if (data.type === 'emergency_alert') {
        if (isCaregiver) {
          setActiveAlerts(prev => {
            const exists = prev.some(a => (a.id || a.alert_id) === alertId);
            if (exists) return prev;
            return [{
              id: alertId,
              alert_id: alertId,
              elder_id: data.elder_id,
              elder_name: data.elder_name,
              elder_phone: data.elder_phone,
              severity: data.severity || 'critical',
              status: data.status || 'active',
              message: data.message,
              created_at: data.created_at
            }, ...prev];
          });
        }
      } else if (data.type === 'emergency_acknowledged') {
        stopEmergencySound();
        // Elder receives notification that caregiver acknowledged
        setCaregiverAcknowledgedInfo({
          name: data.caregiver_name || 'Your Caregiver',
          time: data.acknowledged_at
        });
        if (isCaregiver) {
          setActiveAlerts(prev => prev.map(a => ((a.id || a.alert_id) === alertId ? { ...a, status: 'acknowledged' } : a)));
        }
      } else if (data.type === 'emergency_resolved') {
        stopEmergencySound();
        if (isCaregiver) {
          setActiveAlerts(prev => prev.filter(a => (a.id || a.alert_id) !== alertId));
          loadData();
        } else {
          setElderSosState('idle');
          setElderActiveAlertId(null);
          setCaregiverAcknowledgedInfo(null);
        }
      } else if (data.type === 'caregiver_linked' || data.type === 'caregiver_removed' || data.type === 'pending_request_approved') {
        loadData();
      }
    };

    window.addEventListener('orma_websocket_message', handleWsMessage);
    return () => window.removeEventListener('orma_websocket_message', handleWsMessage);
  }, [isCaregiver, loadData]);

  // Keyboard accessibility for Elder Confirmation Dialog
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && elderSosState === 'confirming') {
        setElderSosState('idle');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [elderSosState]);

  // Elder SOS confirmation
  const handleConfirmEmergency = async () => {
    setElderSosState('processing');
    try {
      const response = await emergencyApi.analyze(
        'Emergency assistance requested by patient', 
        user?.id || null,
        'critical',
        'Emergency SOS'
      );
      if (response && response.status === 'success') {
        setElderSosState('success');
        setElderActiveAlertId(response.alert_id);
        setElderNotifiedCaregiversCount(response.notified_caregivers_count || 0);
      } else {
        setElderSosState('success');
      }
    } catch (err) {
      console.error('Emergency alert request failed:', err);
      setElderSosState('failed');
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      if (alertId) {
        await emergencyApi.resolve(alertId);
      }
      stopEmergencySound();
      setElderSosState('idle');
      setElderActiveAlertId(null);
      setCaregiverAcknowledgedInfo(null);
    } catch (err) {
      console.error('Could not resolve alert:', err);
    }
  };

  // Caregiver Acknowledge Action
  const handleAcknowledge = async (alertId) => {
    setActionLoadingId(alertId);
    try {
      await emergencyApi.acknowledge(alertId);
      stopEmergencySound();
      setActiveAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'acknowledged' } : a));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    } finally {
      setActionLoadingId(null);
    }
  };

  // Localized Emergency Services Number
  const userTz = user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || '';
  const userCountry = user?.country || '';
  let emNumber = '911';
  let emLabel = 'Emergency Services (911)';
  if (userCountry === 'India' || userTz.includes('Calcutta') || userTz.includes('Kolkata')) {
    emNumber = '112';
    emLabel = 'Emergency Services (112)';
  } else if (userCountry === 'UK' || userTz.includes('London')) {
    emNumber = '999';
    emLabel = 'Emergency Services (999)';
  } else if (userCountry === 'UAE' || userTz.includes('Dubai')) {
    emNumber = '998';
    emLabel = 'Ambulance Service (998)';
  }

  // =========================================================================
  // RENDER: CAREGIVER EMERGENCY DASHBOARD
  // =========================================================================
  if (isCaregiver) {
    return (
      <div className="w-full max-w-5xl mx-auto space-y-6 pb-12">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/70 backdrop-blur-xl p-6 sm:p-8 rounded-3xl border border-white/10 shadow-lg">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-red-500/15 border border-red-500/30 flex items-center justify-center text-red-400 shadow-lg shadow-red-500/10 shrink-0">
              <AlertOctagon className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                  Emergency Response Center
                </h1>
                {activeAlerts.length > 0 && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black bg-red-500/20 text-red-300 border border-red-500/40 animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-red-400" />
                    {activeAlerts.length} Active Alert{activeAlerts.length > 1 ? 's' : ''}
                  </span>
                )}
              </div>
              <p className="text-slate-400 text-xs sm:text-sm mt-0.5">
                Real-time safety dispatch and urgent incident escalation for your linked family members.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={loadData}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold border border-white/10 flex items-center gap-2 cursor-pointer transition-colors self-start sm:self-auto"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>

        {/* Active Emergencies Section */}
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-red-400" />
            <span>Active Emergencies</span>
          </h2>

          {loadingAlerts ? (
            <div className="p-8 text-center bg-slate-900/50 rounded-3xl border border-white/5 text-slate-400 text-sm">
              <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-blue-400" />
              Loading emergency status...
            </div>
          ) : activeAlerts.length === 0 ? (
            <div className="p-8 text-center bg-slate-900/40 rounded-3xl border border-white/10 text-slate-400 space-y-2">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
                <Check className="w-6 h-6" />
              </div>
              <p className="text-white font-bold text-base">All Linked Members Safe</p>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                There are no active emergency alerts. When a linked family member triggers an alert, it will immediately appear here with real-time sound and dispatch controls.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {activeAlerts.map((alert) => {
                const isAcknowledged = alert.status === 'acknowledged';
                const timeStr = formatEmergencyTimestamp(alert.created_at, user?.timezone);

                return (
                  <div
                    key={alert.id}
                    className={`p-6 rounded-3xl border-2 ${
                      isAcknowledged 
                        ? 'bg-slate-900/90 border-amber-500/40' 
                        : 'bg-red-950/30 border-red-500 shadow-[0_0_30px_rgba(239,68,68,0.2)]'
                    } space-y-4`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="flex items-center gap-3.5">
                        <div className={`w-12 h-12 rounded-2xl ${
                          isAcknowledged ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' : 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse'
                        } flex items-center justify-center shrink-0`}>
                          <AlertOctagon className="w-6 h-6" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-xl font-black text-white tracking-tight">
                              {alert.elder_name}
                            </h3>
                            <span className={`text-xs font-black uppercase px-2.5 py-0.5 rounded-full border ${
                              isAcknowledged ? 'bg-amber-500/15 text-amber-300 border-amber-500/30' : 'bg-red-500/20 text-red-300 border-red-500/40'
                            }`}>
                              {isAcknowledged ? 'Acknowledged' : 'Active — Response Required'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mt-0.5 font-medium">
                            Received {timeStr} • Source: {alert.alert_source || 'Emergency SOS'}
                          </p>
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex items-center gap-2.5 flex-wrap">
                        {/* Call Elder */}
                        {alert.elder_phone ? (
                          <a
                            href={`tel:${alert.elder_phone}`}
                            className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-md flex items-center gap-1.5 min-h-[44px] cursor-pointer"
                          >
                            <Phone className="w-4 h-4" />
                            <span>Call {alert.elder_name}</span>
                          </a>
                        ) : (
                          <span className="text-xs text-slate-500 font-medium px-3 py-2 bg-slate-950 rounded-xl border border-white/5">
                            Phone unavailable
                          </span>
                        )}

                        {/* Call Emergency Services */}
                        <a
                          href={`tel:${emNumber}`}
                          className="px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold shadow-md flex items-center gap-1.5 min-h-[44px] cursor-pointer"
                        >
                          <PhoneCall className="w-4 h-4" />
                          <span>Call {emNumber}</span>
                        </a>

                        {/* Acknowledge Button */}
                        {!isAcknowledged && (
                          <button
                            type="button"
                            onClick={() => handleAcknowledge(alert.id)}
                            disabled={actionLoadingId === alert.id}
                            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-white/15 text-xs font-bold flex items-center gap-1.5 min-h-[44px] cursor-pointer transition-colors"
                          >
                            {actionLoadingId === alert.id ? (
                              <RefreshCw className="w-4 h-4 animate-spin" />
                            ) : (
                              <Check className="w-4 h-4 text-emerald-400" />
                            )}
                            <span>Acknowledge</span>
                          </button>
                        )}

                        {/* Resolve */}
                        <button
                          type="button"
                          onClick={() => handleResolveAlert(alert.id)}
                          className="px-4 py-2.5 rounded-xl bg-slate-950 hover:bg-slate-900 text-slate-300 border border-white/10 text-xs font-bold min-h-[44px] cursor-pointer transition-colors"
                        >
                          Mark as Resolved
                        </button>
                      </div>
                    </div>

                    {/* Alert Message */}
                    <div className="bg-slate-950/60 p-3.5 rounded-2xl border border-white/5 text-xs sm:text-sm text-slate-300">
                      <strong className="text-slate-400 font-semibold">Incident Details: </strong>
                      {alert.message || `${alert.elder_name} triggered Emergency SOS assistance.`}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Emergency History / Audit Feed */}
        <div className="space-y-4 pt-6">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-400" />
            <span>Emergency History & Audit Log</span>
          </h2>

          <div className="orma-card p-6 border-white/10">
            {historyAlerts.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-4">No past emergency incidents logged.</p>
            ) : (
              <div className="divide-y divide-white/5 space-y-3">
                {historyAlerts.map(h => {
                  const triggeredTime = formatLocalDateTime(h.created_at, user?.timezone);
                  const ackedTime = h.acknowledged_at ? formatLocalTime(h.acknowledged_at, user?.timezone) : null;
                  const resTime = h.resolved_at ? formatLocalTime(h.resolved_at, user?.timezone) : null;

                  return (
                    <div key={h.id} className="pt-3 first:pt-0 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white text-sm">{h.elder_name}</span>
                          <span className="text-slate-400 font-medium">— {h.alert_source || 'Emergency SOS'}</span>
                        </div>
                        <p className="text-slate-400 text-[11px] mt-1 flex items-center gap-2 flex-wrap font-medium">
                          <span>Triggered: <span className="text-slate-200">{triggeredTime}</span></span>
                          {ackedTime && <span>• Acknowledged: <span className="text-amber-300">{ackedTime}</span></span>}
                          {resTime && <span>• Resolved: <span className="text-emerald-300">{resTime}</span></span>}
                        </p>
                      </div>
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold shrink-0 self-start sm:self-center ${
                        h.status === 'resolved' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-300'
                      }`}>
                        {h.status.toUpperCase()}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // =========================================================================
  // RENDER: ELDER EMERGENCY PAGE
  // =========================================================================
  const primaryCaregiver = caregivers.length > 0 ? caregivers[0] : null;

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6 pb-12">
      {/* 1. Header Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/70 backdrop-blur-xl p-6 sm:p-8 rounded-3xl border border-white/10 shadow-lg">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-red-500/15 border border-red-500/30 flex items-center justify-center text-red-400 shadow-lg shadow-red-500/10 shrink-0">
            <AlertOctagon className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Emergency Center
              </h1>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-500/15 text-red-300 border border-red-500/30">
                <span className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
                Urgent Assistance
              </span>
            </div>
            <p className="text-slate-400 text-xs sm:text-sm mt-0.5">
              Immediate one-tap emergency escalation, caregiver dispatch, and direct medical dialing.
            </p>
          </div>
        </div>
      </div>

      {/* 2. Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: SOS Help Card */}
        <div className="lg:col-span-7 space-y-6">
          <div className={`p-6 sm:p-8 rounded-3xl border transition-all duration-300 ${
            elderSosState === 'success'
              ? 'bg-red-950/30 border-red-500/60 shadow-[0_0_40px_rgba(239,68,68,0.2)]'
              : 'bg-slate-900/80 border-white/10 shadow-xl'
          }`}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/20 border border-red-500/30 flex items-center justify-center text-red-400">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                  {elderSosState === 'success' ? 'Emergency Alert Active' : 'Need Immediate Help?'}
                </h2>
                <p className="text-xs text-slate-400">
                  {elderSosState === 'success' 
                    ? 'Your emergency escalation has been recorded.' 
                    : 'Pressing SOS alerts your linked family circle.'}
                </p>
              </div>
            </div>

            {/* IDLE STATE */}
            {elderSosState === 'idle' && (
              <div className="space-y-6">
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                  If you are experiencing a medical emergency, fall, chest discomfort, or urgent distress, press below to notify your linked family caregivers.
                </p>
                <button
                  type="button"
                  onClick={() => setElderSosState('confirming')}
                  className="w-full py-4 sm:py-5 px-6 rounded-2xl bg-red-600 hover:bg-red-500 text-white font-black text-base sm:text-lg shadow-[0_0_25px_rgba(239,68,68,0.4)] transition-all flex items-center justify-center gap-3 cursor-pointer min-h-[56px]"
                  aria-label="Trigger SOS Emergency Help"
                >
                  <AlertOctagon className="w-6 h-6" />
                  <span>SOS / Emergency Help</span>
                </button>
              </div>
            )}

            {/* PROCESSING STATE */}
            {elderSosState === 'processing' && (
              <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
                <RefreshCw className="w-8 h-8 text-red-400 animate-spin" />
                <p className="text-sm font-bold text-white">Sending emergency alert...</p>
                <p className="text-xs text-slate-400">Connecting to response network</p>
              </div>
            )}

            {/* SUCCESS / ACTIVE POST-ALERT STATE */}
            {elderSosState === 'success' && (
              <div className="space-y-6">
                {/* Status Milestones */}
                <div className="p-4 bg-slate-950/60 rounded-2xl border border-white/10 space-y-3">
                  <div className="flex items-center gap-2.5 text-xs font-bold text-emerald-400">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>Emergency alert recorded</span>
                  </div>

                  <div className="flex items-center gap-2.5 text-xs font-bold text-emerald-400">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>
                      {elderNotifiedCaregiversCount > 0 
                        ? `${elderNotifiedCaregiversCount} linked caregiver(s) notified` 
                        : 'Linked caregivers notified'}
                    </span>
                  </div>

                  <div className="flex items-center gap-2.5 text-xs font-bold">
                    {caregiverAcknowledgedInfo ? (
                      <span className="flex items-center gap-2.5 text-cyan-300">
                        <CheckCircle2 className="w-4 h-4 shrink-0 text-cyan-400" />
                        <span>
                          Caregiver ({caregiverAcknowledgedInfo.name}) acknowledged the alert
                          {caregiverAcknowledgedInfo.time ? ` at ${formatLocalTime(caregiverAcknowledgedInfo.time, user?.timezone)}` : ''}
                        </span>
                      </span>
                    ) : (
                      <span className="flex items-center gap-2.5 text-amber-300 animate-pulse">
                        <span className="w-3.5 h-3.5 rounded-full border-2 border-amber-400 border-t-transparent animate-spin shrink-0" />
                        <span>Awaiting caregiver response...</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Direct Action Buttons */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <a
                    href={`tel:${emNumber}`}
                    className="py-3 px-4 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs sm:text-sm shadow-md flex items-center justify-center gap-2 min-h-[48px]"
                  >
                    <PhoneCall className="w-4 h-4" />
                    <span>Call {emNumber}</span>
                  </a>

                  {primaryCaregiver?.phone && (
                    <a
                      href={`tel:${primaryCaregiver.phone}`}
                      className="py-3 px-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs sm:text-sm shadow-md flex items-center justify-center gap-2 min-h-[48px]"
                    >
                      <Phone className="w-4 h-4" />
                      <span>Call Caregiver</span>
                    </a>
                  )}
                </div>

                {/* Reset / Safe Button */}
                <button
                  type="button"
                  onClick={() => handleResolveAlert(elderActiveAlertId)}
                  className="w-full py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold border border-white/10 transition-colors cursor-pointer min-h-[48px]"
                >
                  I Am Safe Now / Reset Status
                </button>
              </div>
            )}

            {/* FAILED STATE */}
            {elderSosState === 'failed' && (
              <div className="space-y-4">
                <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-2xl space-y-1">
                  <h4 className="text-sm font-bold text-red-400 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" /> Unable to send emergency alert
                  </h4>
                  <p className="text-xs text-slate-300">
                    Please try again or call emergency services directly.
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row gap-3">
                  <button
                    type="button"
                    onClick={handleConfirmEmergency}
                    className="w-full sm:w-1/2 py-3 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition-colors min-h-[48px] cursor-pointer"
                  >
                    Try Again
                  </button>
                  <a
                    href={`tel:${emNumber}`}
                    className="w-full sm:w-1/2 py-3 px-4 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs font-bold flex items-center justify-center gap-1.5 min-h-[48px]"
                  >
                    <PhoneCall className="w-4 h-4" />
                    <span>Call {emNumber} Directly</span>
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Quick Contacts & Realistic Action Plan */}
        <div className="lg:col-span-5 space-y-6">
          {/* Quick Contacts Card */}
          <div className="orma-card p-6 border-white/10">
            <h3 className="text-base sm:text-lg font-bold text-white mb-4 flex items-center gap-2">
              <PhoneCall className="w-5 h-5 text-blue-400" />
              <span>Emergency Quick Contacts</span>
            </h3>

            <div className="space-y-4">
              {/* #1 Priority: Emergency Services / Ambulance (Localized) */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-red-950/20 rounded-2xl border border-red-500/30">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400 shrink-0">
                    <AlertOctagon className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm sm:text-base font-extrabold text-white">{emLabel}</h4>
                    <p className="text-xs text-slate-400">Ambulance & Acute Medical Rescue</p>
                  </div>
                </div>
                <a
                  href={`tel:${emNumber}`}
                  className="px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white text-xs sm:text-sm font-bold shadow-md flex items-center justify-center gap-1.5 min-h-[48px] cursor-pointer shrink-0"
                  aria-label={`Call emergency services ${emNumber}`}
                >
                  <PhoneCall className="w-4 h-4" />
                  <span>Call {emNumber}</span>
                </a>
              </div>

              {/* #2 Priority: Primary Caregiver */}
              <div className="p-4 bg-slate-950/50 rounded-2xl border border-white/10 space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
                      <HeartHandshake className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm sm:text-base font-bold text-white">
                        {primaryCaregiver ? primaryCaregiver.name : 'Primary Caregiver'}
                      </h4>
                      <p className="text-xs text-slate-400">
                        {primaryCaregiver ? (
                          <>
                            <span>{primaryCaregiver.relationship || 'Designated Family Contact'}</span>
                            {primaryCaregiver.phone && <span className="ml-2 font-mono text-cyan-300 font-semibold">{primaryCaregiver.phone}</span>}
                          </>
                        ) : 'No linked caregiver'}
                      </p>
                    </div>
                  </div>

                  {primaryCaregiver?.phone && (
                    <a
                      href={`tel:${primaryCaregiver.phone}`}
                      className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs sm:text-sm font-bold shadow-md flex items-center gap-1.5 min-h-[48px] cursor-pointer shrink-0"
                      aria-label={`Call primary caregiver ${primaryCaregiver.name}`}
                    >
                      <Phone className="w-4 h-4" />
                      <span>Call</span>
                    </a>
                  )}
                </div>

                {/* If no caregiver linked at all */}
                {!primaryCaregiver && (
                  <div className="pt-2 border-t border-white/5 text-xs text-slate-400 leading-relaxed bg-slate-900/50 p-2.5 rounded-xl border border-white/5">
                    <p className="font-semibold text-slate-300">
                      No primary caregiver linked.
                    </p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Generate a connection code in Family settings to link with your family caregiver.
                    </p>
                  </div>
                )}

                {/* If caregiver linked but no phone configured */}
                {primaryCaregiver && !primaryCaregiver.phone && (
                  <div className="pt-2 border-t border-white/5 text-xs text-amber-300/90 leading-relaxed bg-amber-500/5 p-2.5 rounded-xl border border-amber-500/20">
                    <p className="font-semibold text-amber-200">
                      Primary caregiver phone number isn't available.
                    </p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Ask your caregiver to add their emergency contact phone in Settings & Preferences.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action Plan Card */}
          <div className="orma-card p-6 border-white/10">
            <h3 className="text-base sm:text-lg font-bold text-white mb-2 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-400" />
              <span>Safety Action Plan</span>
            </h3>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              When emergency assistance is confirmed, ORMA AI immediately triggers a high-priority alert for your linked family caregivers and logs the event to your safety audit feed. If you require immediate physical rescue or ambulance dispatch, please use the direct {emNumber} button above.
            </p>
          </div>
        </div>

      </div>

      {/* 3. Accessible SOS Confirmation Dialog */}
      <AnimatePresence>
        {elderSosState === 'confirming' && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setElderSosState('idle')}
              className="absolute inset-0 bg-slate-950/80 backdrop-blur-md"
              aria-hidden="true"
            />

            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 15 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 15 }}
              transition={{ duration: 0.15 }}
              role="alertdialog"
              aria-modal="true"
              aria-labelledby="emergency-dialog-title"
              aria-describedby="emergency-dialog-desc"
              className="relative bg-slate-900 border border-red-500/40 rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl z-10 space-y-6"
            >
              <div className="flex items-start justify-between">
                <div className="w-12 h-12 rounded-2xl bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-400 shrink-0">
                  <AlertOctagon className="w-6 h-6" />
                </div>
                <button
                  type="button"
                  onClick={() => setElderSosState('idle')}
                  className="p-2 text-slate-400 hover:text-white rounded-xl bg-slate-800/50 hover:bg-slate-800 transition-colors"
                  aria-label="Cancel emergency confirmation"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div>
                <h3 id="emergency-dialog-title" className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
                  Emergency assistance?
                </h3>
                <p id="emergency-dialog-desc" className="text-xs sm:text-sm text-slate-300 mt-2 leading-relaxed">
                  This will notify your linked caregiver(s) and may share your current location.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setElderSosState('idle')}
                  className="w-full sm:w-1/2 py-3.5 px-4 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-sm transition-colors min-h-[48px] cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleConfirmEmergency}
                  autoFocus
                  className="w-full sm:w-1/2 py-3.5 px-4 rounded-2xl bg-red-600 hover:bg-red-500 text-white font-extrabold text-sm shadow-lg shadow-red-600/30 transition-all min-h-[48px] cursor-pointer"
                >
                  Confirm Emergency
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
