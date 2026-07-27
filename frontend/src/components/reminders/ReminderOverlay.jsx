import { motion } from 'framer-motion';

export default function ReminderOverlay({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="orma-modal-overlay"
      aria-modal="true"
      role="dialog"
    >
      {children}
    </motion.div>
  );
}
