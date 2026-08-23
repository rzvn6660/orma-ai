import React from 'react';
import { motion } from 'framer-motion';

export default function TextReveal({ children, className = "", delay = 0, y = 14 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.55, ease: [0.25, 0.1, 0.25, 1.0], delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
