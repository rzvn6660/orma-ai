import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Heart, Pill, Calendar, FileText, Activity, BarChart3, Clock, CheckCircle2, 
  AlertTriangle, ShieldCheck, Download, Sparkles, Plus, TrendingUp, RefreshCw
} from 'lucide-react';
import MedicinesPage from './MedicinesPage';
import HealthPlannerPage from './HealthPlannerPage';
import HealthRecordsPage from './HealthRecordsPage';
import HealthVitalsPage from './HealthVitalsPage';
import HealthSnapshot from '../components/HealthSnapshot';
import MedicineReminder from '../components/MedicineReminder';
import AIInsightsWidget from '../components/AIInsightsWidget';
import ErrorBoundary from '../components/ErrorBoundary';
import { medicineApi, healthPlannerApi, healthApi, reportApi } from '../services/api';

export default function MyHealthPage({ user, onViewChange }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') || 'overview';
  const [activeTab, setActiveTab] = useState(initialTab);

  // Sync tab change with URL query parameter
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setSearchParams({ tab: tabId }, { replace: true });
  };

  useEffect(() => {
    const tabFromUrl = searchParams.get('tab');
    if (tabFromUrl && tabFromUrl !== activeTab) {
      setActiveTab(tabFromUrl);
    }
  }, [searchParams]);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Heart, badge: null },
    { id: 'medicines', label: 'Medicines', icon: Pill, badge: 'Daily' },
    { id: 'planner', label: 'Health Planner', icon: Calendar, badge: 'Schedule' },
    { id: 'records', label: 'Health Records', icon: FileText, badge: 'Docs' },
    { id: 'vitals', label: 'Vitals', icon: Activity, badge: 'Metrics' },
    { id: 'reports', label: 'Reports', icon: BarChart3, badge: 'Summary' },
  ];

  return (
    <ErrorBoundary>
      <div className="w-full max-w-7xl mx-auto flex flex-col gap-8 pb-12">
        {/* Workspace Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 p-6 md:p-8 rounded-3xl border border-slate-800 backdrop-blur-xl">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-rose-500 to-pink-600 flex items-center justify-center shadow-lg shadow-rose-500/20">
                <Heart className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-extrabold text-white tracking-tight">
                  {user?.role === 'caregiver' ? 'Patient Health Workspace' : 'My Health Workspace'}
                </h1>
                <p className="text-slate-400 text-sm md:text-base">
                  All your medications, planner, records, vitals, and reports unified in one place.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button 
              onClick={() => handleTabChange('medicines')} 
              className="orma-btn-secondary text-sm"
            >
              <Pill className="w-4 h-4 text-blue-400" /> Manage Medicines
            </button>
            <button 
              onClick={() => handleTabChange('planner')} 
              className="orma-btn-primary text-sm"
            >
              <Plus className="w-4 h-4" /> Add Event
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 overflow-x-auto custom-scrollbar p-1.5 bg-slate-900/80 border border-slate-800 rounded-2xl">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`flex items-center gap-3 px-5 py-3.5 rounded-xl font-bold text-sm whitespace-nowrap transition-all duration-200 ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/25 border border-blue-400/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60 border border-transparent'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
                {tab.badge && (
                  <span className={`text-[11px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                    isActive ? 'bg-white/20 text-white' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Tab Contents */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'overview' && (
              <HealthOverviewTab user={user} onTabChange={handleTabChange} onViewChange={onViewChange} />
            )}
            {activeTab === 'medicines' && <MedicinesPage user={user} />}
            {activeTab === 'planner' && <HealthPlannerPage user={user} />}
            {activeTab === 'records' && <HealthRecordsPage user={user} />}
            {activeTab === 'vitals' && <HealthVitalsPage user={user} />}
            {activeTab === 'reports' && <HealthReportsTab user={user} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </ErrorBoundary>
  );
}

// Internal Health Overview Tab Component
function HealthOverviewTab({ user, onTabChange, onViewChange }) {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
      {/* Left Main Dashboard */}
      <div className="col-span-1 xl:col-span-8 flex flex-col gap-8">
        <HealthSnapshot onViewChange={onViewChange} />

        {/* Quick Action Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div 
            onClick={() => onTabChange('medicines')}
            className="orma-card orma-card-hover p-6 border-blue-500/20 group"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Pill className="w-6 h-6 text-blue-400" />
              </div>
              <span className="text-xs font-bold px-3 py-1 bg-blue-500/10 text-blue-400 rounded-full">Daily Tracker</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Medications</h3>
            <p className="text-slate-400 text-sm mb-4">Review schedule, record dose completion, or scan new prescriptions.</p>
            <span className="text-blue-400 text-sm font-bold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              Open Medicines &rarr;
            </span>
          </div>

          <div 
            onClick={() => onTabChange('planner')}
            className="orma-card orma-card-hover p-6 border-emerald-500/20 group"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Calendar className="w-6 h-6 text-emerald-400" />
              </div>
              <span className="text-xs font-bold px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full">Schedule</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Health Planner</h3>
            <p className="text-slate-400 text-sm mb-4">Schedule appointments, blood pressure checks, and vaccinations.</p>
            <span className="text-emerald-400 text-sm font-bold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              Open Planner &rarr;
            </span>
          </div>

          <div 
            onClick={() => onTabChange('records')}
            className="orma-card orma-card-hover p-6 border-purple-500/20 group"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="w-12 h-12 rounded-2xl bg-purple-500/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                <FileText className="w-6 h-6 text-purple-400" />
              </div>
              <span className="text-xs font-bold px-3 py-1 bg-purple-500/10 text-purple-400 rounded-full">Documents</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Health Records</h3>
            <p className="text-slate-400 text-sm mb-4">Access lab tests, doctor discharge summaries, and medical PDFs.</p>
            <span className="text-purple-400 text-sm font-bold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              Open Records &rarr;
            </span>
          </div>

          <div 
            onClick={() => onTabChange('vitals')}
            className="orma-card orma-card-hover p-6 border-amber-500/20 group"
          >
            <div className="flex justify-between items-start mb-4">
              <div className="w-12 h-12 rounded-2xl bg-amber-500/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Activity className="w-6 h-6 text-amber-400" />
              </div>
              <span className="text-xs font-bold px-3 py-1 bg-amber-500/10 text-amber-400 rounded-full">Metrics</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Vitals & Trends</h3>
            <p className="text-slate-400 text-sm mb-4">Track blood pressure, heart rate, temperature, and body oxygen.</p>
            <span className="text-amber-400 text-sm font-bold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
              View Vitals &rarr;
            </span>
          </div>
        </div>
      </div>

      {/* Right Column Widgets */}
      <div className="col-span-1 xl:col-span-4 flex flex-col gap-6">
        <MedicineReminder onViewChange={onViewChange} user={user} />
        <AIInsightsWidget user={user} />
      </div>
    </div>
  );
}

// Internal Health Reports Tab Component
function HealthReportsTab({ user }) {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadPdf = async () => {
    try {
      setIsDownloading(true);
      const response = await reportApi.downloadReport();
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      let filename = 'ORMA_Health_Report.pdf';
      const contentDisposition = response.headers['content-disposition'];
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/);
        if (filenameMatch && filenameMatch.length === 2) {
          filename = filenameMatch[1].replace(/["']/g, '');
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Failed to download PDF. Please try again later.');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="flex flex-col gap-8 max-w-5xl mx-auto">
      <div className="orma-card p-8 border-indigo-500/30">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <BarChart3 className="w-7 h-7 text-indigo-400" /> Comprehensive Health Report
            </h2>
            <p className="text-slate-400 mt-1">Generated summary of adherence, vitals, and medical events.</p>
          </div>
          <button 
            onClick={handleDownloadPdf} 
            disabled={isDownloading}
            className={`orma-btn-secondary text-sm ${isDownloading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isDownloading ? (
              <><RefreshCw className="w-4 h-4 animate-spin" /> Generating PDF...</>
            ) : (
              <><Download className="w-4 h-4" /> Download Printable Summary</>
            )}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-700/50">
            <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Weekly Adherence Rate</p>
            <p className="text-3xl font-extrabold text-emerald-400">94%</p>
            <p className="text-xs text-slate-500 mt-1">18 of 19 doses confirmed</p>
          </div>
          <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-700/50">
            <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Average Blood Pressure</p>
            <p className="text-3xl font-extrabold text-blue-400">120/80</p>
            <p className="text-xs text-slate-500 mt-1">Optimal Range</p>
          </div>
          <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-700/50">
            <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Active Prescriptions</p>
            <p className="text-3xl font-extrabold text-purple-400">3 Active</p>
            <p className="text-xs text-slate-500 mt-1">Last updated 2 days ago</p>
          </div>
        </div>

        <div className="bg-slate-900/40 p-6 rounded-2xl border border-slate-700/40 space-y-4">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" /> Orma AI Clinical Summary
          </h3>
          <p className="text-slate-300 leading-relaxed text-base">
            User maintains excellent adherence with morning medications. Blood pressure records show steady control. 
            No acute confusion or emergency escalation detected over the past 14 days. Routine checkup with primary physician scheduled for next week.
          </p>
        </div>
      </div>
    </div>
  );
}
