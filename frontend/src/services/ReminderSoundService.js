export const ReminderSoundService = {
  isEnabled: () => localStorage.getItem('orma_sound_enabled') !== 'false',
  
  toggle: (enabled) => localStorage.setItem('orma_sound_enabled', enabled),

  play: async () => {
    if (!ReminderSoundService.isEnabled()) return;
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      
      osc.type = 'sine';
      
      // Soft, calm two-tone chime (e.g. C5 -> E5)
      osc.frequency.setValueAtTime(523.25, ctx.currentTime);
      osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.3);
      
      // Gentle fade in and out (max volume 0.5)
      gain.gain.setValueAtTime(0, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.5, ctx.currentTime + 0.1);
      gain.gain.setValueAtTime(0.5, ctx.currentTime + 0.4);
      gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 1.2);
      
      osc.connect(gain);
      gain.connect(ctx.destination);
      
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 1.2);
      
      await new Promise(resolve => setTimeout(resolve, 1200));
    } catch (err) {
      console.warn('[ReminderSoundService] Failed to play sound:', err);
    }
  }
};
