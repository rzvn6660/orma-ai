/**
 * emergencyAudio.js
 * Professional Healthcare Emergency Tone Synthesizer using Web Audio API.
 * Produces a calm yet urgent two-tone medical chime (A5 -> D6) with exponential decay.
 * Respects browser autoplay restrictions and looping control.
 */

let audioCtx = null;
let isLooping = false;
let loopTimeout = null;
let isAudioBlocked = false;

function getAudioContext() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  return audioCtx;
}

/**
 * Play a single two-tone medical chime pattern:
 * Tone 1: 880Hz (A5) for 150ms
 * Gap: 80ms
 * Tone 2: 1174.66Hz (D6) for 250ms
 */
function playTonePair() {
  const ctx = getAudioContext();
  if (!ctx) return;

  if (ctx.state === 'suspended') {
    ctx.resume().catch(() => {
      isAudioBlocked = true;
    });
  }

  const now = ctx.currentTime;

  // Tone 1: 880 Hz (A5)
  const osc1 = ctx.createOscillator();
  const gain1 = ctx.createGain();
  osc1.type = 'sine';
  osc1.frequency.setValueAtTime(880, now);
  gain1.gain.setValueAtTime(0, now);
  gain1.gain.linearRampToValueAtTime(0.35, now + 0.02);
  gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
  osc1.connect(gain1);
  gain1.connect(ctx.destination);
  osc1.start(now);
  osc1.stop(now + 0.2);

  // Tone 2: 1174.66 Hz (D6)
  const osc2 = ctx.createOscillator();
  const gain2 = ctx.createGain();
  osc2.type = 'sine';
  osc2.frequency.setValueAtTime(1174.66, now + 0.22);
  gain2.gain.setValueAtTime(0, now + 0.22);
  gain2.gain.linearRampToValueAtTime(0.4, now + 0.24);
  gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
  osc2.connect(gain2);
  gain2.connect(ctx.destination);
  osc2.start(now + 0.22);
  osc2.stop(now + 0.52);
}

/**
 * Starts the looping emergency sound (plays chime, pauses 3s, repeats).
 */
export function startEmergencySound() {
  // Respect sound settings
  const soundPref = localStorage.getItem('orma_sound');
  if (soundPref === 'disabled') return;

  const ctx = getAudioContext();
  if (ctx && ctx.state === 'suspended') {
    ctx.resume().then(() => {
      isAudioBlocked = false;
    }).catch(() => {
      isAudioBlocked = true;
    });
  }

  if (isLooping) return;
  isLooping = true;

  const loop = () => {
    if (!isLooping) return;
    try {
      playTonePair();
    } catch (e) {
      console.warn('[AUDIO] Error playing emergency tone:', e);
    }
    // Repeat every 3.5 seconds while active
    loopTimeout = setTimeout(loop, 3500);
  };

  loop();
}

/**
 * Stops the looping emergency sound immediately.
 */
export function stopEmergencySound() {
  isLooping = false;
  if (loopTimeout) {
    clearTimeout(loopTimeout);
    loopTimeout = null;
  }
}

/**
 * User gesture unlock handler for browser autoplay restrictions.
 */
export function unlockAudioContext() {
  const ctx = getAudioContext();
  if (ctx && ctx.state === 'suspended') {
    ctx.resume().then(() => {
      isAudioBlocked = false;
      if (isLooping) {
        playTonePair();
      }
    });
  }
}

export function isAudioRestricted() {
  const ctx = getAudioContext();
  return ctx ? ctx.state === 'suspended' : isAudioBlocked;
}
