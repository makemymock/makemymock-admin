import { useEffect, useMemo, useState } from 'react';
import Loader from '../../components/common/Loader/Loader';
import ErrorMessage from '../../components/common/ErrorMessage/ErrorMessage';
import LineChart from '../../components/common/LineChart/LineChart';
import { observabilityService } from '../../services/observabilityService';
import { parseApiError } from '../../utils/validators';
import styles from './observability.module.css';

const fmt = new Intl.NumberFormat();
const pctFmt = (n) => `${(n * 100).toFixed(2)}%`;

const TABS = [
  { key: 'usage', label: 'Usage (Mongo)' },
  { key: 'infra', label: 'Infrastructure (GCP)' },
];

const Observability = () => {
  const [tab, setTab] = useState('usage');
  return (
    <section className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Observability</h1>
        <p className={styles.subtitle}>
          SolverX usage from MongoDB · Cloud Run health from GCP Monitoring.
        </p>
      </header>

      <nav className={styles.tabs} aria-label="Observability tabs">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            className={`${styles.tab} ${tab === t.key ? styles.tabActive : ''}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {tab === 'usage' ? <UsagePanel /> : <InfraPanel />}
    </section>
  );
};

// ---------------------------------------------------------------
// Usage tab — backed by Mongo `usage_events` (instant; no GCP call)
// ---------------------------------------------------------------

const UsagePanel = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const payload = await observabilityService.getUsage();
        if (!cancelled) setData(payload);
      } catch (err) {
        if (!cancelled) setError(parseApiError(err, 'Could not load usage.'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const series = useMemo(() => (data ? [{
    name: 'SolverX calls',
    points: (data.daily_calls_14d || []).map((p) => ({ x: p.x, y: p.y })),
  }] : []), [data]);

  if (loading) return <Loader />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return null;

  return (
    <>
      <div className={styles.statGrid}>
        <Stat label="Calls (24h)"  value={data.calls_24h}  sub={`${fmt.format(data.tokens_24h)} tokens`} />
        <Stat label="DAU"          value={data.dau}        sub={`WAU ${fmt.format(data.wau)} · MAU ${fmt.format(data.mau)}`} />
        <Stat label="Error rate"   value={pctFmt(data.error_rate_24h)} sub="last 24h" />
        <Stat label="Calls (7d)"   value={data.calls_7d}   sub={`${fmt.format(data.tokens_7d)} tokens`} />
      </div>

      <div className={styles.twoCol}>
        <section className={styles.card}>
          <header className={styles.cardHead}>
            <h2 className={styles.cardTitle}>SolverX calls — last 14 days</h2>
            <span className={styles.cardSub}>1 point per day</span>
          </header>
          {series[0].points.length === 0 ? (
            <p className={styles.empty}>No SolverX usage in the last 14 days yet.</p>
          ) : (
            <LineChart series={series} height={240} ariaLabel="SolverX calls per day" />
          )}
        </section>

        <section className={styles.card}>
          <header className={styles.cardHead}>
            <h2 className={styles.cardTitle}>Model mix — last 7 days</h2>
            <span className={styles.cardSub}>by total tokens</span>
          </header>
          {data.model_usage_7d.length === 0 ? (
            <p className={styles.empty}>No model usage recorded yet.</p>
          ) : (
            <table className={styles.modelTable}>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Calls</th>
                  <th>Input</th>
                  <th>Output</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {data.model_usage_7d.map((row) => (
                  <tr key={row.model}>
                    <td>{row.model}</td>
                    <td>{fmt.format(row.calls)}</td>
                    <td>{fmt.format(row.input_tokens)}</td>
                    <td>{fmt.format(row.output_tokens)}</td>
                    <td>{fmt.format(row.total_tokens)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </>
  );
};

// ---------------------------------------------------------------
// Infra tab — backed by GCP Cloud Monitoring (60s server cache)
// ---------------------------------------------------------------

const seriesFrom = (points, name) => [{
  name,
  points: (points || []).map((p) => ({ x: p.x, y: p.y })),
}];

const InfraPanel = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const payload = await observabilityService.getInfra();
        if (!cancelled) { setData(payload); setError(''); }
      } catch (err) {
        if (!cancelled) setError(parseApiError(err, 'Could not load infra metrics.'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    const id = setInterval(load, 60_000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  if (loading) return <Loader />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return null;

  return (
    <>
      {data.error ? (
        <div className={styles.errBanner}>
          GCP Cloud Monitoring is unavailable: {data.error}
        </div>
      ) : null}

      <p className={styles.cardSub}>
        Cloud Run · last {Math.round(data.window_seconds / 3600)}h ·
        refreshed {new Date(data.fetched_at).toLocaleTimeString()}
      </p>

      <div className={styles.twoCol}>
        <MetricCard
          title="Request rate"
          sub="Cloud Run requests per second"
          series={seriesFrom(data.cloud_run_request_count, 'Requests / sec')}
          ariaLabel="Cloud Run request rate"
        />
        <MetricCard
          title="5xx error rate"
          sub="Cloud Run 5xx responses per second"
          series={seriesFrom(data.cloud_run_5xx_count, '5xx / sec')}
          ariaLabel="Cloud Run 5xx rate"
        />
      </div>

      <div className={styles.twoCol}>
        <MetricCard
          title="Container instances"
          sub="Mean instance count (cold-start signal when frequently 0)"
          series={seriesFrom(data.cloud_run_instance_count, 'Instances')}
          ariaLabel="Cloud Run container instances"
        />
        <MetricCard
          title="p95 latency"
          sub="Cloud Run request latency, 95th percentile (ms)"
          series={seriesFrom(data.cloud_run_p95_latency_ms, 'p95 ms')}
          ariaLabel="Cloud Run p95 latency"
        />
      </div>
    </>
  );
};

// ---------------------------------------------------------------
// Shared bits
// ---------------------------------------------------------------

const Stat = ({ label, value, sub }) => (
  <article className={styles.stat}>
    <p className={styles.statLabel}>{label}</p>
    <p className={styles.statValue}>
      {typeof value === 'number' ? fmt.format(value) : value}
    </p>
    {sub ? <p className={styles.statSub}>{sub}</p> : null}
  </article>
);

const MetricCard = ({ title, sub, series, ariaLabel }) => {
  const hasData = (series[0]?.points || []).length > 0;
  return (
    <section className={styles.card}>
      <header className={styles.cardHead}>
        <h2 className={styles.cardTitle}>{title}</h2>
      </header>
      <p className={styles.cardSub}>{sub}</p>
      {hasData ? (
        <LineChart series={series} height={220} ariaLabel={ariaLabel} />
      ) : (
        <p className={styles.empty}>No data in this window.</p>
      )}
    </section>
  );
};

export default Observability;
