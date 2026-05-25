import { useCallback, useEffect, useMemo, useState } from 'react';
import { questionService } from '../../services/questionService';
import { parseApiError } from '../../utils/validators';
import Button from '../../components/common/Button/Button';
import SelectField from '../../components/common/SelectField/SelectField';
import InputField from '../../components/common/InputField/InputField';
import Loader from '../../components/common/Loader/Loader';
import ErrorMessage from '../../components/common/ErrorMessage/ErrorMessage';
import QuestionCard from '../../components/questions/QuestionCard';
import styles from './questions.module.css';

const PAGE_SIZE = 10;

const QUESTION_TYPES = [
  { value: 'single_correct', label: 'Single correct' },
  { value: 'multi_correct', label: 'Multi correct' },
  { value: 'integer', label: 'Integer' },
  { value: 'matching', label: 'Matching' },
  { value: 'passage', label: 'Passage' },
];

const DIFFICULTIES = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
];

const Questions = () => {
  const [catalog, setCatalog] = useState(null);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState('');

  const [filters, setFilters] = useState({
    subject: '',
    chapter: '',
    topic: '',
    question_type: '',
    difficulty: '',
    q: '',
  });
  const [searchInput, setSearchInput] = useState('');

  const [questions, setQuestions] = useState({ total: 0, items: [] });
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await questionService.getCatalog();
        if (!cancelled) setCatalog(data);
      } catch (err) {
        if (!cancelled) setCatalogError(parseApiError(err, 'Could not load catalog.'));
      } finally {
        if (!cancelled) setCatalogLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const subjects = useMemo(() => {
    if (!catalog) return [];
    return catalog.subjects.map((s) => ({
      value: s.name,
      label: `${s.name} (${s.question_count})`,
    }));
  }, [catalog]);

  const chapters = useMemo(() => {
    if (!catalog || !filters.subject) return [];
    const subj = catalog.subjects.find((s) => s.name === filters.subject);
    if (!subj) return [];
    return subj.chapters.map((c) => ({
      value: c.name,
      label: `${c.name} (${c.question_count})`,
    }));
  }, [catalog, filters.subject]);

  const topics = useMemo(() => {
    if (!catalog || !filters.subject || !filters.chapter) return [];
    const subj = catalog.subjects.find((s) => s.name === filters.subject);
    const chap = subj?.chapters.find((c) => c.name === filters.chapter);
    if (!chap) return [];
    return chap.topics.map((t) => ({
      value: t.name,
      label: `${t.name} (${t.question_count})`,
    }));
  }, [catalog, filters.subject, filters.chapter]);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await questionService.list({
        ...filters,
        page,
        page_size: PAGE_SIZE,
      });
      setQuestions({ total: data.total, items: data.items });
    } catch (err) {
      setError(parseApiError(err, 'Could not load questions.'));
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  // Refetch when filters or page change. We deliberately keep this as a
  // single effect — fewer race-condition surfaces than juggling multiple.
  useEffect(() => { load(); }, [load]);

  const onFilterChange = (key) => (e) => {
    const value = e.target.value;
    setFilters((prev) => {
      // Reset downstream filters when parents change so we never end up
      // with a stale topic for a different chapter.
      if (key === 'subject') return { ...prev, subject: value, chapter: '', topic: '' };
      if (key === 'chapter') return { ...prev, chapter: value, topic: '' };
      return { ...prev, [key]: value };
    });
    setPage(1);
  };

  const onSearchSubmit = (e) => {
    e.preventDefault();
    setFilters((prev) => ({ ...prev, q: searchInput.trim() }));
    setPage(1);
  };

  const clearAll = () => {
    setFilters({ subject: '', chapter: '', topic: '', question_type: '', difficulty: '', q: '' });
    setSearchInput('');
    setPage(1);
  };

  const totalPages = Math.max(1, Math.ceil(questions.total / PAGE_SIZE));

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Question explorer</h1>
          <p className={styles.subtitle}>
            Browse the question catalog. Correct options are highlighted in green,
            and solutions are shown when available.
          </p>
        </div>
        {catalog ? (
          <div className={styles.catalogBadge}>
            <strong>{catalog.total_questions.toLocaleString()}</strong> questions
          </div>
        ) : null}
      </header>

      {catalogError ? <ErrorMessage message={catalogError} /> : null}
      {catalogLoading ? <Loader label="Loading catalog…" /> : null}

      {catalog ? (
        <section className={styles.filters}>
          <SelectField
            label="Subject"
            value={filters.subject}
            onChange={onFilterChange('subject')}
            options={subjects}
            placeholder="All subjects"
          />
          <SelectField
            label="Chapter"
            value={filters.chapter}
            onChange={onFilterChange('chapter')}
            options={chapters}
            placeholder={filters.subject ? 'All chapters' : 'Select a subject first'}
            disabled={!filters.subject}
          />
          <SelectField
            label="Topic"
            value={filters.topic}
            onChange={onFilterChange('topic')}
            options={topics}
            placeholder={filters.chapter ? 'All topics' : 'Select a chapter first'}
            disabled={!filters.chapter}
          />
          <SelectField
            label="Type"
            value={filters.question_type}
            onChange={onFilterChange('question_type')}
            options={QUESTION_TYPES}
            placeholder="All types"
          />
          <SelectField
            label="Difficulty"
            value={filters.difficulty}
            onChange={onFilterChange('difficulty')}
            options={DIFFICULTIES}
            placeholder="Any difficulty"
          />

          <form className={styles.searchForm} onSubmit={onSearchSubmit} role="search">
            <InputField
              label="Search"
              placeholder="Substring in question text…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </form>

          <div className={styles.filterActions}>
            <Button variant="ghost" onClick={clearAll}>Clear filters</Button>
          </div>
        </section>
      ) : null}

      <header className={styles.resultHeader}>
        <p className={styles.resultCount}>
          {loading ? 'Loading…' : `${questions.total.toLocaleString()} matching questions`}
        </p>
        <div className={styles.pageControls}>
          <Button
            variant="ghost"
            disabled={page <= 1 || loading}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            ←
          </Button>
          <span className={styles.pageInfo}>
            {page} / {totalPages}
          </span>
          <Button
            variant="ghost"
            disabled={page >= totalPages || loading}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            →
          </Button>
        </div>
      </header>

      {error ? <ErrorMessage message={error} /> : null}

      <section className={styles.list}>
        {loading ? (
          <Loader />
        ) : questions.items.length === 0 ? (
          <p className={styles.empty}>
            No questions match these filters. Try widening the selection.
          </p>
        ) : (
          questions.items.map((q, idx) => (
            <QuestionCard
              key={q.id}
              question={q}
              index={(page - 1) * PAGE_SIZE + idx + 1}
            />
          ))
        )}
      </section>
    </div>
  );
};

export default Questions;
