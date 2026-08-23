export const ReminderSoundService = {
  isEnabled: () => localStorage.getItem('orma_sound_enabled') !== 'false',
  
  toggle: (enabled) => localStorage.setItem('orma_sound_enabled', enabled),

  play: async () => {
    if (!ReminderSoundService.isEnabled()) return;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return;
      
      const ctx = new AudioContextClass();
      if (ctx.state === 'suspended') {
        await ctx.resume().catch(() => {});
      }
      
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = 'sine';
      
      // Soft, calm two-tone chime (C5: 523.25Hz -> E5: 659.25Hz)
      const now = ctx.currentTime;
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.setValueAtTime(659.25, now + 0.25);
      
      // Gentle fade in and out (max volume 0.35 - calm and reassuring)
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.35, now + 0.08);
      gain.gain.setValueAtTime(0.35, now + 0.35);
      gain.gain.linearRampToValueAtTime(0, now + 0.85);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.start(now);
      osc.stop(now + 0.85);
      
      await new Promise(resolve => setTimeout(resolve, 900));
      ctx.close().catch(() => {});
    } catch (err) {
      console.warn('[ReminderSoundService] Audio playback skipped or blocked:', err);
    }
  }
};

