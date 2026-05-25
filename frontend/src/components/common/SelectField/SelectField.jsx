import React, { useId } from 'react';
import styles from './SelectField.module.css';

const SelectField = ({
  label,
  value,
  onChange,
  options = [],
  placeholder = '— Select —',
  disabled = false,
  error,
  allowEmpty = true,
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
        <select
          id={id}
          className={styles.select}
          value={value ?? ''}
          onChange={onChange}
          disabled={disabled}
          aria-invalid={error ? 'true' : 'false'}
        >
          {allowEmpty ? <option value="">{placeholder}</option> : null}
          {options.map((opt) => {
            const key = typeof opt === 'string' ? opt : opt.value;
            const labelText = typeof opt === 'string' ? opt : opt.label;
            return (
              <option key={key} value={key}>
                {labelText}
              </option>
            );
          })}
        </select>
      </div>
      {error ? (
        <p role="alert" className={styles.error}>
          {error}
        </p>
      ) : null}
    </div>
  );
};

export default SelectField;
