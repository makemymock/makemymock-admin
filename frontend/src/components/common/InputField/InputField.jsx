import React, { useId } from 'react';
import styles from './InputField.module.css';

const InputField = ({
  label,
  type = 'text',
  value,
  onChange,
  onBlur,
  placeholder,
  error,
  rightAdornment,
  autoComplete,
  ...rest
}) => {
  const id = useId();
  return (
    <div className={styles.wrap}>
      {label ? (
        <label htmlFor={id} className={styles.label}>
          {label}
        </label>
      ) : null}
      <div className={`${styles.field} ${error ? styles.fieldError : ''}`}>
        <input
          id={id}
          type={type}
          className={styles.input}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          placeholder={placeholder}
          autoComplete={autoComplete}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${id}-error` : undefined}
          {...rest}
        />
        {rightAdornment ? <div className={styles.adornment}>{rightAdornment}</div> : null}
      </div>
      {error ? (
        <p id={`${id}-error`} role="alert" className={styles.error}>
          {error}
        </p>
      ) : null}
    </div>
  );
};

export default InputField;
