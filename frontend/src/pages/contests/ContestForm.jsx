import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Button from '../../components/common/Button/Button';
import ErrorMessage from '../../components/common/ErrorMessage/ErrorMessage';
import Loader from '../../components/common/Loader/Loader';
import MarkdownText from '../../components/common/MarkdownText/MarkdownText';
import { contestService } from '../../services/contestService';
import { questionService } from '../../services/questionService';
import { parseApiError } from '../../utils/validators';
import styles from './contests.module.css';

const DEFAULT_MARKING = { correct: 4, wrong: -1, unattempted: 0 };

const minutesToSeconds = (m) => Math.round(Number(m) * 60);
const secondsToMinutes = (s) => Math.round(Number(s) / 60);

// `<input type="datetime-local">` returns / accepts strings WITHOUT a
// timezone marker. We treat them as the user's local time, convert to
// UTC for the server, and back again for prefill.
const toLocalInputValue = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
};

const fromLocalInputValue = (str) => {
  if (!str) return '';
  // Treat as local time; toISOString() yields UTC.
  return new Date(str).toISOString();
};

const substituteRules = (template, ctx) => {
  if (!template) return '';
  return template
    .replaceAll('{question_count}', String(ctx.questionCount || 0))
    .replaceAll('{duration_minutes}', String(ctx.durationMinutes || 0))
    .replaceAll('{marks_correct}', `+${ctx.marking.correct}`)
    .replaceAll('{marks_wrong}', String(ctx.marking.wrong))
    .replaceAll('{marks_unattempted}', String(ctx.marking.unattempted));
};

// -------------- picker --------------
const QuestionPicker = ({ selectedIds, onToggle }) => {
  const [filters, setFilters] = useState({
    subject: '', chapter: '', topic: '', question_type: '', difficulty: '', q: '',
  });
  const [data, setData] = useState({ items: [], total: 0 });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [catalog, setCatalog] = useState(null);

  useEffect(() => {
    questionService.getCatalog().then(setCatalog).catch(() => setCatalog(null));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await questionService.list({
        ...filters, page, page_size: 25,
      });
      setData(res);
    } catch {
      setData({ items: [], total: 0 });
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => { load(); }, [load]);

  const onFilter = (key) => (e) => {
    const value = e.target.value;
    setFilters((f) => ({ ...f, [key]: value }));
    setPage(1);
  };

  const subjects = catalog?.subjects || [];
  const chapters = useMemo(
    () => subjects.find((s) => s.name === filters.subject)?.chapters || [],
    [subjects, filters.subject],
  );
  const topics = useMemo(
    () => chapters.find((c) => c.name === filters.chapter)?.topics || [],
    [chapters, filters.chapter],
  );

  const total = data.total;
  const totalPages = Math.max(1, Math.ceil(total / 25));

  // v1 limitation: contests skip passage-type questions (no UI / grader
  // path yet). Hide them in the picker so the admin can't add what we
  // can't grade.
  const visibleItems = (data.items || []).filter(
    (q) => q.question_type !== 'passage',
  );

  return (
    <>
      <div className={styles.pickerFilters}>
        <select
          className={styles.select}
          value={filters.subject}
          onChange={(e) => {
            const v = e.target.value;
            setFilters((f) => ({ ...f, subject: v, chapter: '', topic: '' }));
            setPage(1);
          }}
        >
          <option value="">All subjects</option>
          {subjects.map((s) => (
            <option key={s.name} value={s.name}>{s.name}</option>
          ))}
        </select>
        <select
          className={styles.select}
          value={filters.chapter}
          onChange={(e) => {
            const v = e.target.value;
            setFilters((f) => ({ ...f, chapter: v, topic: '' }));
            setPage(1);
          }}
          disabled={!filters.subject}
        >
          <option value="">All chapters</option>
          {chapters.map((c) => (
            <option key={c.name} value={c.name}>{c.name}</option>
          ))}
        </select>
        <select
          className={styles.select}
          value={filters.topic}
          onChange={onFilter('topic')}
          disabled={!filters.chapter}
        >
          <option value="">All topics</option>
          {topics.map((t) => (
            <option key={t.name} value={t.name}>{t.name}</option>
          ))}
        </select>
        <select
          className={styles.select}
          value={filters.difficulty}
          onChange={onFilter('difficulty')}
        >
          <option value="">All difficulty</option>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
      </div>

      <div className={styles.pickerFilters}>
        <select
          className={styles.select}
          value={filters.question_type}
          onChange={onFilter('question_type')}
        >
          <option value="">All types</option>
          <option value="single_correct">Single correct</option>
          <option value="multi_correct">Multi correct</option>
          <option value="integer">Integer</option>
          <option value="matching">Matching</option>
        </select>
        <input
          className={styles.input}
          placeholder="Search question text…"
          value={filters.q}
          onChange={onFilter('q')}
        />
      </div>

      <div className={styles.pickerList}>
        {loading ? (
          <Loader />
        ) : visibleItems.length === 0 ? (
          <p style={{ padding: 16, color: 'var(--color-text-subtle)' }}>
            No questions match these filters.
          </p>
        ) : visibleItems.map((q) => {
          const checked = selectedIds.includes(q.id);
          return (
            <label key={q.id} className={styles.pickerRow}>
              <input
                type="checkbox"
                className={styles.pickerCheckbox}
                checked={checked}
                onChange={() => onToggle(q)}
              />
              <div className={styles.pickerMeta}>
                <p className={styles.pickerCrumb}>
                  {q.subject} › {q.chapter} › {q.topic}
                </p>
                {/* `inline` so the 2-line clamp on .pickerText holds —
                    block-paragraph rendering would break the clamp. */}
                <div className={styles.pickerText}>
                  <MarkdownText text={q.question_text} inline />
                </div>
                <div className={styles.pickerTags}>
                  <span className={styles.pickerTag}>
                    {q.question_type?.replace('_', ' ')}
                  </span>
                  {q.difficulty ? (
                    <span className={styles.pickerTag}>{q.difficulty}</span>
                  ) : null}
                </div>
              </div>
            </label>
          );
        })}
      </div>

      <div className={styles.helpRow}>
        <span>{total} matching · page {page} of {totalPages}</span>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button
            type="button"
            variant="ghost"
            disabled={page <= 1 || loading}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            ← Prev
          </Button>
          <Button
            type="button"
            variant="ghost"
            disabled={page >= totalPages || loading}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            Next →
          </Button>
        </div>
      </div>
    </>
  );
};

// -------------- main form --------------
const ContestForm = () => {
  const { contestId } = useParams();
  const navigate = useNavigate();
  const editing = Boolean(contestId);

  const [loading, setLoading] = useState(editing);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [defaultTemplate, setDefaultTemplate] = useState('');

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [startLocal, setStartLocal] = useState('');
  const [durationMinutes, setDurationMinutes] = useState(30);
  const [marking, setMarking] = useState(DEFAULT_MARKING);
  const [rules, setRules] = useState('');
  const [selected, setSelected] = useState([]); // [{id, question_text, question_type, ...}]

  // Prefill rules with the default template on first mount (create only).
  useEffect(() => {
    contestService
      .defaultRules()
      .then(({ rules: r }) => setDefaultTemplate(r))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!editing) return;
    setLoading(true);
    contestService
      .get(contestId)
      .then((c) => {
        setTitle(c.title || '');
        setDescription(c.description || '');
        setStartLocal(toLocalInputValue(c.start_time));
        setDurationMinutes(secondsToMinutes(c.duration_seconds));
        setMarking(c.marking || DEFAULT_MARKING);
        setRules(c.rules || '');
        setSelected(c.questions || []);
      })
      .catch((err) => setError(parseApiError(err, 'Could not load contest.')))
      .finally(() => setLoading(false));
  }, [editing, contestId]);

  // Prefill rules from template once we know the template (create mode only).
  useEffect(() => {
    if (editing || !defaultTemplate || rules) return;
    setRules(defaultTemplate);
  }, [defaultTemplate, editing, rules]);

  const onToggle = useCallback((q) => {
    setSelected((cur) => {
      const exists = cur.find((x) => x.id === q.id);
      if (exists) return cur.filter((x) => x.id !== q.id);
      return [...cur, q];
    });
  }, []);

  const onRemove = (id) =>
    setSelected((cur) => cur.filter((x) => x.id !== id));

  const onResetRules = () => {
    const substituted = substituteRules(defaultTemplate, {
      questionCount: selected.length,
      durationMinutes,
      marking,
    });
    setRules(substituted);
  };

  const onSave = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      const payload = {
        title: title.trim(),
        description: description.trim(),
        rules: rules,
        start_time: fromLocalInputValue(startLocal),
        duration_seconds: minutesToSeconds(durationMinutes),
        question_ids: selected.map((q) => q.id),
        marking: {
          correct: Number(marking.correct),
          wrong: Number(marking.wrong),
          unattempted: Number(marking.unattempted),
        },
      };
      if (editing) {
        await contestService.update(contestId, payload);
      } else {
        await contestService.create(payload);
      }
      navigate('/contests');
    } catch (err) {
      setError(parseApiError(err, 'Could not save contest.'));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Loader />;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>{editing ? 'Edit contest' : 'New contest'}</h1>
          <p className={styles.subtitle}>
            {editing
              ? 'Locked once the contest starts.'
              : 'Schedule a contest — students see it in their Compete tab automatically.'}
          </p>
        </div>
        <div className={styles.headerActions}>
          <Button variant="ghost" type="button" onClick={() => navigate('/contests')}>
            Cancel
          </Button>
        </div>
      </header>

      {error ? <ErrorMessage message={error} /> : null}

      <form className={styles.form} onSubmit={onSave}>
        <div className={styles.formMain}>
          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Basics</h2>
            <div className={styles.fieldGrid}>
              <div className="full">
                <label className={styles.label}>Title</label>
                <input
                  className={styles.input}
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  placeholder="Weekly JEE Math Sprint"
                />
              </div>
              <div className="full">
                <label className={styles.label}>Short description</label>
                <input
                  className={styles.input}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="One-liner shown in the contest card"
                />
              </div>
              <div>
                <label className={styles.label}>Start time (your local time)</label>
                <input
                  type="datetime-local"
                  className={styles.input}
                  value={startLocal}
                  onChange={(e) => setStartLocal(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className={styles.label}>Duration (minutes)</label>
                <input
                  type="number"
                  className={styles.input}
                  value={durationMinutes}
                  min={1}
                  max={360}
                  onChange={(e) => setDurationMinutes(Number(e.target.value))}
                  required
                />
              </div>
            </div>
          </section>

          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Marking scheme</h2>
            <div className={styles.fieldGrid}>
              <div>
                <label className={styles.label}>Correct (+)</label>
                <input
                  type="number"
                  className={styles.input}
                  value={marking.correct}
                  onChange={(e) => setMarking((m) => ({ ...m, correct: e.target.value }))}
                  step="0.5"
                />
              </div>
              <div>
                <label className={styles.label}>Wrong (−)</label>
                <input
                  type="number"
                  className={styles.input}
                  value={marking.wrong}
                  onChange={(e) => setMarking((m) => ({ ...m, wrong: e.target.value }))}
                  step="0.5"
                />
              </div>
              <div>
                <label className={styles.label}>Unattempted</label>
                <input
                  type="number"
                  className={styles.input}
                  value={marking.unattempted}
                  onChange={(e) => setMarking((m) => ({ ...m, unattempted: e.target.value }))}
                  step="0.5"
                />
              </div>
              <div>
                <label className={styles.label}>Max score</label>
                <input
                  className={styles.input}
                  value={(Number(marking.correct) || 0) * selected.length}
                  readOnly
                />
              </div>
            </div>
          </section>

          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Pick questions</h2>
            <p className={styles.cardHint}>
              Passage-type questions are not yet supported in contests. Pick
              from single-correct, multi-correct, integer, and matching.
            </p>
            <QuestionPicker selectedIds={selected.map((q) => q.id)} onToggle={onToggle} />
          </section>

          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Rules & regulations (Markdown)</h2>
            <div className={styles.helpRow}>
              <span>
                Tokens like <code>{'{question_count}'}</code>, <code>{'{duration_minutes}'}</code>,
                {' '}<code>{'{marks_correct}'}</code>, <code>{'{marks_wrong}'}</code>,
                {' '}<code>{'{marks_unattempted}'}</code> are substituted live here.
              </span>
              <button type="button" className={styles.linkButton} onClick={onResetRules}>
                Reset to default
              </button>
            </div>
            <textarea
              className={styles.textarea}
              value={rules}
              onChange={(e) => setRules(e.target.value)}
              required
            />
          </section>
        </div>

        <aside className={styles.formSide}>
          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Summary</h2>
            <dl className={styles.summaryRow}>
              <dt>Questions</dt><dd>{selected.length}</dd>
              <dt>Duration</dt><dd>{durationMinutes} min</dd>
              <dt>Marking</dt>
              <dd>+{marking.correct} / {marking.wrong} / {marking.unattempted}</dd>
              <dt>Starts</dt>
              <dd>{startLocal ? new Date(startLocal).toLocaleString() : '—'}</dd>
            </dl>
          </section>

          <section className={styles.card}>
            <h2 className={styles.cardTitle}>Selected ({selected.length})</h2>
            {selected.length === 0 ? (
              <p className={styles.cardHint}>Pick questions from the panel on the left.</p>
            ) : (
              <ol className={styles.selectedList}>
                {selected.map((q, i) => (
                  <li key={q.id} className={styles.selectedRow}>
                    <div className={styles.pickerMeta}>
                      <span className={styles.selectedIndex}>Q{i + 1}</span>
                      <p className={styles.pickerCrumb}>
                        {q.subject} › {q.topic}
                      </p>
                      <div className={styles.pickerText}>
                        <MarkdownText text={q.question_text} inline />
                      </div>
                    </div>
                    <button
                      type="button"
                      className={styles.removeBtn}
                      onClick={() => onRemove(q.id)}
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ol>
            )}
          </section>

          <div className={styles.actions}>
            <Button type="submit" variant="primary" loading={saving}>
              {editing ? 'Save changes' : 'Schedule contest'}
            </Button>
          </div>
        </aside>
      </form>
    </div>
  );
};

export default ContestForm;
