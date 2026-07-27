import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { motion } from 'framer-motion';
import { tsgpApi } from '../services/api';
import { useApi } from '../hooks/useApi';
import { ShieldCheck, AlertOctagon, Activity, FileText, CheckCircle2, XCircle, ShieldAlert } from 'lucide-react';
import { RiskBadge, SafetyAlert, PrivacyIndicator } from '../components/safety/SafetyComponents';

export default function SafetyDashboard({ currentView, onViewChange, user, onLogout }) {
  const { data: auditLogs, execute: loadLogs } = useApi(tsgpApi.getSafetyAudits);
  
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    loadLogs(50);
  }, []);

  const handleTest = async (e) => {
    e.preventDefault();
    if (!testInput.trim()) return;
    
    // Simplistic intent detection for testing
    let intent = "GeneralChat";
    if (testInput.toLowerCase().includes("dose") || testInput.toLowerCase().includes("medicine")) {
      intent = "Medication";
    } else if (testInput.toLowerCase().includes("pain") || testInput.toLowerCase().includes("stroke")) {
      intent = "Emergency";
    }
    
    try {
      const result = await tsgpApi.evaluateRequest(testInput, intent);
      setTestResult(result);
      loadLogs(50); // Refresh logs
    } catch(err) {
      console.error(err);
    }
  };

  return (
    <DashboardLayout currentView={currentView} onViewChange={onViewChange} user={user} onLogout={onLogout}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <ShieldCheck className="text-emerald-400" /> Trust & Safety Governance
        </h1>
        <p className="text-slate-400">Monitor clinical risk evaluations, blocked requests, and system safety policies.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Testing Tool */}
        <div className="lg:col-span-1 orma-card p-6 border-slate-700/50 h-fit">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-400" /> Policy Simulator
          </h3>
          <p className="text-sm text-slate-400 mb-4">Type a simulated user request to see how the Clinical Risk Engine evaluates it.</p>
          
          <form onSubmit={handleTest} className="mb-4">
            <input 
              type="text" 
              value={testInput}
              onChange={(e) => setTestInput(e.target.value)}
              placeholder="e.g. Should I double my dose?"
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 outline-none mb-3"
            />
            <button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-xl transition-colors">
              Evaluate Request
            </button>
          </form>
          
          {testResult && (
            <div className="mt-6 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-bold text-slate-300">Decision:</span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                  testResult.action === 'allowed' ? 'bg-emerald-500/20 text-emerald-400' :
                  testResult.action === 'escalated' ? 'bg-red-500/20 text-red-400' :
                  'bg-orange-500/20 text-orange-400'
                }`}>
                  {testResult.action.toUpperCase()}
                </span>
              </div>
              {testResult.risk_score && (
                <div className="flex justify-between items-center">
                  <span className="text-sm font-bold text-slate-300">Calculated Risk:</span>
                  <RiskBadge score={testResult.risk_score} />
                </div>
              )}
              <SafetyAlert 
                message={testResult.explainability} 
                type={testResult.action === 'allowed' ? 'info' : testResult.action === 'escalated' ? 'error' : 'warning'} 
              />
            </div>
          )}
        </div>

        {/* Audit Log */}
        <div className="lg:col-span-2 orma-card p-6 border-slate-700/50">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-purple-400" /> Immutable Audit Trail
          </h3>
          
          <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
            {!auditLogs || auditLogs.length === 0 ? (
              <p className="text-slate-500 text-center py-8">No evaluations recorded yet.</p>
            ) : (
              auditLogs.map(log => (
                <div key={log.id} className="bg-slate-900/50 p-4 rounded-xl border border-slate-700/50 hover:border-slate-600 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <p className="text-slate-200 font-medium text-sm">"{log.request_text}"</p>
                    <RiskBadge score={log.risk_score} />
                  </div>
                  
                  <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50 mb-2">
                    <p className="text-xs text-slate-400"><strong className="text-slate-300">Action:</strong> {log.action_taken.toUpperCase()}</p>
                    <p className="text-xs text-slate-400"><strong className="text-slate-300">Reason:</strong> {log.explainability}</p>
                    {log.policies_applied && log.policies_applied.length > 0 && (
                      <p className="text-xs text-slate-400 mt-1"><strong className="text-slate-300">Policies Triggered:</strong> {log.policies_applied.join(', ')}</p>
                    )}
                  </div>
                  
                  <div className="flex justify-between items-center text-xs text-slate-500">
                    <span className="font-mono">ID: {log.id} • Intent: {log.intent}</span>
                    <span>{new Date(log.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
