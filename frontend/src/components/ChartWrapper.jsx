import React, { useState, useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';

export default function ChartWrapper({ children, minHeight = 256 }) {
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!containerRef.current) return;
    
    let debounceTimer;
    const observer = new ResizeObserver(entries => {
      // Use debounce to prevent duplicate triggers in Strict Mode
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        for (let entry of entries) {
          const { width, height } = entry.contentRect;
          // Only update and render chart if container is practically visible (>0)
          if (width > 0 && height > 0) {
            setDimensions({ width, height });
          } else {
            // If hidden (e.g. inside inactive tab), reset to prevent Recharts warnings
            setDimensions({ width: 0, height: 0 });
          }
        }
      }, 10);
    });
    
    observer.observe(containerRef.current);
    
    return () => {
      clearTimeout(debounceTimer);
      observer.disconnect();
    };
  }, []);

  // minWidth: 0 is absolutely required for Recharts to not overflow flex containers
  return (
    <div 
      ref={containerRef} 
      style={{ width: '100%', height: '100%', minHeight, minWidth: 0, position: 'relative' }}
    >
      {dimensions.width > 0 && dimensions.height > 0 ? (
        children
      ) : (
        <div 
          className="absolute inset-0 flex items-center justify-center bg-slate-800/20 rounded-xl border border-slate-700/30"
          style={{ minHeight }}
        >
          <div className="flex flex-col items-center gap-3 text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin opacity-50" />
            <span className="text-xs font-medium uppercase tracking-wider opacity-50">Loading Chart...</span>
          </div>
        </div>
      )}
    </div>
  );
}
