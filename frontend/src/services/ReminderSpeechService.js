import { tts } from './tts';

export const ReminderSpeechService = {
  isEnabled: () => localStorage.getItem('orma_voice_enabled') !== 'false',
  
  toggle: (enabled) => localStorage.setItem('orma_voice_enabled', enabled),

  getGreeting: () => {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) return 'Good morning';
    if (hour >= 12 && hour < 17) return 'Good afternoon';
    if (hour >= 17 && hour < 22) return 'Good evening';
    return 'Good night';
  },

  speak: async (medicine, user) => {
    if (!ReminderSpeechService.isEnabled()) return;
    
    try {
      const name = user?.first_name || user?.name || 'there';
      const greeting = ReminderSpeechService.getGreeting();
      
      const isHealthEvent = medicine.event_type !== undefined;
      const eventType = isHealthEvent ? medicine.event_type : 'medicine';
      const title = isHealthEvent ? medicine.title : medicine.medicine_name;
      const description = isHealthEvent ? medicine.description : medicine.dosage;

      let sentence = `${greeting}, ${name}. `;
      
      if (eventType === 'medicine') {
        sentence += `It's time to take your ${title} ${description || ''}`;
        if (medicine.purpose) sentence += ` for ${medicine.purpose}.`;
        else sentence += '.';
      } else if (eventType === 'doctor_appointment') {
        sentence += `You have an appointment with ${title} coming up.`;
      } else if (eventType === 'blood_test') {
        sentence += `Reminder: You have a ${title} scheduled.`;
      } else if (eventType === 'exercise') {
        sentence += `It's time for your ${title}. Let's get moving!`;
      } else if (eventType === 'water_reminder') {
        sentence += `Time to drink some water. Stay hydrated!`;
      } else {
        sentence += `This is a reminder for your ${title}.`;
      }

      return new Promise((resolve) => {
        tts.speak(sentence, {
          onEnd: resolve,
          onError: (err) => {
            console.warn('[ReminderSpeechService] TTS Error:', err);
            resolve();
          }
        });
      });
    } catch (err) {
      console.warn('[ReminderSpeechService] Failed to speak:', err);
    }
  }
};
