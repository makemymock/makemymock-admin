import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { userService } from '../../services/userService';
import { parseApiError } from '../../utils/validators';
import Button from '../../components/common/Button/Button';
import InputField from '../../components/common/InputField/InputField';
import Loader from '../../components/common/Loader/Loader';
import ErrorMessage from '../../components/common/ErrorMessage/ErrorMessage';
import styles from './users.module.css';

const PAGE_SIZE = 25;

const Users = () => {
  const [data, setData] = useState({ total: 0, page: 1, items: [] });
  const [query, setQuery] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await userService.list({ page, page_size: PAGE_SIZE, q: search });
      setData(res);
    } catch (err) {
      setError(parseApiError(err, 'Could not load users.'));
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => { load(); }, [load]);

  const onSearch = (e) => {
    e.preventDefault();
    setSearch(query.trim());
    setPage(1);
  };

  const onDownload = async () => {
    setDownloading(true);
    try {
      await userService.downloadCsv(search);
    } catch (err) {
      setError(parseApiError(err, 'CSV download failed.'));
    } finally {
      setDownloading(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Users</h1>
          <p className={styles.subtitle}>
            {data.total.toLocaleString()} total · page {data.page} of {totalPages}
          </p>
        </div>
        <div className={styles.headerActions}>
          <Button variant="primary" onClick={onDownload} loading={downloading}>
            ⬇ Download CSV
          </Button>
        </div>
      </header>

      <form className={styles.searchRow} onSubmit={onSearch} role="search">
        <InputField
          placeholder="Search by email or username…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit" variant="outline">Search</Button>
        {search ? (
          <Button
            type="button"
            variant="ghost"
            onClick={() => { setQuery(''); setSearch(''); setPage(1); }}
          >
            Clear
          </Button>
        ) : null}
      </form>

      {error ? <ErrorMessage message={error} /> : null}

      <section className={styles.tableWrap}>
        {loading ? (
          <Loader />
        ) : data.items.length === 0 ? (
          <p className={styles.empty}>No users match this filter.</p>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>User</th>
                <th>Class / Target</th>
                <th>Location</th>
                <th>Status</th>
                <th>Joined</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data.items.map((u) => (
                <tr key={u.id}>
                  <td>
                    <div className={styles.userCell}>
                      <span className={styles.avatar}>
                        {(u.username || u.email).slice(0, 1).toUpperCase()}
                      </span>
                      <div>
                        <p className={styles.userName}>{u.full_name || u.username}</p>
                        <p className={styles.userEmail}>{u.email}</p>
                      </div>
                    </div>
                  </td>
                  <td>
                    <p className={styles.cell}>{u.class_grade ? `Class ${u.class_grade}` : '—'}</p>
                    <p className={styles.cellSub}>{u.target_exam?.replace(/_/g, ' ') || '—'}</p>
                  </td>
                  <td>
                    <p className={styles.cell}>{u.city || '—'}</p>
                    <p className={styles.cellSub}>{u.state || '—'}</p>
                  </td>
                  <td>
                    <span
                      className={`${styles.badge} ${
                        u.is_verified ? styles.badgeOk : styles.badgePending
                      }`}
                    >
                      {u.is_verified ? 'Verified' : 'Unverified'}
                    </span>
                    {!u.is_active ? (
                      <span className={`${styles.badge} ${styles.badgeDanger}`}>Inactive</span>
                    ) : null}
                  </td>
                  <td>
                    <p className={styles.cell}>
                      {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                    </p>
                  </td>
                  <td>
                    <Link to={`/users/${u.id}`} className={styles.detailLink}>
                      View →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <footer className={styles.pagination}>
        <Button
          variant="ghost"
          disabled={page <= 1 || loading}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          ← Previous
        </Button>
        <span className={styles.pageInfo}>
          Page {page} of {totalPages}
        </span>
        <Button
          variant="ghost"
          disabled={page >= totalPages || loading}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
        >
          Next →
        </Button>
      </footer>
    </div>
  );
};

export default Users;
