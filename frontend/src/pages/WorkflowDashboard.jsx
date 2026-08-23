import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import { motion } from 'framer-motion';
import { oweApi } from '../services/api';
import { useApi } from '../hooks/useApi';
import { 
  Activity, CheckCircle2, XCircle, Clock, AlertTriangle, Play, RefreshCw
} from 'lucide-react';

export default function WorkflowDashboard({ currentView, onViewChange, user, onLogout }) {
  const { data: auditLogs, execute: loadLogs } = useApi(oweApi.getAuditLogs);
  const { data: approvals, execute: loadApprovals } = useApi(oweApi.getPendingApprovals);
  
  const [activeTab, setActiveTab] = useState('approvals'); // approvals, audit

  const loadData = () => {
    loadLogs(50);
    loadApprovals();
  };

  useEffect(() => {
    loadData();
    
    // Subscribe to SSE for live updates
    const apiBase = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000');
    const eventSource = new EventSource(`${apiBase}/api/owe/events`);
    
    eventSource.onmessage = (event) => {
      console.log("Received OWE Event:", event.data);
      // Refresh data without polling
      loadData();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  const handleResolve = async (id, status) => {
    await oweApi.resolveApproval(id, status);
    loadData();
  };

  const handleTestTrigger = async (eventName) => {
    await oweApi.testTrigger(eventName);
    // UI will auto refresh via SSE
  };

  const renderApprovals = () => {
    if (!approvals || approvals.length === 0) {
      return (
        <div className="text-center py-12 border border-dashed border-slate-700 rounded-2xl bg-slate-900/50">
          <CheckCircle2 className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-slate-300 mb-2">No Pending Approvals</h3>
          <p className="text-slate-500 mb-6">There are no sensitive actions waiting for your confirmation.</p>
          <div className="flex justify-center gap-2">
            <button onClick={() => handleTestTrigger('MedicineModified', 'modify')} className="px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-colors">
              Test Medicine Modify
            </button>
            <button onClick={() => handleTestTrigger('AppointmentRescheduled', 'reschedule')} className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors">
              Test Appt Reschedule
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {approvals.map((req, idx) => (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            key={req.id} 
            className="orma-card p-6 border-amber-500/30 bg-amber-900/10"
          >
            <div className="flex items-start gap-4">
              <div className="p-3 bg-amber-500/20 rounded-xl">
                <AlertTriangle className="w-6 h-6 text-amber-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-white mb-2 capitalize">Approval Required: {req.action_type.replace('_', ' ')}</h3>
                <p className="text-slate-300 mb-4">ORMA AI needs your permission to proceed with this workflow.</p>
                
                <div className="bg-slate-900/80 p-4 rounded-xl border border-slate-700/50 mb-4 font-mono text-xs text-slate-400 overflow-x-auto">
                  {JSON.stringify(req.payload, null, 2)}
                </div>

                <div className="flex gap-3 mt-4">
                  <button onClick={() => handleResolve(req.id, 'approved')} className="flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 rounded-lg font-bold transition-colors">
                    <CheckCircle2 className="w-5 h-5" /> Approve Action
                  </button>
                  <button onClick={() => handleResolve(req.id, 'rejected')} className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg font-bold transition-colors">
                    <XCircle className="w-5 h-5" /> Reject
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    );
  };

  const renderAudit = () => {
    if (!auditLogs || auditLogs.length === 0) {
      return <p className="text-slate-500 text-center py-8">No workflows have run yet.</p>;
    }

    return (
      <div className="space-y-3">
        <div className="flex justify-end gap-2 mb-4">
          <button onClick={() => handleTestTrigger('EmergencyDetected', 'create')} className="px-3 py-1.5 bg-red-500/20 text-red-400 text-xs rounded-lg font-bold">
            Simulate Emergency Workflow
          </button>
          <button onClick={() => handleTestTrigger('MedicineCreated', 'create')} className="px-3 py-1.5 bg-emerald-500/20 text-emerald-400 text-xs rounded-lg font-bold">
            Simulate Medicine Creation
          </button>
        </div>
        {auditLogs.map(log => (
          <div key={log.id} className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50 flex justify-between items-center">
            <div>
              <p className="text-white font-medium flex items-center gap-2">
                <Activity className="w-4 h-4 text-purple-400" />
                {log.workflow_id}
              </p>
              <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                <span>Actor: {log.actor}</span>
                <span>Retries: {log.retries}</span>
                <span>ID: {log.idempotency_key?.substring(0, 8)}...</span>
              </div>
            </div>
            <div className="text-right">
              <div className={`inline-flex px-3 py-1 rounded-full text-xs font-bold mb-1 ${
                log.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' :
                log.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                log.status === 'pending_approval' ? 'bg-amber-500/20 text-amber-400' :
                'bg-blue-500/20 text-blue-400'
              }`}>
                {log.status.toUpperCase()}
              </div>
              <p className="text-xs text-slate-500 block">{new Date(log.created_at).toLocaleTimeString()}</p>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <DashboardLayout currentView={currentView} onViewChange={onViewChange} user={user} onLogout={onLogout}>
      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <Activity className="text-purple-400" /> Action & Workflow Engine
          </h1>
          <p className="text-slate-400">Monitor automated workflows, resolve approvals, and view audit trails in real-time.</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 bg-emerald-400/10 px-3 py-1.5 rounded-full">
          <RefreshCw className="w-3 h-3 animate-spin-slow" /> Live Sync Active
        </div>
      </div>

      <div className="flex gap-2 mb-8 border-b border-slate-800 pb-2">
        <button 
          onClick={() => setActiveTab('approvals')}
          className={`px-4 py-2 font-bold transition-colors flex items-center gap-2 ${activeTab === 'approvals' ? 'text-amber-400 border-b-2 border-amber-400' : 'text-slate-500 hover:text-slate-300'}`}
        >
          Pending Approvals
          {approvals?.length > 0 && (
            <span className="bg-amber-500 text-white text-xs px-2 py-0.5 rounded-full">{approvals.length}</span>
          )}
        </button>
        <button 
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 font-bold transition-colors ${activeTab === 'audit' ? 'text-purple-400 border-b-2 border-purple-400' : 'text-slate-500 hover:text-slate-300'}`}
        >
          Workflow Audit Log
        </button>
      </div>

      <div>
        {activeTab === 'approvals' ? renderApprovals() : renderAudit()}
      </div>
    </DashboardLayout>
  );
}
