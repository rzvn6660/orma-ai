import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Mic, Upload, Edit3, Pill, CheckCircle2, AlertTriangle, AlertCircle, Loader2, ArrowLeft, ArrowRight, ShieldCheck, Lock } from 'lucide-react';
import { medicineApi, speechApi } from '../services/api';
import ReminderTimePicker from './ReminderTimePicker';
import MedicineUploadDropzone from './ui/MedicineUploadDropzone';

export default function AddMedicineModal({ isOpen, onClose, onAdded }) {
  const [mode, setMode] = useState('select'); // select, manual, voice, ocr, verify
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recording, setRecording] = useState(false);
  
  const [formData, setFormData] = useState({
    medicine_name: '',
    dosage: '',
    timings: ['08:00 AM'],
    frequency: 'Once Daily',
    purpose: '',
    suggestion: null,
    confidence: 100
  });

  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Reset when opened
  useEffect(() => {
    if (isOpen) {
      setMode('select');
      setFormData({ medicine_name: '', dosage: '', timings: ['08:00 AM'], frequency: 'Once Daily', purpose: '', suggestion: null, confidence: 100 });
      setError(null);
      setLoading(false);
    }
  }, [isOpen]);

  const handleClose = () => {
    onClose();
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFrequencyChange = (newFreq) => {
    let newTimings = ['08:00 AM'];
    if (newFreq === 'Twice Daily') {
      newTimings = ['08:00 AM', '08:00 PM'];
    } else if (newFreq === 'Three Times Daily' || newFreq === 'Thrice Daily') {
      newTimings = ['08:00 AM', '02:00 PM', '08:00 PM'];
    } else if (newFreq === 'SOS (As Needed)') {
      newTimings = [];
    }
    setFormData(prev => ({ ...prev, frequency: newFreq, timings: newTimings }));
  };

  const handleSubmit = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (formData.frequency !== 'SOS (As Needed)') {
        if (!formData.timings || formData.timings.length === 0 || formData.timings.some(t => !t)) {
          setError("Please select valid reminder times.");
          setLoading(false);
          return;
        }
        if (new Set(formData.timings).size !== formData.timings.length) {
          setError("Duplicate reminder times detected. Please select a unique time for each dose.");
          setLoading(false);
          return;
        }
      }

      const finalTimings = formData.frequency === 'SOS (As Needed)' ? '' : formData.timings.join(', ');

      await medicineApi.createReminder({
        medicine_name: formData.medicine_name,
        dosage: formData.dosage,
        reminder_time: finalTimings,
        frequency: formData.frequency,
        purpose: formData.purpose,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      });
      onAdded();
      handleClose();
    } catch (err) {
      setError("Failed to save medicine.");
    } finally {
      setLoading(false);
    }
  };

  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };
      
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processVoiceInput(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start();
      setRecording(true);
    } catch (err) {
      setError("Could not access microphone.");
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const processVoiceInput = async (audioBlob) => {
    setLoading(true);
    setError(null);
    try {
      const transResult = await speechApi.transcribe(audioBlob, 'en');
      const text = transResult.transcription;
      if (!text) throw new Error("Could not transcribe voice.");
      
      const parseResult = await medicineApi.parseVoice(text);
      if (parseResult.status === 'success') {
        const { data } = parseResult;
        let timings = data.timing ? data.timing.split(',').map(t => t.trim()) : ['08:00 AM'];
        let freq = data.frequency || 'Once Daily';
        setFormData(prev => ({
          ...prev,
          medicine_name: data.medicine_name || '',
          dosage: data.dosage || '',
          timings: timings,
          frequency: freq,
          purpose: data.purpose || '',
          suggestion: data.suggestion,
          confidence: data.confidence
        }));
        setMode('verify');
      } else {
        throw new Error("Failed to parse medicine from voice.");
      }
    } catch (err) {
      setError(err.message || "Voice processing failed.");
      setMode('select');
    } finally {
      setLoading(false);
    }
  };

  const handleDirectFileSelected = async (file) => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const parseResult = await medicineApi.parseOcr(file);
      if (parseResult.status === 'success') {
        const { data } = parseResult;
        setFormData(prev => ({
          ...prev,
          medicine_name: data.medicine_name || '',
          dosage: data.dosage || '',
          timings: data.timing ? [data.timing] : prev.timings,
          purpose: data.purpose || '',
          suggestion: data.suggestion,
          confidence: data.confidence || 100
        }));
        setMode('verify');
      } else {
        throw new Error("Failed to extract data from image.");
      }
    } catch (err) {
      setError(err.message || "OCR processing failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleDirectFileSelected(file);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 lg:p-10 bg-slate-950/90 backdrop-blur-xl overflow-y-auto"
      >
        <motion.div 
          initial={{ scale: 0.95, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.95, opacity: 0, y: 20 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className={`bg-slate-900 border border-slate-700/50 rounded-[2rem] shadow-[0_0_80px_rgba(0,0,0,0.8)] flex flex-col relative w-full ${mode === 'select' ? 'max-w-6xl' : 'max-w-2xl'} min-h-[500px] my-auto`}
        >
          
          {/* Close Button (Absolute for Select mode) */}
          {mode === 'select' && (
            <button onClick={handleClose} className="absolute top-6 right-6 text-slate-400 hover:text-white transition-colors bg-slate-800/50 hover:bg-slate-700 p-3 rounded-full z-20">
              <X className="w-6 h-6" />
            </button>
          )}

          {/* Header for Inner Forms */}
          {mode !== 'select' && (
            <div className="flex items-center justify-between p-6 md:p-8 border-b border-slate-800 shrink-0 bg-slate-900 rounded-t-[2rem] z-10">
              <div className="flex items-center gap-4">
                <button 
                  onClick={() => setMode('select')}
                  className="p-3 bg-slate-800 hover:bg-slate-700 rounded-full transition-colors text-slate-300 flex-shrink-0"
                >
                  <ArrowLeft className="w-6 h-6" />
                </button>
                <h2 className="text-2xl sm:text-3xl font-extrabold text-white truncate">
                  {mode === 'manual' && "Type Medicine"}
                  {mode === 'voice' && "Voice Entry"}
                  {mode === 'ocr' && "Scan Prescription"}
                  {mode === 'verify' && "Verify Details"}
                </h2>
              </div>
              <button onClick={handleClose} className="text-slate-400 hover:text-white transition-colors bg-slate-800 hover:bg-slate-700 p-3 rounded-full flex-shrink-0 ml-4">
                <X className="w-6 h-6" />
              </button>
            </div>
          )}

          <div className="flex-1 flex flex-col items-center p-6 md:p-10 lg:p-12 overflow-y-auto overflow-x-hidden w-full">
            
            {error && (
              <div className="w-full max-w-2xl mb-8 p-5 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 flex items-center gap-4 shrink-0">
                <AlertCircle className="w-8 h-8 shrink-0" />
                <p className="text-lg font-medium">{error}</p>
              </div>
            )}

            {/* STEP 1: Massive Premium Selection Mode */}
            {mode === 'select' && (
              <div className="w-full flex flex-col items-center max-w-5xl mx-auto">
                
                {/* Header Titles */}
                <div className="text-center mb-12">
                  <div className="w-20 h-20 bg-slate-800 border border-slate-700 rounded-full flex items-center justify-center mx-auto mb-6 shadow-xl relative group">
                    <div className="absolute inset-0 bg-blue-500/20 rounded-full blur-xl group-hover:bg-blue-500/30 transition-all"></div>
                    <Pill className="w-10 h-10 text-blue-400 relative z-10" />
                  </div>
                  <h1 className="text-4xl md:text-5xl font-extrabold text-white mb-4 tracking-tight">Add Medicine</h1>
                  <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto">
                    Choose the easiest way to add your medicine. We'll help you stay on track.
                  </p>
                </div>

                {/* The 3 Big Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full mb-10">
                  
                  {/* Card 1: Type */}
                  <button 
                    onClick={() => setMode('manual')}
                    className="flex flex-col items-center text-center p-8 lg:p-10 bg-slate-800/40 hover:bg-slate-800/80 border border-slate-700/50 hover:border-blue-500/50 rounded-3xl transition-all duration-300 group min-h-[280px]"
                  >
                    <div className="w-20 h-20 rounded-full bg-blue-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform relative">
                      <div className="absolute inset-0 bg-blue-500/20 rounded-full blur-lg group-hover:blur-xl transition-all"></div>
                      <Edit3 className="w-8 h-8 text-blue-400 relative z-10" />
                    </div>
                    <h3 className="text-2xl font-bold text-white mb-3">Type Medicine</h3>
                    <p className="text-base text-slate-400 mb-8 leading-relaxed flex-1">
                      Manually enter medicine details like name, dosage and time.
                    </p>
                    <div className="w-12 h-12 rounded-full bg-slate-800 group-hover:bg-blue-600 flex items-center justify-center transition-colors">
                      <ArrowRight className="w-6 h-6 text-slate-400 group-hover:text-white" />
                    </div>
                  </button>

                  {/* Card 2: Voice */}
                  <button 
                    onClick={() => setMode('voice')}
                    className="flex flex-col items-center text-center p-8 lg:p-10 bg-slate-800/40 hover:bg-slate-800/80 border border-slate-700/50 hover:border-emerald-500/50 rounded-3xl transition-all duration-300 group min-h-[280px]"
                  >
                    <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform relative">
                      <div className="absolute inset-0 bg-emerald-500/20 rounded-full blur-lg group-hover:blur-xl transition-all"></div>
                      <Mic className="w-8 h-8 text-emerald-400 relative z-10" />
                    </div>
                    <h3 className="text-2xl font-bold text-white mb-3">Voice Entry</h3>
                    <p className="text-base text-slate-400 mb-8 leading-relaxed flex-1">
                      Speak medicine name, dosage and time. We'll save it for you.
                    </p>
                    <div className="w-12 h-12 rounded-full bg-slate-800 group-hover:bg-emerald-600 flex items-center justify-center transition-colors">
                      <ArrowRight className="w-6 h-6 text-slate-400 group-hover:text-white" />
                    </div>
                  </button>

                  {/* Card 3: Scan */}
                  <button 
                    onClick={() => setMode('ocr')}
                    className="flex flex-col items-center text-center p-8 lg:p-10 bg-slate-800/40 hover:bg-slate-800/80 border border-slate-700/50 hover:border-purple-500/50 rounded-3xl transition-all duration-300 group min-h-[280px] cursor-pointer"
                  >
                    <div className="w-20 h-20 rounded-full bg-purple-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform relative">
                      <div className="absolute inset-0 bg-purple-500/20 rounded-full blur-lg group-hover:blur-xl transition-all"></div>
                      <Upload className="w-8 h-8 text-purple-400 relative z-10" />
                    </div>
                    <h3 className="text-2xl font-bold text-white mb-3">Scan Prescription</h3>
                    <p className="text-base text-slate-400 mb-8 leading-relaxed flex-1">
                      Upload or scan your prescription and we'll extract the medicine details.
                    </p>
                    <div className="w-12 h-12 rounded-full bg-slate-800 group-hover:bg-purple-600 flex items-center justify-center transition-colors">
                      <ArrowRight className="w-6 h-6 text-slate-400 group-hover:text-white" />
                    </div>
                  </button>
                </div>

                {/* Trust Badge */}
                <div className="orma-card">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-slate-700 flex items-center justify-center shrink-0">
                      <ShieldCheck className="w-6 h-6 text-slate-300" />
                    </div>
                    <div className="text-left">
                      <h4 className="text-lg font-bold text-white">Your Information is Safe</h4>
                      <p className="text-sm text-slate-400">All medicine data is encrypted and stored securely.</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-emerald-400 bg-emerald-400/10 px-4 py-2 rounded-lg shrink-0">
                    <Lock className="w-4 h-4" />
                    <span className="text-sm font-bold">100% Secure</span>
                  </div>
                </div>

                {/* Cancel Link */}
                <button onClick={handleClose} className="text-slate-400 hover:text-white text-lg font-medium transition-colors cursor-pointer">
                  Cancel
                </button>

              </div>
            )}

            {/* Content Area for other modes */}
            {mode !== 'select' && (
              <div className="flex flex-col justify-center w-full max-w-2xl">
                
                {/* Voice Mode */}
                {mode === 'voice' && (
                  <div className="flex flex-col items-center text-center py-12">
                    {loading ? (
                      <>
                        <Loader2 className="w-16 h-16 text-emerald-400 animate-spin mb-6" />
                        <p className="text-2xl text-white font-medium">Extracting details...</p>
                      </>
                    ) : (
                      <>
                        <button 
                          onClick={recording ? stopVoiceRecording : startVoiceRecording}
                          className={`w-40 h-40 rounded-[3rem] flex items-center justify-center transition-all shadow-2xl shrink-0 cursor-pointer ${
                            recording 
                              ? 'bg-red-500 text-white shadow-[0_0_50px_rgba(239,68,68,0.6)] animate-pulse scale-105' 
                              : 'bg-emerald-600 text-white hover:bg-emerald-500 hover:scale-105'
                          }`}
                        >
                          <Mic className="w-20 h-20" />
                        </button>
                        <p className="mt-10 text-2xl text-white font-bold px-4">
                          {recording ? "Recording... Tap to stop" : "Tap the microphone"}
                        </p>
                        <p className="mt-4 text-xl text-slate-400 px-4">
                          Say: "Add Amlodipine 10mg at 8 AM"
                        </p>
                      </>
                    )}
                  </div>
                )}

                {/* OCR Mode with Polished Dropzone */}
                {mode === 'ocr' && (
                  <div className="py-6 px-2">
                    <MedicineUploadDropzone 
                      onFileSelected={handleDirectFileSelected} 
                      isLoading={loading} 
                    />
                    <div className="mt-6 text-center">
                      <button 
                        type="button"
                        onClick={() => setMode('select')}
                        className="text-slate-400 hover:text-white text-sm font-bold transition-colors inline-flex items-center gap-1.5 cursor-pointer"
                      >
                        <ArrowLeft className="w-4 h-4" /> Choose Different Entry Method
                      </button>
                    </div>
                  </div>
                )}

                {/* Manual / Verify Form */}
                {(mode === 'manual' || mode === 'verify') && (
                  <form id="medicine-form" onSubmit={handleSubmit} className="flex flex-col gap-5 sm:gap-6 pb-4 w-full">
                    {mode === 'verify' && formData.suggestion && (
                      <div className="p-5 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex flex-col sm:flex-row items-start gap-4 shrink-0">
                        <AlertTriangle className="w-8 h-8 text-amber-400 shrink-0" />
                        <div>
                          <p className="text-lg font-bold text-amber-300">AI Correction Suggestion</p>
                          <p className="text-base text-amber-200/90 mt-1">{formData.suggestion}</p>
                        </div>
                      </div>
                    )}

                    <div className="space-y-3 shrink-0">
                      <label className="text-lg font-bold text-slate-300 ml-2">Medicine Name</label>
                      <input 
                        required
                        name="medicine_name"
                        value={formData.medicine_name}
                        onChange={handleInputChange}
                        className="w-full bg-slate-950 border-2 border-slate-700 rounded-2xl px-5 sm:px-6 py-4 sm:py-5 text-xl text-white font-medium focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all outline-none"
                        placeholder="e.g. Amlodipine"
                      />
                    </div>
                    
                    <div className="space-y-3 shrink-0">
                      <label className="text-lg font-bold text-slate-300 ml-2">Dosage</label>
                      <input 
                        name="dosage"
                        value={formData.dosage}
                        onChange={handleInputChange}
                        className="w-full bg-slate-950 border-2 border-slate-700 rounded-2xl px-5 sm:px-6 py-4 sm:py-5 text-xl text-white font-medium focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all outline-none"
                        placeholder="e.g. 10mg"
                      />
                    </div>

                    <div className="space-y-3 shrink-0">
                      <label className="text-lg font-bold text-slate-300 ml-2">Frequency</label>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                        {[
                          { label: 'Once Daily', detail: '1 time per day', value: 'Once Daily' },
                          { label: 'Twice Daily', detail: '2 times per day', value: 'Twice Daily' },
                          { label: 'Three Times Daily', detail: '3 times per day', value: 'Three Times Daily' },
                          { label: 'SOS', detail: 'As needed only', value: 'SOS (As Needed)' },
                          { label: 'Custom', detail: 'Flexible times', value: 'Custom' },
                        ].map((item) => {
                          const isSelected = (formData.frequency || 'Once Daily') === item.value;
                          return (
                            <button
                              key={item.value}
                              type="button"
                              onClick={() => handleFrequencyChange(item.value)}
                              className={`p-3.5 rounded-2xl border-2 text-left transition-all cursor-pointer flex flex-col justify-center ${
                                isSelected
                                  ? 'bg-blue-600/30 border-blue-400 text-white shadow-lg shadow-blue-600/20 ring-2 ring-blue-400/30 scale-[1.02]'
                                  : 'bg-slate-950/80 border-slate-700/80 text-slate-300 hover:bg-slate-800 hover:border-slate-600 hover:text-white'
                              }`}
                            >
                              <span className="font-extrabold text-base leading-tight">{item.label}</span>
                              <span className={`text-xs font-semibold mt-1 ${isSelected ? 'text-blue-300' : 'text-slate-400'}`}>
                                {item.detail}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {formData.frequency !== 'SOS (As Needed)' && (
                      <div className="space-y-3 shrink-0">
                        <ReminderTimePicker
                          timings={formData.timings || ['08:00 AM']}
                          onChange={(newTimings) => setFormData(prev => ({ ...prev, timings: newTimings }))}
                          frequency={formData.frequency || 'Once Daily'}
                          isCustom={formData.frequency === 'Custom'}
                        />
                      </div>
                    )}

                    <div className="space-y-3 shrink-0">
                      <label className="text-lg font-bold text-slate-300 ml-2">Purpose (Optional)</label>
                      <input 
                        name="purpose"
                        value={formData.purpose}
                        onChange={handleInputChange}
                        className="w-full bg-slate-950 border-2 border-slate-700 rounded-2xl px-5 sm:px-6 py-4 sm:py-5 text-xl text-white font-medium focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all outline-none"
                        placeholder="e.g. Blood Pressure"
                      />
                    </div>
                    
                    <button 
                      type="submit"
                      disabled={loading}
                      className="orma-btn-primary"
                    >
                      {loading && <Loader2 className="w-8 h-8 animate-spin" />}
                      {mode === 'verify' ? "Confirm & Save" : "Save Medicine"}
                    </button>
                  </form>
                )}
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
