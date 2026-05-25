import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../../services/authService';
import { parseApiError, validateEmail, validateLoginPassword } from '../../utils/validators';
import Button from '../../components/common/Button/Button';
import InputField from '../../components/common/InputField/InputField';
import ErrorMessage from '../../components/common/ErrorMessage/ErrorMessage';
import styles from './login.module.css';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from?.pathname || '/dashboard';

  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({ email: '', password: '' });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const onChange = (field) => (e) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: '' }));
  };

  const onBlur = (field) => () => {
    const value = form[field];
    let err = '';
    if (field === 'email') err = validateEmail(value);
    if (field === 'password') err = validateLoginPassword(value);
    setErrors((prev) => ({ ...prev, [field]: err }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const nextErrors = {
      email: validateEmail(form.email),
      password: validateLoginPassword(form.password),
    };
    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) return;

    setSubmitting(true);
    setFormError('');
    try {
      await authService.login(form);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setFormError(parseApiError(err, 'Could not sign you in.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.brandBlock}>
          <span className={styles.brandMark}>MM</span>
          <p className={styles.brandTitle}>MakeMyMock</p>
          <p className={styles.brandSub}>Admin Console</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form} noValidate>
          <h1 className={styles.title}>Sign in</h1>
          <p className={styles.subtitle}>
            Restricted area. Sign in with your administrator credentials.
          </p>

          <InputField
            label="Email"
            type="email"
            value={form.email}
            onChange={onChange('email')}
            onBlur={onBlur('email')}
            placeholder="admin@makemymock.local"
            autoComplete="username"
            error={errors.email}
          />

          <InputField
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={form.password}
            onChange={onChange('password')}
            onBlur={onBlur('password')}
            placeholder="••••••••"
            autoComplete="current-password"
            error={errors.password}
            rightAdornment={
              <button
                type="button"
                className={styles.eye}
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            }
          />

          {formError ? <ErrorMessage message={formError} /> : null}

          <Button type="submit" fullWidth loading={submitting}>
            Sign in
          </Button>
        </form>
      </div>
    </div>
  );
};

export default Login;
