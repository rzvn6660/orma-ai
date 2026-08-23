import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Camera, 
  Upload, 
  Image as ImageIcon, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  X 
} from 'lucide-react';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg', 'application/pdf'];
const MAX_SIZE_MB = 10;

export default function MedicineUploadDropzone({
  onFileSelected,
  isLoading = false,
  loadingMessage = 'Scanning medicine package with AI OCR...',
  className = ''
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const validateAndProcessFile = (file) => {
    if (!file) return;
    setError(null);

    // Validate type
    if (!ALLOWED_TYPES.includes(file.type) && !file.name.match(/\.(jpg|jpeg|png|webp|pdf)$/i)) {
      setError('Unsupported file type. Please upload a JPG, PNG, or WEBP image.');
      return;
    }

    // Validate size (10 MB max)
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`Image size exceeds ${MAX_SIZE_MB}MB limit.`);
      return;
    }

    setSelectedFile(file);

    // Generate local preview if image
    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }

    if (onFileSelected) {
      onFileSelected(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  return (
    <div className={`w-full ${className}`} aria-label="Medicine Package OCR Upload">
      {/* Dropzone Container */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`relative border-2 border-dashed rounded-3xl p-6 sm:p-8 text-center transition-all ${
          isDragOver
            ? 'border-blue-500 bg-blue-500/10 shadow-lg shadow-blue-500/10'
            : selectedFile
            ? 'border-emerald-500/40 bg-slate-950/60'
            : 'border-white/15 bg-slate-950/40 hover:border-white/25 hover:bg-slate-900/50'
        }`}
      >
        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-slate-950/90 backdrop-blur-md rounded-3xl z-20 flex flex-col items-center justify-center p-6 text-center">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/20 text-blue-400 flex items-center justify-center mb-3 animate-spin">
              <RefreshCw className="w-6 h-6" />
            </div>
            <h4 className="text-base font-bold text-white mb-1">Analyzing Medicine Label</h4>
            <p className="text-xs text-slate-400 max-w-xs">{loadingMessage}</p>
          </div>
        )}

        {/* File Preview or Upload Trigger */}
        {previewUrl ? (
          <div className="flex flex-col items-center">
            <div className="relative mb-3">
              <img
                src={previewUrl}
                alt="Prescription preview"
                className="w-32 h-32 object-cover rounded-2xl border border-white/20 shadow-md"
              />
              <button
                type="button"
                onClick={handleClear}
                className="absolute -top-2 -right-2 p-1.5 rounded-full bg-slate-800 hover:bg-slate-700 text-white border border-white/20 transition-colors shadow-lg cursor-pointer"
                title="Remove photo"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-xs font-bold text-emerald-400 mb-1 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Photo Selected
            </p>
            <p className="text-[11px] text-slate-400 font-mono">{selectedFile?.name}</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            {/* Featured Icon */}
            <div className="w-16 h-16 rounded-3xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mb-4 shadow-lg">
              <Camera className="w-8 h-8" />
            </div>

            <h4 className="text-base sm:text-lg font-bold text-white mb-1">
              Upload Medicine Package
            </h4>
            <p className="text-xs sm:text-sm text-slate-400 max-w-sm mb-5 leading-relaxed">
              Take a clear photo or upload an image of the medicine label/box for instant AI parsing.
            </p>

            {/* Action Buttons */}
            <div className="flex items-center gap-3 flex-wrap justify-center">
              {/* Desktop / Generic file chooser */}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs sm:text-sm font-bold transition-all shadow-md shadow-blue-600/20 flex items-center gap-1.5 cursor-pointer"
              >
                <Upload className="w-4 h-4" />
                <span>Choose Image</span>
              </button>

              {/* Mobile direct camera capture */}
              <button
                type="button"
                onClick={() => cameraInputRef.current?.click()}
                className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-white/10 text-slate-200 text-xs sm:text-sm font-bold transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <Camera className="w-4 h-4 text-emerald-400" />
                <span>Take Photo</span>
              </button>
            </div>
          </div>
        )}

        {/* Hidden Inputs */}
        <input
          type="file"
          ref={fileInputRef}
          accept="image/jpeg,image/png,image/webp,application/pdf"
          onChange={(e) => e.target.files?.[0] && validateAndProcessFile(e.target.files[0])}
          className="hidden"
        />
        <input
          type="file"
          ref={cameraInputRef}
          accept="image/*"
          capture="environment"
          onChange={(e) => e.target.files?.[0] && validateAndProcessFile(e.target.files[0])}
          className="hidden"
        />
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-3 p-3 rounded-2xl bg-red-500/15 border border-red-500/30 flex items-center gap-2 text-xs text-red-300">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
