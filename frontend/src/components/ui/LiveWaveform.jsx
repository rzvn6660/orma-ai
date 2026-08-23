import React, { useEffect, useRef } from 'react';

/**
 * LiveWaveform
 * 21st.dev / ElevenLabs Live Waveform component adapted for ORMA AI.
 * Displays live microphone volume amplitude during listening and
 * gentle speech cadence during speaking.
 */
export default function LiveWaveform({
  active = false,
  mode = 'listening', // 'listening' | 'speaking'
  audioLevel = 0,
  barCount = 20,
  barWidth = 3,
  barGap = 2,
  height = 28,
  color = '#22d3ee', // Cyan 400 for listening, Blue 400 for speaking
  className = ''
}) {
  const canvasRef = useRef(null);
  const animFrameRef = useRef(null);
  const timeRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const isReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const totalWidth = barCount * barWidth + (barCount - 1) * barGap;
    canvas.width = totalWidth * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${totalWidth}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);

    const render = () => {
      ctx.clearRect(0, 0, totalWidth, height);
      timeRef.current += isReduced ? 0.01 : 0.04;
      const t = timeRef.current;

      const midY = height / 2;
      const halfCount = barCount / 2;

      for (let i = 0; i < barCount; i++) {
        const x = i * (barWidth + barGap);
        const normDistFromCenter = 1 - Math.abs(i - halfCount) / halfCount; // 0 to 1 at center

        let barH = 4; // minimum height

        if (active) {
          if (mode === 'listening') {
            // React to live mic audio level + subtle organic jitter
            const jitter = Math.sin(t * 3 + i * 0.8) * 0.2 + 0.8;
            const levelScale = Math.max(0.1, audioLevel * 1.8);
            barH = Math.max(4, Math.min(height - 2, normDistFromCenter * levelScale * height * jitter + 4));
          } else if (mode === 'speaking') {
            // Smooth organic speech envelope
            const wave1 = Math.sin(t * 2.5 + i * 0.35) * 0.4;
            const wave2 = Math.cos(t * 1.5 - i * 0.2) * 0.3;
            const combined = Math.max(0.15, (0.45 + wave1 + wave2) * normDistFromCenter);
            barH = Math.max(4, Math.min(height - 2, combined * height * 0.9 + 4));
          }
        }

        const y = midY - barH / 2;
        const radius = barWidth / 2;

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barH, radius);
        ctx.fill();
      }

      if (active) {
        animFrameRef.current = requestAnimationFrame(render);
      }
    };

    if (active) {
      animFrameRef.current = requestAnimationFrame(render);
    } else {
      render(); // Draw flat idle line
    }

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [active, mode, audioLevel, barCount, barWidth, barGap, height, color]);

  return (
    <div className={`flex items-center justify-center pointer-events-none select-none ${className}`} aria-hidden="true">
      <canvas ref={canvasRef} className="block" />
    </div>
  );
}
