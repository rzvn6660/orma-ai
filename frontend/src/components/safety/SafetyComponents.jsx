import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, AlertOctagon, Info, Eye, EyeOff } from 'lucide-react';

export function RiskBadge({ score }) {
  const styles = {
    Low: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50',
    Medium: 'bg-amber-500/20 text-amber-400 border-amber-500/50',
    High: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
    Critical: 'bg-red-500/20 text-red-400 border-red-500/50',
  };
  
  const icon = score === 'Critical' ? <AlertOctagon className="w-3 h-3" /> :
               score === 'High' ? <AlertTriangle className="w-3 h-3" /> :
               score === 'Medium' ? <Info className="w-3 h-3" /> :
               <ShieldCheck className="w-3 h-3" />;
               
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${styles[score] || styles.Low}`}>
      {icon} {score} Risk
    </span>
  );
}

export function SafetyAlert({ message, type = 'info' }) {
  const styles = {
    info: 'bg-blue-500/10 border-blue-500/30 text-blue-300',
    warning: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
    error: 'bg-red-500/10 border-red-500/30 text-red-300',
  };
  
  return (
    <div className={`p-4 rounded-xl border ${styles[type]} flex gap-3 items-start`}>
      <ShieldAlert className="w-5 h-5 shrink-0 mt-0.5" />
      <p className="text-sm font-medium leading-relaxed">{message}</p>
    </div>
  );
}

export function EmergencyBanner({ onDismiss }) {
  return (
    <div className="bg-red-500 text-white p-4 flex flex-col sm:flex-row items-center justify-between gap-4 rounded-xl shadow-lg shadow-red-500/20 border-2 border-red-400">
      <div className="flex items-center gap-3">
        <AlertOctagon className="w-8 h-8 animate-pulse" />
        <div>
          <h3 className="font-bold text-lg">Emergency Detected</h3>
          <p className="text-sm text-red-100">Please seek immediate medical attention or call emergency services.</p>
        </div>
      </div>
      <div className="flex gap-2 w-full sm:w-auto">
        <button className="flex-1 sm:flex-none px-4 py-2 bg-white text-red-600 font-bold rounded-lg hover:bg-red-50 transition-colors shadow">
          Call 911
        </button>
        {onDismiss && (
          <button onClick={onDismiss} className="px-4 py-2 bg-red-600 font-bold rounded-lg hover:bg-red-700 transition-colors">
            Dismiss
          </button>
        )}
      </div>
    </div>
  );
}

export function PrivacyIndicator({ visibility }) {
  const isPrivate = visibility === 'Private';
  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium border ${isPrivate ? 'bg-slate-800 text-slate-300 border-slate-700' : 'bg-blue-900/30 text-blue-300 border-blue-800/50'}`}>
      {isPrivate ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
      {visibility}
    </div>
  );
}
