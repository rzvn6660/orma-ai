import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Activity, Heart, Thermometer, Droplets, Search, Filter, ArrowUpDown, MoreVertical, Edit2, Trash2, Eye, Plus, TrendingUp } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import ChartWrapper from '../../components/ChartWrapper';

// VITAL CONFIG
const VITAL_TYPES = {
  blood_pressure: { label: 'Blood Pressure', icon: Heart, color: 'text-rose-500', bg: 'bg-rose-500/10' },
  heart_rate: { label: 'Heart Rate', icon: Activity, color: 'text-rose-400', bg: 'bg-rose-400/10' },
  spo2: { label: 'Oxygen', icon: Droplets, color: 'text-cyan-500', bg: 'bg-cyan-500/10' },
  temperature: { label: 'Temperature', icon: Thermometer, color: 'text-amber-500', bg: 'bg-amber-500/10' },
  weight: { label: 'Weight', icon: Activity, color: 'text-blue-400', bg: 'bg-blue-400/10' },
  blood_sugar: { label: 'Blood Sugar', icon: Droplets, color: 'text-red-500', bg: 'bg-red-500/10' }
};

// MOCK DATA (Can be replaced by API later)
const MOCK_HISTORY = [
  { id: 1, vital_type: 'blood_pressure', value: '120/80', unit: 'mmHg', date: '2026-07-15', time: '08:00', status: 'Normal' },
  { id: 2, vital_type: 'heart_rate', value: '72', unit: 'bpm', date: '2026-07-15', time: '08:05', status: 'Normal' },
  { id: 3, vital_type: 'spo2', value: '98', unit: '%', date: '2026-07-15', time: '08:10', status: 'Normal' },
  { id: 4, vital_type: 'temperature', value: '98.6', unit: '°F', date: '2026-07-15', time: '08:15', status: 'Normal' },
  { id: 5, vital_type: 'weight', value: '65', unit: 'kg', date: '2026-07-15', time: '08:20', status: 'Normal' },
  
  { id: 6, vital_type: 'blood_pressure', value: '128/82', unit: 'mmHg', date: '2026-07-14', time: '09:00', status: 'Elevated' },
  { id: 7, vital_type: 'heart_rate', value: '74', unit: 'bpm', date: '2026-07-14', time: '09:05', status: 'Normal' },
  { id: 8, vital_type: 'spo2', value: '97', unit: '%', date: '2026-07-14', time: '09:10', status: 'Normal' },
  { id: 9, vital_type: 'weight', value: '65.3', unit: 'kg', date: '2026-07-14', time: '09:15', status: 'Normal' },
  
  { id: 10, vital_type: 'blood_pressure', value: '118/78', unit: 'mmHg', date: '2026-07-13', time: '07:30', status: 'Normal' },
  { id: 11, vital_type: 'temperature', value: '99.1', unit: '°F', date: '2026-07-13', time: '07:35', status: 'Elevated' },
  { id: 12, vital_type: 'heart_rate', value: '70', unit: 'bpm', date: '2026-07-13', time: '07:40', status: 'Normal' }
];

const StatusBadge = ({ status }) => {
  if (!status) return null;
  const styles = {
    Normal: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    Elevated: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    High: 'bg-red-500/10 text-red-400 border-red-500/20'
  };
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${styles[status] || 'bg-slate-700/50 text-slate-300'}`}>
      {status}
    </span>
  );
};

const RecordActions = ({ onEdit, onDelete, record }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className="p-2 text-slate-400 hover:text-white rounded-full hover:bg-slate-700/50 transition-colors">
        <MoreVertical className="w-4 h-4" />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-2 w-32 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl z-20 overflow-hidden">
            <button className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 flex items-center gap-2">
              <Eye className="w-3.5 h-3.5" /> View
            </button>
            <button onClick={() => { setOpen(false); onEdit?.(record); }} className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 flex items-center gap-2">
              <Edit2 className="w-3.5 h-3.5" /> Edit
            </button>
            <button onClick={() => { setOpen(false); onDelete?.(record.id); }} className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-slate-700 flex items-center gap-2">
              <Trash2 className="w-3.5 h-3.5" /> Delete
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default function HealthHistoryTab({ records = [], onAddReading, onEdit, onDelete }) {
  const isDemo = records.length === 0;
  const activeRecords = isDemo ? MOCK_HISTORY : records;

  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [sortOrder, setSortOrder] = useState('newest');
  const [activeChartVital, setActiveChartVital] = useState('blood_pressure');
  const [chartTimeRange, setChartTimeRange] = useState('30');

  // Filter and Sort Data
  const processedData = useMemo(() => {
    let data = [...activeRecords];
    
    // Filter
    if (filterType !== 'all') {
      data = data.filter(d => d.vital_type === filterType);
    }
    
    // Search
    if (search) {
      data = data.filter(d => 
        (VITAL_TYPES[d.vital_type]?.label || '').toLowerCase().includes(search.toLowerCase()) ||
        d.value.includes(search)
      );
    }
    
    // Sort
    data.sort((a, b) => {
      const dateA = new Date(`${a.date}T${a.time}`);
      const dateB = new Date(`${b.date}T${b.time}`);
      return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
    });

    return data;
  }, [search, filterType, sortOrder]);

  // Group by Date
  const groupedData = useMemo(() => {
    const groups = {};
    processedData.forEach(record => {
      const dateLabel = new Date(record.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
      if (!groups[dateLabel]) groups[dateLabel] = [];
      groups[dateLabel].push(record);
    });
    return groups;
  }, [processedData]);

  // Chart Data preparation (needs to be ascending for chart)
  const chartData = useMemo(() => {
    const subset = activeRecords.filter(r => r.vital_type === activeChartVital).slice(0, parseInt(chartTimeRange)).reverse();
    return subset.map(r => {
      if (activeChartVital === 'blood_pressure') {
        const [sys, dia] = r.value.split('/');
        return { name: r.date, sys: parseInt(sys), dia: parseInt(dia) };
      }
      return { name: r.date, value: parseFloat(r.value) };
    });
  }, [activeChartVital, activeRecords]);

  if (activeRecords.length === 0) {
    return (
      <Card className="text-center py-20 flex flex-col items-center">
        <Activity className="w-12 h-12 text-slate-500 mb-4 opacity-50" />
        <h3 className="text-xl font-bold text-white mb-2">No health records yet</h3>
        <p className="text-slate-400 mb-6">Start tracking your vitals to see history.</p>
        <Button onClick={onAddReading}><Plus className="w-4 h-4"/> Add Health Reading</Button>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* TREND CHART */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
          <div className="flex items-center gap-3">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-400" /> Health Trends
            </h3>
            {isDemo && (
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-widest bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                Demo Data
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-3 w-full md:w-auto">
            <select 
              value={chartTimeRange}
              onChange={(e) => setChartTimeRange(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
            >
              <option value="7">Last 7 Days</option>
              <option value="30">Last 30 Days</option>
              <option value="90">Last 90 Days</option>
            </select>
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-4 w-full hide-scrollbar">
          {Object.keys(VITAL_TYPES).map(vKey => {
            const meta = VITAL_TYPES[vKey];
            const Icon = meta.icon;
            return (
              <button 
                key={vKey}
                onClick={() => setActiveChartVital(vKey)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 whitespace-nowrap ${
                  activeChartVital === vKey 
                    ? 'bg-blue-600 text-white border border-blue-500' 
                    : 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700'
                }`}
              >
                <Icon className="w-3.5 h-3.5" /> {meta.label}
              </button>
            )
          })}
        </div>
        
        <div className="h-64 w-full">
          <ChartWrapper height={256}>
            <ResponsiveContainer width="100%" height="100%">
              {activeChartVital === 'blood_pressure' ? (
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis dataKey="name" stroke="#94a3b8" tick={{fontSize: 12}} />
                  <YAxis stroke="#94a3b8" tick={{fontSize: 12}} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }} />
                  <Line type="monotone" dataKey="sys" name="Systolic" stroke="#ef4444" strokeWidth={3} dot={{r: 4, fill: '#ef4444'}} />
                  <Line type="monotone" dataKey="dia" name="Diastolic" stroke="#3b82f6" strokeWidth={3} dot={{r: 4, fill: '#3b82f6'}} />
                </LineChart>
              ) : (
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis dataKey="name" stroke="#94a3b8" tick={{fontSize: 12}} />
                  <YAxis stroke="#94a3b8" tick={{fontSize: 12}} />
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#fff' }} />
                  <Area type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorVal)" />
                </AreaChart>
              )}
            </ResponsiveContainer>
          </ChartWrapper>
        </div>
      </Card>

      {/* TOOLBAR */}
      <div className="flex flex-col lg:flex-row gap-4 justify-between items-start lg:items-center p-4 bg-slate-900/60 border border-slate-700/50 rounded-2xl">
        <div className="relative w-full lg:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search records..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
          />
        </div>
        <div className="flex gap-4 w-full lg:w-auto">
          <div className="relative flex-1 lg:w-48">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <select 
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 appearance-none"
            >
              <option value="all">All Readings</option>
              {Object.keys(VITAL_TYPES).map(k => (
                <option key={k} value={k}>{VITAL_TYPES[k].label}</option>
              ))}
            </select>
          </div>
          <div className="relative flex-1 lg:w-40">
            <ArrowUpDown className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <select 
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 appearance-none"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
            </select>
          </div>
        </div>
      </div>

      {/* TIMELINE */}
      <div className="space-y-8">
        {Object.keys(groupedData).length === 0 ? (
          <div className="text-center py-10 text-slate-500 italic">No matching records found.</div>
        ) : (
          Object.keys(groupedData).map(dateKey => (
            <div key={dateKey} className="space-y-4">
              <h4 className="text-slate-400 font-bold uppercase tracking-widest text-sm border-b border-slate-800 pb-2">
                {dateKey}
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {groupedData[dateKey].map(record => {
                  const meta = VITAL_TYPES[record.vital_type] || { icon: Activity, label: record.vital_type, color: 'text-slate-400', bg: 'bg-slate-700' };
                  const Icon = meta.icon;
                  return (
                    <motion.div 
                      key={record.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-slate-800/40 border border-slate-700/50 p-4 rounded-2xl flex items-center justify-between hover:bg-slate-800/60 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl ${meta.bg} ${meta.color}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h5 className="text-white font-medium">{meta.label}</h5>
                            <span className="text-xs text-slate-500">• {record.time}</span>
                          </div>
                          <div className="flex items-baseline gap-2">
                            <span className="text-xl font-bold text-slate-200">{record.value}</span>
                            <span className="text-sm text-slate-400">{record.unit}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4">
                        <StatusBadge status={record.status || 'Normal'} />
                        <RecordActions onEdit={onEdit} onDelete={onDelete} record={record} />
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
