import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Mic, Upload, Edit3, Pill, CheckCircle2, AlertTriangle, AlertCircle, Loader2 } from 'lucide-react';
import { medicineApi, speechApi } from '../services/api';

export default function AddMedicineModal({ isOpen, onClose, onAdded }) {
  const [mode, setMode] = useState('select'); // select, manual, voice, ocr, verify
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recording, setRecording] = useState(false);
  
  const [formData, setFormData] = useState({
    medicine_name: '',
    dosage: '',
    timing: '08:00 AM',
    purpose: '',
    frequency: '',
    notes: '',
    suggestion: null,
    confidence: 100
  });

  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const resetState = () => {
    setMode('select');
    setFormData({
      medicine_name: '', dosage: '', timing: '08:00 AM', purpose: '', frequency: '', notes: '', suggestion: null, confidence: 100
    });
    setError(null);
    setLoading(false);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await medicineApi.createReminder({
        medicine_name: formData.medicine_name,
        dosage: formData.dosage,
        reminder_time: formData.timing,
        purpose: formData.purpose,
        frequency: formData.frequency,
        notes: formData.notes
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
      // 1. Transcribe
      const transResult = await speechApi.transcribe(audioBlob, 'en');
      const text = transResult.transcription;
      if (!text) throw new Error("Could not transcribe voice.");
      
      // 2. Parse
      const parseResult = await medicineApi.parseVoice(text);
      if (parseResult.status === 'success') {
        const { data } = parseResult;
        setFormData(prev => ({
          ...prev,
          medicine_name: data.medicine_name || '',
          dosage: data.dosage || '',
          timing: data.timing || '',
          purpose: data.purpose || '',
          frequency: data.frequency || '',
          notes: data.notes || '',
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

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setLoading(true);
    setError(null);
    setMode('ocr');
    
    try {
      const parseResult = await medicineApi.parseOcr(file);
      if (parseResult.status === 'success') {
        const { data } = parseResult;
        setFormData(prev => ({
          ...prev,
          medicine_name: data.medicine_name || '',
          dosage: data.dosage || '',
          timing: data.timing || '',
          purpose: data.purpose || '',
          frequency: data.frequency || '',
          notes: data.notes || '',
          suggestion: data.suggestion,
          confidence: data.confidence
        }));
        setMode('verify');
      } else {
        throw new Error("Failed to extract data from image.");
      }
    } catch (err) {
      setError(err.message || "OCR processing failed.");
      setMode('select');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-md"
      >
        <motion.div 
          initial={{ scale: 0.95, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.95, y: 20 }}
          className="bg-slate-800 border border-slate-700/50 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl relative flex flex-col max-h-[90vh]"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-slate-700/50 shrink-0">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Pill className="text-blue-400 w-6 h-6" />
              {mode === 'select' && "How would you like to add medicines?"}
              {mode === 'manual' && "Manual Entry"}
              {mode === 'voice' && "Voice Entry"}
              {mode === 'ocr' && "Processing Prescription"}
              {mode === 'verify' && "Human Verification"}
            </h2>
            <button onClick={handleClose} className="text-slate-400 hover:text-white transition-colors bg-slate-700/30 p-2 rounded-full">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="p-6 overflow-y-auto">
            {error && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            {/* Mode: Selection */}
            {mode === 'select' && (
              <div className="grid gap-4">
                <button 
                  onClick={() => setMode('manual')}
                  className="flex flex-col items-center gap-3 p-6 bg-slate-700/30 hover:bg-slate-700/60 border border-slate-600/50 rounded-2xl transition-all"
                >
                  <div className="w-16 h-16 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 mb-2">
                    <Edit3 className="w-8 h-8" />
                  </div>
                  <h3 className="text-lg font-bold text-white">Manual Entry</h3>
                  <p className="text-sm text-slate-400 text-center">Type in medicine details directly.</p>
                </button>

                <button 
                  onClick={() => setMode('voice')}
                  className="flex flex-col items-center gap-3 p-6 bg-slate-700/30 hover:bg-slate-700/60 border border-slate-600/50 rounded-2xl transition-all"
                >
                  <div className="w-16 h-16 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 mb-2">
                    <Mic className="w-8 h-8" />
                  </div>
                  <h3 className="text-lg font-bold text-white">Voice Input</h3>
                  <p className="text-sm text-slate-400 text-center">Speak the medicine details.</p>
                </button>

                <button 
                  onClick={() => fileInputRef.current?.click()}
                  className="flex flex-col items-center gap-3 p-6 bg-slate-700/30 hover:bg-slate-700/60 border border-slate-600/50 rounded-2xl transition-all"
                >
                  <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 mb-2">
                    <Upload className="w-8 h-8" />
                  </div>
                  <h3 className="text-lg font-bold text-white">Upload Prescription</h3>
                  <p className="text-sm text-slate-400 text-center">Extract details using OCR.</p>
                </button>
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  className="hidden" 
                  accept="image/*,.pdf" 
                  onChange={handleFileUpload} 
                />
              </div>
            )}

            {/* Mode: Voice Recording */}
            {mode === 'voice' && (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <p className="text-slate-300 mb-8 max-w-sm">
                  Say something like:<br/>"Add Amlodipine 10mg at 8 AM for Blood Pressure"
                </p>
                {loading ? (
                  <div className="flex flex-col items-center">
                    <Loader2 className="w-12 h-12 text-blue-400 animate-spin mb-4" />
                    <p className="text-blue-300 font-medium">Extracting details...</p>
                  </div>
                ) : (
                  <button 
                    onClick={recording ? stopVoiceRecording : startVoiceRecording}
                    className={`w-24 h-24 rounded-full flex items-center justify-center transition-all ${
                      recording 
                        ? 'bg-red-500 text-white shadow-[0_0_30px_rgba(239,68,68,0.5)] animate-pulse' 
                        : 'bg-purple-500 text-white hover:scale-105'
                    }`}
                  >
                    <Mic className="w-10 h-10" />
                  </button>
                )}
                <p className="mt-6 text-sm text-slate-400 font-medium h-6">
                  {recording ? "Recording... Tap to stop" : (!loading && "Tap to start speaking")}
                </p>
              </div>
            )}

            {/* Mode: OCR Loading */}
            {mode === 'ocr' && loading && (
               <div className="flex flex-col items-center justify-center py-16 text-center">
                 <Loader2 className="w-12 h-12 text-emerald-400 animate-spin mb-6" />
                 <h3 className="text-lg font-bold text-white mb-2">Scanning Prescription...</h3>
                 <p className="text-slate-400 text-sm max-w-xs">
                   AI is extracting medicine details using OCR. This may take a moment.
                 </p>
               </div>
            )}

            {/* Mode: Verification or Manual Form */}
            {(mode === 'verify' || mode === 'manual') && (
              <form id="medicine-form" onSubmit={handleSubmit} className="space-y-4">
                {mode === 'verify' && (
                  <div className="mb-6">
                    <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl mb-4">
                      <h4 className="text-sm font-bold text-blue-400 mb-1 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4" />
                        AI-assisted prescription digitization
                      </h4>
                      <p className="text-xs text-blue-200">
                        Please verify the extracted information below before saving. AI does not replace a doctor.
                      </p>
                    </div>

                    {formData.suggestion && (
                      <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-amber-200">AI Correction Suggestion</p>
                          <p className="text-xs text-amber-400/80 mt-1">{formData.suggestion}</p>
                          <p className="text-xs text-amber-400/60 mt-1">Confidence Score: {formData.confidence}%</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-400">Medicine Name *</label>
                    <input 
                      required
                      name="medicine_name"
                      value={formData.medicine_name}
                      onChange={handleInputChange}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all outline-none"
                      placeholder="e.g. Amlodipine"
                    />
                  </div>
                  
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-400">Dosage</label>
                    <input 
                      name="dosage"
                      value={formData.dosage}
                      onChange={handleInputChange}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all outline-none"
                      placeholder="e.g. 10mg"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-400">Timing *</label>
                    <input 
                      required
                      name="timing"
                      value={formData.timing}
                      onChange={handleInputChange}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all outline-none"
                      placeholder="e.g. 08:00 AM"
                    />
                  </div>
                  
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-400">Frequency</label>
                    <input 
                      name="frequency"
                      value={formData.frequency}
                      onChange={handleInputChange}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all outline-none"
                      placeholder="e.g. Once daily"
                    />
                  </div>

                  <div className="space-y-1 md:col-span-2">
                    <label className="text-xs font-medium text-slate-400">Purpose</label>
                    <input 
                      name="purpose"
                      value={formData.purpose}
                      onChange={handleInputChange}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all outline-none"
                      placeholder="e.g. Blood Pressure"
                    />
                  </div>

                  <div className="space-y-1 md:col-span-2">
                    <label className="text-xs font-medium text-slate-400">Notes</label>
                    <textarea 
                      name="notes"
                      value={formData.notes}
                      onChange={handleInputChange}
                      className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all outline-none resize-none h-24"
                      placeholder="e.g. Take after food"
                    />
                  </div>
                </div>
              </form>
            )}
          </div>

          {/* Footer Actions */}
          <div className="p-6 border-t border-slate-700/50 shrink-0 flex gap-3">
            {mode !== 'select' && !loading && (
              <button 
                onClick={() => setMode('select')}
                className="px-6 py-3 rounded-xl font-bold text-slate-300 hover:text-white bg-slate-700/50 hover:bg-slate-700 transition-colors"
              >
                Back
              </button>
            )}
            <div className="flex-1"></div>
            {(mode === 'manual' || mode === 'verify') && (
              <button 
                form="medicine-form"
                type="submit"
                disabled={loading}
                className="px-8 py-3 rounded-xl font-bold text-white bg-blue-600 hover:bg-blue-500 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {mode === 'verify' ? "Confirm & Save" : "Save Medicine"}
              </button>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
