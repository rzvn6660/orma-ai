import { motion } from 'framer-motion';
import { HeartPulse, Plus, CheckCircle2, TrendingUp, Activity, FileText, Brain, AlertCircle, Share2, Stethoscope, Watch } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';



function TimelinePreview() {
  return (
    <Card className="w-full relative overflow-hidden">
      <div className="absolute top-0 right-0 bg-blue-500/10 text-blue-400 text-[10px] uppercase tracking-widest font-bold px-3 py-1 rounded-bl-lg">
        Preview Layout
      </div>
      <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
        <Activity className="w-5 h-5 text-slate-400" /> Upcoming History
      </h3>
      
      <div className="space-y-4 opacity-50 pointer-events-none grayscale-[50%]">
        <div className="flex justify-between items-center p-4 bg-slate-800/50 rounded-xl border border-slate-700 border-dashed">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-slate-700 rounded-lg"><HeartPulse className="w-4 h-4 text-slate-400" /></div>
            <div>
              <div className="h-4 w-24 bg-slate-700 rounded mb-2"></div>
              <div className="h-3 w-32 bg-slate-700/50 rounded"></div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-6 w-16 bg-slate-700 rounded"></div>
          </div>
        </div>
        
        <div className="flex justify-between items-center p-4 bg-slate-800/50 rounded-xl border border-slate-700 border-dashed">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-slate-700 rounded-lg"><Activity className="w-4 h-4 text-slate-400" /></div>
            <div>
              <div className="h-4 w-20 bg-slate-700 rounded mb-2"></div>
              <div className="h-3 w-28 bg-slate-700/50 rounded"></div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-6 w-12 bg-slate-700 rounded"></div>
          </div>
        </div>
      </div>
    </Card>
  );
}

export default function EmptyHealthState({ onAddReading }) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto space-y-8 pb-12"
    >
      {/* Hero Section */}
      <Card className="text-center py-12 relative overflow-hidden border-blue-500/20 bg-slate-900/60 shadow-[0_0_50px_rgba(59,130,246,0.05)]">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent pointer-events-none" />
        
        <div className="w-20 h-20 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-6 shadow-inner border border-slate-700 relative">
          <div className="absolute inset-0 rounded-full animate-ping bg-blue-500/10" />
          <span className="text-4xl">🩺</span>
        </div>
        
        <h2 className="text-2xl font-bold text-white mb-4 tracking-wide">
          Start Building Your Health History
        </h2>
        
        <p className="text-slate-400 max-w-lg mx-auto mb-8 leading-relaxed">
          Track your Blood Pressure, Blood Sugar, Heart Rate, Oxygen Level, Temperature and Weight. 
          ORMA AI will organize your records and help you monitor long-term health trends.
        </p>
        
        <Button variant="primary" onClick={onAddReading} className="px-8 mx-auto shadow-[0_0_30px_rgba(59,130,246,0.3)] hover:scale-105">
          <Plus className="w-5 h-5" /> Add First Health Reading
        </Button>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        
        {/* Left Column */}
        <div className="space-y-8">
          
          {/* Why Track Health */}
          <Card>
            <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <FileText className="w-5 h-5 text-emerald-400" /> Why Health Records Matter
            </h3>
            <ul className="space-y-4">
              <li className="flex items-start gap-3">
                <TrendingUp className="w-5 h-5 text-blue-400 mt-0.5 shrink-0" />
                <span className="text-slate-300 text-sm leading-relaxed">Detect long-term trends and identify potential issues early.</span>
              </li>
              <li className="flex items-start gap-3">
                <Brain className="w-5 h-5 text-purple-400 mt-0.5 shrink-0" />
                <span className="text-slate-300 text-sm leading-relaxed">Enable Orma AI to provide better, personalized health summaries.</span>
              </li>
              <li className="flex items-start gap-3">
                <Share2 className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
                <span className="text-slate-300 text-sm leading-relaxed">Keep your family network and caregivers informed securely.</span>
              </li>
              <li className="flex items-start gap-3">
                <Stethoscope className="w-5 h-5 text-cyan-400 mt-0.5 shrink-0" />
                <span className="text-slate-300 text-sm leading-relaxed">Generate organized reports to share during doctor visits.</span>
              </li>
            </ul>
          </Card>

          <TimelinePreview />

        </div>

        {/* Right Column */}
        <div className="space-y-8">
          
          {/* Product Roadmap */}
          <Card className="bg-slate-800/20 border-slate-700/30">
            <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-slate-400" /> Product Roadmap
            </h3>
            <div className="space-y-5 relative before:absolute before:inset-0 before:ml-2.5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-slate-700/50">
              
              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-500/20 border-2 border-emerald-500 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-[0_0_10px_rgba(16,185,129,0.3)] z-10">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                </div>
                <div className="w-[calc(100%-3rem)] md:w-[calc(50%-2rem)] p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/5">
                  <h4 className="font-bold text-emerald-400 text-sm mb-1">Manual Health Records</h4>
                  <p className="text-xs text-slate-400">Available Today</p>
                </div>
              </div>
              
              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                <div className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-800 border-2 border-slate-600 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                  <Watch className="w-3 h-3 text-slate-500" />
                </div>
                <div className="w-[calc(100%-3rem)] md:w-[calc(50%-2rem)] p-3 rounded-lg border border-slate-700 bg-slate-800/30">
                  <h4 className="font-bold text-slate-300 text-sm mb-1">Wearable Device Sync</h4>
                  <p className="text-xs text-slate-500 font-mono">Future Version</p>
                </div>
              </div>

              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                <div className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-800 border-2 border-slate-600 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                  <Brain className="w-3 h-3 text-slate-500" />
                </div>
                <div className="w-[calc(100%-3rem)] md:w-[calc(50%-2rem)] p-3 rounded-lg border border-slate-700 bg-slate-800/30">
                  <h4 className="font-bold text-slate-300 text-sm mb-1">AI Health Trend Analysis</h4>
                  <p className="text-xs text-slate-500 font-mono">Future Version</p>
                </div>
              </div>

              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
                <div className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-800 border-2 border-slate-600 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10">
                  <AlertCircle className="w-3 h-3 text-slate-500" />
                </div>
                <div className="w-[calc(100%-3rem)] md:w-[calc(50%-2rem)] p-3 rounded-lg border border-slate-700 bg-slate-800/30">
                  <h4 className="font-bold text-slate-300 text-sm mb-1">Caregiver Alerts</h4>
                  <p className="text-xs text-slate-500 font-mono">Future Version</p>
                </div>
              </div>

            </div>
          </Card>

          {/* Future Integration Map */}
          <Card className="bg-slate-800/40 border-slate-700/50">
            <div className="mb-6">
              <div className="flex items-center justify-between gap-4 mb-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Watch className="w-5 h-5 text-blue-400" /> Future Integrations
                </h3>
                <span className="px-2.5 py-1 bg-slate-700/50 text-slate-300 text-[10px] uppercase tracking-wider font-bold rounded-lg border border-slate-600/50 whitespace-nowrap">
                  Planned for Future Release
                </span>
              </div>
              <p className="text-sm text-slate-400 leading-relaxed">
                Automatic synchronization with wearable devices and home medical equipment is planned for a future version of ORMA AI. The current MVP focuses on reliable manual health record entry to provide a stable user experience.
              </p>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/30 border border-slate-700/30">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-700/50 rounded-lg"><Watch className="w-4 h-4 text-slate-400" /></div>
                  <span className="text-sm font-medium text-slate-300">Wearable Device Synchronization</span>
                </div>
                <span className="text-xs text-slate-500 font-medium">Planned</span>
              </div>
              
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/30 border border-slate-700/30">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-700/50 rounded-lg"><Activity className="w-4 h-4 text-slate-400" /></div>
                  <span className="text-sm font-medium text-slate-300">Home Medical Device Integration</span>
                </div>
                <span className="text-xs text-slate-500 font-medium">Planned</span>
              </div>
              
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/30 border border-slate-700/30">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-700/50 rounded-lg"><Brain className="w-4 h-4 text-slate-400" /></div>
                  <span className="text-sm font-medium text-slate-300">AI Health Trend Analysis</span>
                </div>
                <span className="text-xs text-slate-500 font-medium">Planned</span>
              </div>
            </div>
          </Card>

        </div>
      </div>
    </motion.div>
  );
}
