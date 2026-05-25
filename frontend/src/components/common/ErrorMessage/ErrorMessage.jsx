import React from 'react';
import styles from './ErrorMessage.module.css';

const ErrorMessage = ({ message }) => {
  if (!message) return null;
  return (
    <p role="alert" className={styles.pill}>
      {message}
    </p>
  );
};

export default ErrorMessage;
