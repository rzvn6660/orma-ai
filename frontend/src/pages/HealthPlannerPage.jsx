import { useState, useEffect } from 'react';
import { 
  Calendar, Clock, CheckCircle2, AlertTriangle, Activity, Phone, MapPin, Edit3, Trash2, 
  Plus, MoreVertical, Droplet, Moon, HeartPulse, Stethoscope, Syringe, ClipboardList
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { healthPlannerApi } from '../services/api';

const EVENT_ICONS = {
  medicine: ClipboardList,
  doctor_appointment: Stethoscope,
  blood_test: Droplet,
  vaccination: Syringe,
  blood_pressure_check: HeartPulse,
  blood_sugar_check: Activity,
  exercise: Activity,
  water_reminder: Droplet,
  sleep_reminder: Moon,
  custom_reminder: Calendar
};

export default function HealthPlannerPage({ user }) {
  const [events, setEvents] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeMenu, setActiveMenu] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    event_type: 'medicine',
    title: '',
    description: '',
    reminder_time: '',
    event_date: '',
    notes: '',
    location: '',
    contact_number: '',
    priority: 'normal'
  });

  const fetchEvents = async () => {
    try {
      const data = await healthPlannerApi.getEvents();
      setEvents(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchEvents();
    const handleUpdates = () => fetchEvents();
    window.addEventListener('orma:plannerUpdated', handleUpdates);
    return () => window.removeEventListener('orma:plannerUpdated', handleUpdates);
  }, []);

  const handleMarkCompleted = async (id) => {
    try {
      await healthPlannerApi.completeEvent(id);
      fetchEvents();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this event?")) return;
    try {
      await healthPlannerApi.deleteEvent(id);
      fetchEvents();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveEvent = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await healthPlannerApi.createEvent({
        ...formData,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      });
      setShowAddForm(false);
      setFormData({
        event_type: 'medicine', title: '', description: '', reminder_time: '', 
        event_date: '', notes: '', location: '', contact_number: '', priority: 'normal'
      });
      fetchEvents();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getEventIcon = (type) => {
    const Icon = EVENT_ICONS[type] || Calendar;
    return <Icon className="w-6 h-6" />;
  };

  const todayStr = new Date().toISOString().split('T')[0];

  const todayEvents = events.filter(e => (!e.event_date || e.event_date === todayStr) && !e.status);
  const upcomingEvents = events.filter(e => e.event_date && e.event_date > todayStr && !e.status);
  const completedEvents = events.filter(e => e.status);

  const renderEventCard = (event) => {
    let completedTimeStr = "--:--";
    if (event.status && event.completed_at) {
       const d = new Date(event.completed_at + "Z");
       completedTimeStr = d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
    
    return (
      <div key={event.id} className={`p-5 border rounded-2xl transition-all flex flex-col ${event.status ? 'bg-emerald-900/10 border-emerald-500/20' : 'bg-slate-800/40 border-slate-700/50'}`}>
        <div className="flex items-start gap-4 mb-4">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${event.status ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'}`}>
            {getEventIcon(event.event_type)}
          </div>
          <div className="flex-1">
            <div className="flex justify-between items-start">
              <h3 className={`text-xl font-bold ${event.status ? 'text-emerald-300' : 'text-white'}`}>{event.title}</h3>
              <div className="flex items-center gap-2">
                {event.priority === 'high' && <span className="px-2 py-1 bg-red-500/20 text-red-400 text-xs font-bold rounded-md">High Priority</span>}
                {event.status ? (
                  <span className="text-xs font-bold px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded-md">Completed at {completedTimeStr}</span>
                ) : (
                  <span className="text-xs font-bold px-2 py-1 bg-amber-500/20 text-amber-400 rounded-md">Pending</span>
                )}
                
                <div className="relative">
                  <button onClick={() => setActiveMenu(activeMenu === event.id ? null : event.id)} className="p-1 text-slate-400 hover:text-white rounded-full">
                    <MoreVertical className="w-5 h-5" />
                  </button>
                  {activeMenu === event.id && (
                      <div className="absolute right-0 mt-2 w-48 bg-slate-800 rounded-xl border border-slate-700 shadow-xl overflow-hidden z-10">
                        <button onClick={() => handleDelete(event.id)} className="w-full text-left px-4 py-3 text-sm text-red-400 hover:bg-slate-700 transition-colors">
                          Delete Event
                        </button>
                      </div>
                  )}
                </div>
              </div>
            </div>
            
            <p className="text-slate-400 text-sm mt-1">{event.description}</p>
            
            <div className="grid grid-cols-2 gap-x-4 gap-y-2 mt-3 bg-slate-900/50 p-3 rounded-lg border border-slate-700/30">
              <div>
                <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-0.5">Time</p>
                <p className="text-sm text-slate-300 font-medium">{event.reminder_time}</p>
              </div>
              {event.event_date && (
                <div>
                  <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-0.5">Date</p>
                  <p className="text-sm text-slate-300 font-medium">{event.event_date}</p>
                </div>
              )}
            </div>

            {(event.location || event.contact_number) && (
              <div className="flex flex-wrap gap-2 mt-3">
                {event.location && (
                  <button className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800/80 hover:bg-slate-700/80 rounded-md border border-slate-700 text-sm text-slate-300 transition-colors">
                    <MapPin className="w-4 h-4 text-blue-400" /> Open Maps ({event.location})
                  </button>
                )}
                {event.contact_number && (
                  <button className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 rounded-md border border-emerald-500/20 text-sm text-emerald-400 transition-colors">
                    <Phone className="w-4 h-4" /> Call {event.contact_number}
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
        
        {!event.status && (
          <div className="flex items-center gap-2 mt-auto pt-2 border-t border-slate-700/30">
            <button onClick={() => handleMarkCompleted(event.id)} className="px-4 py-2 bg-emerald-500/10 text-emerald-400 font-medium rounded-lg hover:bg-emerald-500/20 transition-colors flex items-center gap-2 mt-2 w-full justify-center">
              <CheckCircle2 className="w-4 h-4" /> Mark Completed
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-full max-w-7xl mx-auto flex flex-col gap-8 pb-10 relative">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Planner</h1>
          <p className="text-slate-400">Manage your medicines, appointments, and wellness routines in one place.</p>
        </div>
        <button onClick={() => setShowAddForm(true)} className="orma-btn-primary">
          <Plus className="w-5 h-5" /> Add Health Event
        </button>
      </div>

      {!showAddForm ? (
        <div className="space-y-10">
          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2"><Clock className="text-amber-400" /> Today's Plan</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {todayEvents.map(renderEventCard)}
              {todayEvents.length === 0 && <p className="text-slate-500 col-span-full">No events pending for today.</p>}
            </div>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2"><Calendar className="text-blue-400" /> Upcoming Events</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {upcomingEvents.map(renderEventCard)}
              {upcomingEvents.length === 0 && <p className="text-slate-500 col-span-full">No upcoming events scheduled.</p>}
            </div>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2"><CheckCircle2 className="text-emerald-400" /> Completed</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {completedEvents.map(renderEventCard)}
              {completedEvents.length === 0 && <p className="text-slate-500 col-span-full">No completed events yet.</p>}
            </div>
          </section>
        </div>
      ) : (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="orma-card p-6 md:p-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">Add New Health Event</h2>
            <button onClick={() => setShowAddForm(false)} className="text-slate-400 hover:text-white">Cancel</button>
          </div>
          <form onSubmit={handleSaveEvent} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400">Event Type</label>
                <select value={formData.event_type} onChange={(e) => setFormData({...formData, event_type: e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500">
                  <option value="medicine">Medicine</option>
                  <option value="doctor_appointment">Doctor Appointment</option>
                  <option value="blood_test">Blood Test</option>
                  <option value="vaccination">Vaccination</option>
                  <option value="blood_pressure_check">Blood Pressure Check</option>
                  <option value="blood_sugar_check">Blood Sugar Check</option>
                  <option value="exercise">Exercise</option>
                  <option value="water_reminder">Water Reminder</option>
                  <option value="sleep_reminder">Sleep Reminder</option>
                  <option value="custom_reminder">Custom Event</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400">Priority</label>
                <select value={formData.priority} onChange={(e) => setFormData({...formData, priority: e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500">
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-400">Title (e.g. Dr. Smith / Paracetamol)</label>
              <input required value={formData.title} onChange={(e) => setFormData({...formData, title: e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400">Time *</label>
                <input required type="time" value={formData.reminder_time} onChange={(e) => {
                  let [hr, min] = e.target.value.split(':');
                  let suffix = hr >= 12 ? 'PM' : 'AM';
                  let hr12 = hr % 12 || 12;
                  setFormData({...formData, reminder_time: `${String(hr12).padStart(2,'0')}:${min} ${suffix}`});
                }} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500" />
                <p className="text-xs text-slate-500">Current selection: {formData.reminder_time}</p>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400">Date (Leave empty for daily)</label>
                <input type="date" value={formData.event_date} onChange={(e) => setFormData({...formData, event_date: e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500" />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400">Location (Hospital / Clinic)</label>
                <input value={formData.location} onChange={(e) => setFormData({...formData, location: e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-slate-400">Contact Number</label>
                <input type="tel" value={formData.contact_number} onChange={(e) => setFormData({...formData, contact_number: e.target.value})} className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500" />
              </div>
            </div>

            <button type="submit" disabled={loading} className="w-full orma-btn-primary py-4 text-lg">
              {loading ? "Saving..." : "Save Health Event"}
            </button>
          </form>
        </motion.div>
      )}
    </div>
  );
}
