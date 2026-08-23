import React, { useEffect, useRef } from 'react';
import { Renderer, Program, Mesh, Triangle, Vec3 } from 'ogl';

/**
 * OrmaShaderOrb
 * Premium, calm WebGL shader orb tailored for ORMA AI healthcare companion.
 * Inspired by 21st.dev Voice Powered Orb, adapted to ORMA's royal navy & cyan aesthetic.
 */
export default function OrmaShaderOrb({ 
  state = 'idle', 
  audioLevel = 0, 
  isSpeaking = false, 
  isProcessing = false,
  className = ''
}) {
  const containerRef = useRef(null);

  const vert = /* glsl */ `
    precision highp float;
    attribute vec2 position;
    attribute vec2 uv;
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = vec4(position, 0.0, 1.0);
    }
  `;

  const frag = /* glsl */ `
    precision highp float;

    uniform float iTime;
    uniform vec3 iResolution;
    uniform float stateMode;    // 0: idle, 1: listening, 2: thinking, 3: speaking, 4: error
    uniform float audioLevel;   // 0.0 - 1.0
    uniform float rot;
    varying vec2 vUv;

    // Fast 3D simplex noise
    vec3 hash33(vec3 p3) {
      p3 = fract(p3 * vec3(0.1031, 0.11369, 0.13787));
      p3 += dot(p3, p3.yxz + 19.19);
      return -1.0 + 2.0 * fract(vec3(
        p3.x + p3.y,
        p3.x + p3.z,
        p3.y + p3.z
      ) * p3.zyx);
    }

    float snoise3(vec3 p) {
      const float K1 = 0.333333333;
      const float K2 = 0.166666667;
      vec3 i = floor(p + (p.x + p.y + p.z) * K1);
      vec3 d0 = p - (i - (i.x + i.y + i.z) * K2);
      vec3 e = step(vec3(0.0), d0 - d0.yzx);
      vec3 i1 = e * (1.0 - e.zxy);
      vec3 i2 = 1.0 - e.zxy * (1.0 - e);
      vec3 d1 = d0 - (i1 - K2);
      vec3 d2 = d0 - (i2 - K1);
      vec3 d3 = d0 - 0.5;
      vec4 h = max(0.6 - vec4(
        dot(d0, d0),
        dot(d1, d1),
        dot(d2, d2),
        dot(d3, d3)
      ), 0.0);
      vec4 n = h * h * h * h * vec4(
        dot(d0, hash33(i)),
        dot(d1, hash33(i + i1)),
        dot(d2, hash33(i + i2)),
        dot(d3, hash33(i + 1.0))
      );
      return dot(vec4(31.316), n);
    }

    vec4 extractAlpha(vec3 colorIn) {
      float a = max(max(colorIn.r, colorIn.g), colorIn.b);
      return vec4(colorIn.rgb / (a + 1e-5), smoothstep(0.05, 0.95, a));
    }

    float light1(float intensity, float attenuation, float dist) {
      return intensity / (1.0 + dist * attenuation);
    }

    float light2(float intensity, float attenuation, float dist) {
      return intensity / (1.0 + dist * dist * attenuation);
    }

    vec4 draw(vec2 uv) {
      // ORMA Tailored Palette: Royal Navy, ORMA Blue, Voice Cyan, Soft Emerald/Violet
      vec3 colorBlue = vec3(0.14, 0.45, 0.95);   // ORMA Primary Blue
      vec3 colorCyan = vec3(0.10, 0.82, 0.94);   // ORMA Voice Cyan
      vec3 colorNavy = vec3(0.03, 0.07, 0.24);   // Deep Navy Base
      vec3 colorViolet = vec3(0.38, 0.22, 0.85); // Subtle Thinking Violet
      vec3 colorPink = vec3(0.85, 0.25, 0.65);   // Speech Pulse Accent

      vec3 c1 = colorBlue;
      vec3 c2 = colorCyan;
      vec3 c3 = colorNavy;

      // State color adaptation
      if (stateMode > 1.5 && stateMode < 2.5) {
        // Thinking: Blue & Violet
        c1 = mix(colorBlue, colorViolet, 0.6);
        c2 = colorCyan;
      } else if (stateMode > 2.5 && stateMode < 3.5) {
        // Speaking: Cyan & Deep Blue with subtle warmth
        c1 = colorCyan;
        c2 = mix(colorBlue, colorPink, 0.25);
      } else if (stateMode > 3.5) {
        // Error: Muted Amber/Red
        c1 = vec3(0.85, 0.35, 0.2);
        c2 = vec3(0.95, 0.6, 0.2);
      }

      float ang = atan(uv.y, uv.x);
      float len = length(uv);
      float invLen = len > 0.0 ? 1.0 / len : 0.0;

      float noiseSpeed = 0.35;
      float noiseScale = 0.65;
      float innerRadius = 0.58;

      if (stateMode > 0.5 && stateMode < 1.5) {
        // Listening reacts to real audio level
        noiseSpeed = 0.4 + audioLevel * 0.8;
        innerRadius = 0.55 + audioLevel * 0.12;
      } else if (stateMode > 2.5 && stateMode < 3.5) {
        // Speaking
        noiseSpeed = 0.65;
      }

      float n0 = snoise3(vec3(uv * noiseScale, iTime * noiseSpeed)) * 0.5 + 0.5;
      float r0 = mix(mix(innerRadius, 0.95, 0.35), mix(innerRadius, 0.95, 0.65), n0);
      float d0 = distance(uv, (r0 * invLen) * uv);
      
      float v0 = light1(1.0, 10.0, d0);
      v0 *= smoothstep(r0 * 1.05, r0, len);
      float cl = cos(ang + iTime * 1.5) * 0.5 + 0.5;

      float a = iTime * -0.8;
      vec2 pos = vec2(cos(a), sin(a)) * r0;
      float d = distance(uv, pos);
      float v1 = light2(1.4, 5.0, d);
      v1 *= light1(1.0, 45.0, d0);

      float v2 = smoothstep(0.98, mix(innerRadius, 0.98, n0 * 0.5), len);
      float v3 = smoothstep(innerRadius * 0.7, mix(innerRadius, 0.98, 0.5), len);

      vec3 col = mix(c1, c2, cl);
      col = mix(c3, col, v0);
      col = (col + v1) * v2 * v3;
      col = clamp(col, 0.0, 1.0);

      return extractAlpha(col);
    }

    void main() {
      vec2 center = iResolution.xy * 0.5;
      float size = min(iResolution.x, iResolution.y);
      vec2 uv = (gl_FragCoord.xy - center) / size * 2.0;

      float angle = rot;
      float s = sin(angle);
      float c = cos(angle);
      uv = vec2(c * uv.x - s * uv.y, s * uv.x + c * uv.y);

      // Subtle organic wave perturbation
      float hoverDistort = (stateMode > 0.5 && stateMode < 1.5) 
        ? (0.05 + audioLevel * 0.12) 
        : (stateMode > 2.5 && stateMode < 3.5) ? 0.08 : 0.03;

      uv.x += hoverDistort * sin(uv.y * 8.0 + iTime);
      uv.y += hoverDistort * sin(uv.x * 8.0 + iTime);

      vec4 col = draw(uv);
      gl_FragColor = vec4(col.rgb * col.a, col.a);
    }
  `;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let rendererInstance = null;
    let gl = null;
    let rafId = null;
    let program = null;

    try {
      rendererInstance = new Renderer({
        alpha: true,
        premultipliedAlpha: false,
        antialias: true,
        dpr: Math.min(window.devicePixelRatio || 1, 2)
      });

      gl = rendererInstance.gl;
      gl.clearColor(0, 0, 0, 0);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

      // Clean existing canvas
      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }
      gl.canvas.style.display = 'block';
      gl.canvas.style.position = 'absolute';
      gl.canvas.style.top = '0';
      gl.canvas.style.left = '0';
      gl.canvas.style.width = '100%';
      gl.canvas.style.height = '100%';
      container.appendChild(gl.canvas);

      const geometry = new Triangle(gl);
      program = new Program(gl, {
        vertex: vert,
        fragment: frag,
        uniforms: {
          iTime: { value: 0 },
          iResolution: {
            value: new Vec3(gl.canvas.width, gl.canvas.height, gl.canvas.width / (gl.canvas.height || 1)),
          },
          stateMode: { value: 0 },
          audioLevel: { value: 0 },
          rot: { value: 0 },
        },
      });

      const mesh = new Mesh(gl, { geometry, program });

      const handleResize = () => {
        if (!container || !rendererInstance || !gl) return;
        const width = container.clientWidth;
        const height = container.clientHeight;
        if (width === 0 || height === 0) return;

        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        rendererInstance.setSize(width * dpr, height * dpr);
        gl.canvas.style.width = `${width}px`;
        gl.canvas.style.height = `${height}px`;

        if (program) {
          program.uniforms.iResolution.value.set(
            gl.canvas.width,
            gl.canvas.height,
            gl.canvas.width / gl.canvas.height
          );
        }
      };

      window.addEventListener('resize', handleResize);
      handleResize();

      let lastTime = performance.now();
      let currentRot = 0;

      // Check user reduced motion preference
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      const render = (now) => {
        rafId = requestAnimationFrame(render);
        if (!program || !gl || !rendererInstance) return;

        const delta = (now - lastTime) * 0.001;
        lastTime = now;

        const timeScale = prefersReducedMotion ? 0.2 : 1.0;
        program.uniforms.iTime.value = (now * 0.001) * timeScale;

        // Map state string to numeric stateMode uniform
        let modeNum = 0; // idle
        if (state === 'listening') modeNum = 1;
        else if (isProcessing || state === 'thinking') modeNum = 2;
        else if (isSpeaking || state === 'speaking') modeNum = 3;
        else if (state === 'error') modeNum = 4;

        program.uniforms.stateMode.value = modeNum;
        program.uniforms.audioLevel.value = audioLevel || 0;

        // Rotation speed adapts smoothly to voice state and audio level
        let rotSpeed = 0.2; // calm idle
        if (modeNum === 1) {
          rotSpeed = 0.3 + (audioLevel * 1.5);
        } else if (modeNum === 2) {
          rotSpeed = 0.4;
        } else if (modeNum === 3) {
          rotSpeed = 0.55;
        }

        if (!prefersReducedMotion) {
          currentRot += delta * rotSpeed;
        }
        program.uniforms.rot.value = currentRot;

        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        rendererInstance.render({ scene: mesh });
      };

      rafId = requestAnimationFrame(render);

      return () => {
        if (rafId) cancelAnimationFrame(rafId);
        window.removeEventListener('resize', handleResize);
        if (container && gl && gl.canvas && container.contains(gl.canvas)) {
          container.removeChild(gl.canvas);
        }
      };
    } catch (err) {
      console.warn('WebGL Shader Orb fallback to CSS mode:', err);
    }
  }, [state, isSpeaking, isProcessing]);

  return (
    <div 
      ref={containerRef} 
      className={`w-full h-full relative overflow-hidden pointer-events-none ${className}`}
      aria-hidden="true"
    />
  );
}
