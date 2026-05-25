import React from 'react';
import styles from './Loader.module.css';

const Loader = ({ fullscreen = false, label = 'Loading…' }) => {
  return (
    <div
      className={fullscreen ? styles.fullscreen : styles.inline}
      role="status"
      aria-label={label}
    >
      <span className={styles.spinner} aria-hidden="true" />
      <span className={styles.label}>{label}</span>
    </div>
  );
};

export default Loader;
