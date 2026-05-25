import { useEffect, useState } from 'react';
import { statsService } from '../../services/statsService';
import { parseApiError } from '../../utils/validators';
import StatCard from '../../components/common/StatCard/StatCard';
import Loader from '../../components/common/Loader/Loader';
import ErrorMessage from '../../components/common/ErrorMessage/ErrorMessage';
import styles from './dashboard.module.css';

const Dashboard = () => {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await statsService.getOverview();
        if (!cancelled) setOverview(data);
      } catch (err) {
        if (!cancelled) setError(parseApiError(err, 'Could not load the dashboard.'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Overview</h1>
        <p className={styles.subtitle}>
          Live snapshot of users, sessions, battles, and the question catalog.
        </p>
      </header>

      {loading ? <Loader /> : null}
      {error ? <ErrorMessage message={error} /> : null}

      {overview ? (
        <>
          <section className={styles.statRow}>
            <StatCard
              accent="teal"
              label="Total users"
              value={overview.total_users.toLocaleString()}
              sub={`${overview.verified_users} verified · ${overview.users_with_profile} with profile`}
            />
            <StatCard
              accent="blue"
              label="New users (7d)"
              value={overview.new_users_last_7_days}
              sub={`${overview.new_users_last_30_days} in last 30 days`}
            />
            <StatCard
              accent="purple"
              label="Mock sessions"
              value={overview.total_mock_sessions.toLocaleString()}
              sub={`${overview.completed_mock_sessions} completed · ${overview.pending_mock_sessions} pending`}
            />
            <StatCard
              accent="gold"
              label="1v1 battles"
              value={overview.total_battles.toLocaleString()}
              sub={`${overview.battles_last_7_days} in last 7 days`}
            />
            <StatCard
              accent="red"
              label="Active users"
              value={overview.active_users.toLocaleString()}
              sub="Account status active"
            />
            <StatCard
              accent="teal"
              label="Questions in catalog"
              value={overview.total_questions.toLocaleString()}
              sub="Across all subjects"
            />
          </section>

          <section className={styles.grid}>
            <SignupTrend points={overview.signup_trend_30d} />
            <TargetExamBreakdown rows={overview.by_target_exam} />
          </section>
        </>
      ) : null}
    </div>
  );
};

const SignupTrend = ({ points }) => {
  if (!points || points.length === 0) return null;
  const max = Math.max(1, ...points.map((p) => p.count));
  const total = points.reduce((sum, p) => sum + p.count, 0);
  return (
    <section className={styles.card}>
      <header className={styles.cardHeader}>
        <div>
          <h2 className={styles.cardTitle}>Signup trend</h2>
          <p className={styles.cardSubtitle}>Daily signups over the last 30 days</p>
        </div>
        <span className={styles.totalBadge}>{total} total</span>
      </header>

      <div className={styles.chart}>
        {points.map((p) => (
          <div key={p.date} className={styles.bar} title={`${p.date}: ${p.count}`}>
            <span
              className={styles.barFill}
              style={{ height: `${(p.count / max) * 100}%` }}
              aria-hidden="true"
            />
          </div>
        ))}
      </div>

      <div className={styles.xAxis}>
        <span>{points[0]?.date}</span>
        <span>{points[points.length - 1]?.date}</span>
      </div>
    </section>
  );
};

const TargetExamBreakdown = ({ rows }) => {
  if (!rows || rows.length === 0) {
    return (
      <section className={styles.card}>
        <header className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>By target exam</h2>
        </header>
        <p className={styles.emptyHint}>No profile data yet.</p>
      </section>
    );
  }
  const max = Math.max(...rows.map((r) => r.count));
  return (
    <section className={styles.card}>
      <header className={styles.cardHeader}>
        <h2 className={styles.cardTitle}>By target exam</h2>
        <p className={styles.cardSubtitle}>Distribution of student profiles</p>
      </header>
      <ul className={styles.barList}>
        {rows.map((r) => (
          <li key={r.target_exam} className={styles.barRow}>
            <span className={styles.barLabel}>{r.target_exam.replace(/_/g, ' ')}</span>
            <div className={styles.barTrack}>
              <span
                className={styles.barTrackFill}
                style={{ width: `${(r.count / max) * 100}%` }}
                aria-hidden="true"
              />
            </div>
            <span className={styles.barCount}>{r.count}</span>
          </li>
        ))}
      </ul>
    </section>
  );
};

export default Dashboard;
