import React, { useEffect, useRef, useState } from 'react';

/**
 * SparklesCore
 * 21st.dev Sparkles component (by Manu Arora), tailored for ORMA AI.
 * Ultra-lightweight Canvas 2D particle engine with calm healthcare aesthetics,
 * radial mask support, and reduced-motion safety.
 */
export default function SparklesCore({
  id = 'sparkles',
  className = '',
  background = 'transparent',
  minSize = 0.4,
  maxSize = 1.2,
  speed = 0.5,
  particleColor = '#38bdf8', // ORMA Voice Cyan / Sapphire
  particleDensity = 50,
}) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const [isReducedMotion, setIsReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setIsReducedMotion(mediaQuery.matches);
    const handler = (e) => setIsReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId;
    let particles = [];
    let width = (canvas.width = container.clientWidth);
    let height = (canvas.height = container.clientHeight);

    // Color variations: Sapphire Blue, Voice Cyan, Soft White
    const colors = [
      particleColor,
      '#60a5fa', // Blue 400
      '#22d3ee', // Cyan 400
      '#e0f2fe', // Soft Ice Blue / White
    ];

    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const initParticles = () => {
      width = container.clientWidth;
      height = container.clientHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.scale(dpr, dpr);

      // Scale density for smaller screens (mobile / tablet)
      const count = Math.max(
        15,
        Math.floor((width * height) / (120000 / (particleDensity || 50)))
      );

      particles = [];
      for (let i = 0; i < count; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          size: Math.random() * (maxSize - minSize) + minSize,
          color: colors[Math.floor(Math.random() * colors.length)],
          vx: (Math.random() - 0.5) * speed * (isReducedMotion ? 0.05 : 0.4),
          vy: (Math.random() - 0.5) * speed * (isReducedMotion ? 0.05 : 0.4),
          alpha: Math.random() * 0.6 + 0.2,
          targetAlpha: Math.random() * 0.7 + 0.2,
          fadeSpeed: Math.random() * 0.008 + 0.002,
        });
      }
    };

    initParticles();

    const handleResize = () => {
      if (container) {
        initParticles();
      }
    };

    window.addEventListener('resize', handleResize);

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      particles.forEach((p) => {
        // Move particle gently
        if (!isReducedMotion) {
          p.x += p.vx;
          p.y += p.vy;

          if (p.x < 0) p.x = width;
          if (p.x > width) p.x = 0;
          if (p.y < 0) p.y = height;
          if (p.y > height) p.y = 0;
        }

        // Smooth subtle alpha breathing
        if (Math.abs(p.alpha - p.targetAlpha) < 0.01) {
          p.targetAlpha = Math.random() * 0.7 + 0.2;
        } else {
          p.alpha += (p.targetAlpha - p.alpha) * p.fadeSpeed;
        }

        // Draw soft glow dot
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.alpha;
        ctx.shadowBlur = 4;
        ctx.shadowColor = p.color;
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
    };
  }, [minSize, maxSize, speed, particleColor, particleDensity, isReducedMotion]);

  return (
    <div
      ref={containerRef}
      id={id}
      className={`relative w-full h-full overflow-hidden pointer-events-none ${className}`}
      style={{ background }}
      aria-hidden="true"
    >
      <canvas ref={canvasRef} className="absolute inset-0 block w-full h-full" />
    </div>
  );
}
