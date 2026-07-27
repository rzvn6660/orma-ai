import { Users, ShieldCheck, Heart } from 'lucide-react';
import CaregiverLinkManager from '../components/CaregiverLinkManager';
import FamilyMonitoring from '../components/FamilyMonitoring';
import ErrorBoundary from '../components/ErrorBoundary';

export default function FamilyPage({ user }) {
  return (
    <ErrorBoundary>
      <div className="w-full max-w-7xl mx-auto flex flex-col gap-8 pb-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/60 p-6 md:p-8 rounded-3xl border border-slate-800 backdrop-blur-xl">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-blue-600/20 text-blue-400 flex items-center justify-center border border-blue-500/30">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold text-white tracking-tight">Family & Caregiver Hub</h1>
              <p className="text-slate-400 text-sm md:text-base mt-0.5">
                Manage linked family profiles, caregiver access tokens, and family health monitoring.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="col-span-1 lg:col-span-8">
            <CaregiverLinkManager user={user} />
          </div>
          <div className="col-span-1 lg:col-span-4 flex flex-col gap-6">
            <FamilyMonitoring />
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
