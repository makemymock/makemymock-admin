import React from 'react';
import styles from './StatCard.module.css';

const StatCard = ({ label, value, sub, accent = 'teal' }) => {
  return (
    <article className={`${styles.card} ${styles[`accent_${accent}`] || ''}`}>
      <p className={styles.label}>{label}</p>
      <p className={styles.value}>{value}</p>
      {sub ? <p className={styles.sub}>{sub}</p> : null}
    </article>
  );
};

export default StatCard;
