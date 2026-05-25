import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { userService } from '../../services/userService';
import { parseApiError } from '../../utils/validators';
import Loader from '../../components/common/Loader/Loader';
import ErrorMessage from '../../components/common/ErrorMessage/ErrorMessage';
import StatCard from '../../components/common/StatCard/StatCard';
import styles from './userDetail.module.css';

const FIELD_LABELS = {
  full_name: 'Full name',
  username: 'Username',
  email: 'Email',
  phone_number: 'Phone',
  gender: 'Gender',
  date_of_birth: 'Date of birth',
  class_grade: 'Class',
  target_exam: 'Target exam',
  state: 'State',
  city: 'City',
  school_name: 'School',
  preferred_language: 'Preferred language',
};

const UserDetail = () => {
  const { userId } = useParams();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await userService.get(userId);
        if (!cancelled) setUser(data);
      } catch (err) {
        if (!cancelled) setError(parseApiError(err, 'Could not load this user.'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [userId]);

  if (loading) return <Loader />;
  if (error) return <ErrorMessage message={error} />;
  if (!user) return null;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <Link to="/users" className={styles.back}>← All users</Link>
        <div className={styles.identity}>
          <span className={styles.avatar}>
            {(user.username || user.email).slice(0, 1).toUpperCase()}
          </span>
          <div>
            <h1 className={styles.title}>{user.full_name || user.username}</h1>
            <p className={styles.subtitle}>{user.email}</p>
            <div className={styles.statusRow}>
              <span className={`${styles.badge} ${
                user.is_verified ? styles.badgeOk : styles.badgePending
              }`}>
                {user.is_verified ? 'Verified' : 'Unverified'}
              </span>
              <span className={`${styles.badge} ${
                user.is_active ? styles.badgeOk : styles.badgeDanger
              }`}>
                {user.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <section className={styles.statRow}>
        <StatCard
          label="Mock tests started"
          value={user.total_mock_tests}
          sub={`${user.completed_mock_tests} completed`}
          accent="teal"
        />
        <StatCard
          label="1v1 battles"
          value={user.total_battles}
          sub="Lifetime"
          accent="gold"
        />
        <StatCard
          label="Joined"
          value={user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
          sub="Account created"
          accent="blue"
        />
      </section>

      <section className={styles.card}>
        <h2 className={styles.cardTitle}>Profile details</h2>
        <dl className={styles.fields}>
          {Object.entries(FIELD_LABELS).map(([key, label]) => (
            <div key={key} className={styles.field}>
              <dt>{label}</dt>
              <dd>{formatValue(user[key])}</dd>
            </div>
          ))}
        </dl>
      </section>
    </div>
  );
};

const formatValue = (v) => {
  if (v == null || v === '') return '—';
  if (typeof v === 'string') return v.replace(/_/g, ' ');
  return String(v);
};

export default UserDetail;
