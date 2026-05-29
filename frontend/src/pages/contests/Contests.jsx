import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Button from '../../components/common/Button/Button';
import ErrorMessage from '../../components/common/ErrorMessage/ErrorMessage';
import Loader from '../../components/common/Loader/Loader';
import { contestService } from '../../services/contestService';
import { parseApiError } from '../../utils/validators';
import styles from './contests.module.css';

const fmtDateTime = (iso) =>
  new Date(iso).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

const fmtDuration = (seconds) => {
  const m = Math.round(seconds / 60);
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  const rem = m % 60;
  return rem ? `${h}h ${rem}m` : `${h}h`;
};

const StatusBadge = ({ status }) => {
  const tone =
    status === 'live' ? styles.badgeLive
      : status === 'scheduled' ? styles.badgeScheduled
        : styles.badgeDone;
  return <span className={`${styles.badge} ${tone}`}>{status}</span>;
};

const Contests = () => {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await contestService.list();
      setItems(res.items || []);
    } catch (err) {
      setError(parseApiError(err, 'Could not load contests.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onDelete = async (id, title) => {
    if (!window.confirm(`Delete contest "${title}"? This cannot be undone.`)) return;
    try {
      await contestService.remove(id);
      load();
    } catch (err) {
      setError(parseApiError(err, 'Could not delete contest.'));
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Contests</h1>
          <p className={styles.subtitle}>
            {items.length} total · scheduled events appear here once created
          </p>
        </div>
        <div className={styles.headerActions}>
          <Button variant="primary" onClick={() => navigate('/contests/new')}>
            + New contest
          </Button>
        </div>
      </header>

      {error ? <ErrorMessage message={error} /> : null}

      <section className={styles.tableWrap}>
        {loading ? (
          <Loader />
        ) : items.length === 0 ? (
          <div className={styles.empty}>
            <p>No contests yet.</p>
            <Button variant="outline" onClick={() => navigate('/contests/new')}>
              Schedule your first contest
            </Button>
          </div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Starts</th>
                <th>Duration</th>
                <th>Questions</th>
                <th>Participants</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {items.map((c) => (
                <tr key={c.id}>
                  <td>
                    <Link to={`/contests/${c.id}`} className={styles.titleLink}>
                      {c.title}
                    </Link>
                    {c.description ? (
                      <p className={styles.descCell}>{c.description}</p>
                    ) : null}
                  </td>
                  <td><StatusBadge status={c.status} /></td>
                  <td>
                    <p className={styles.cell}>{fmtDateTime(c.start_time)}</p>
                    <p className={styles.cellSub}>ends {fmtDateTime(c.end_time)}</p>
                  </td>
                  <td>{fmtDuration(c.duration_seconds)}</td>
                  <td>{c.question_count}</td>
                  <td>{c.participant_count}</td>
                  <td>
                    <div className={styles.rowActions}>
                      <Link to={`/contests/${c.id}`} className={styles.detailLink}>
                        Edit →
                      </Link>
                      {c.status === 'scheduled' ? (
                        <button
                          type="button"
                          className={styles.dangerLink}
                          onClick={() => onDelete(c.id, c.title)}
                        >
                          Delete
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
};

export default Contests;
