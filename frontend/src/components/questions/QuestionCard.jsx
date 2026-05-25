import React from 'react';
import MarkdownText from '../common/MarkdownText/MarkdownText';
import styles from './QuestionCard.module.css';

const TYPE_LABEL = {
  single_correct: 'Single correct',
  multi_correct: 'Multi correct',
  integer: 'Integer',
  matching: 'Matching',
  passage: 'Passage',
};

const QuestionCard = ({ question, index }) => {
  if (!question) return null;
  return (
    <article className={styles.card}>
      <header className={styles.header}>
        <span className={styles.indexBadge}>Q{index}</span>
        <div className={styles.metaRow}>
          <span className={styles.metaPill}>
            {TYPE_LABEL[question.question_type] || question.question_type}
          </span>
          {question.difficulty ? (
            <span
              className={`${styles.metaPill} ${
                styles[`diff_${question.difficulty}`] || ''
              }`}
            >
              {question.difficulty}
            </span>
          ) : null}
          <span className={styles.crumb}>
            {question.subject}
            <span className={styles.sep}>/</span>
            {question.chapter}
            <span className={styles.sep}>/</span>
            {question.topic}
          </span>
        </div>
      </header>

      {/* Passage block */}
      {question.passage_text ? (
        <section className={styles.passageBlock}>
          <h3 className={styles.passageTitle}>Passage</h3>
          <MarkdownText text={question.passage_text} />
          {question.passage_image ? (
            <img src={question.passage_image} alt="" className={styles.image} />
          ) : null}
        </section>
      ) : null}

      {/* Stem */}
      <section className={styles.stem}>
        {question.question_text ? (
          <MarkdownText text={question.question_text} />
        ) : (
          <p>
            <em>(no stem)</em>
          </p>
        )}
        {question.question_image ? (
          <img src={question.question_image} alt="" className={styles.image} />
        ) : null}
      </section>

      {/* Options */}
      {question.options && question.options.length > 0 ? (
        <section className={styles.options}>
          {question.options.map((opt) => (
            <div
              key={opt.key}
              className={`${styles.option} ${
                opt.is_correct ? styles.optionCorrect : ''
              }`}
            >
              <span className={styles.optionKey}>{opt.key}</span>
              <span className={styles.optionText}>
                <MarkdownText text={opt.text} inline />
                {opt.image ? (
                  <img src={opt.image} alt="" className={styles.optionImage} />
                ) : null}
              </span>
              {opt.is_correct ? (
                <span className={styles.optionCheck}>✓ Correct</span>
              ) : null}
            </div>
          ))}
        </section>
      ) : null}

      {/* Integer answer */}
      {question.question_type === 'integer' &&
      question.correct_integer != null &&
      question.correct_integer !== '' ? (
        <section className={styles.integerBlock}>
          <span className={styles.label}>Correct answer:</span>
          <span className={styles.integerValue}>
            {String(question.correct_integer)}
          </span>
        </section>
      ) : null}

      {/* Matching */}
      {question.question_type === 'matching' &&
      (question.matching_left.length > 0 ||
        question.matching_right.length > 0) ? (
        <section className={styles.matching}>
          <div className={styles.matchingCol}>
            <h4 className={styles.matchingTitle}>Left column</h4>
            <ul className={styles.matchingList}>
              {question.matching_left.map((item) => (
                <li key={item.key}>
                  <span className={styles.matchingKey}>{item.key}</span>{' '}
                  <MarkdownText text={item.text} inline />
                </li>
              ))}
            </ul>
          </div>
          <div className={styles.matchingCol}>
            <h4 className={styles.matchingTitle}>Right column</h4>
            <ul className={styles.matchingList}>
              {question.matching_right.map((item) => (
                <li key={item.key}>
                  <span className={styles.matchingKey}>{item.key}</span>{' '}
                  <MarkdownText text={item.text} inline />
                </li>
              ))}
            </ul>
          </div>
          {question.matching_correct &&
          Object.keys(question.matching_correct).length > 0 ? (
            <div className={styles.matchingPairs}>
              <h4 className={styles.matchingTitle}>Correct mapping</h4>
              <ul className={styles.pairList}>
                {Object.entries(question.matching_correct).map(([l, r]) => (
                  <li key={l} className={styles.pairItem}>
                    <span className={styles.pairLeft}>{l}</span>
                    <span className={styles.pairArrow}>→</span>
                    <span className={styles.pairRight}>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      ) : null}

      {/* Sub-questions (passage) */}
      {question.sub_questions && question.sub_questions.length > 0 ? (
        <section className={styles.subSection}>
          <h3 className={styles.subSectionTitle}>Sub-questions</h3>
          {question.sub_questions.map((sub, idx) => (
            <QuestionCard
              key={sub.id || idx}
              question={sub}
              index={`${index}.${idx + 1}`}
            />
          ))}
        </section>
      ) : null}

      {/* Solution */}
      {question.solution_text || question.solution_image ? (
        <section className={styles.solution}>
          <h3 className={styles.solutionTitle}>Solution</h3>
          {question.solution_text ? (
            <MarkdownText text={question.solution_text} />
          ) : null}
          {question.solution_image ? (
            <img src={question.solution_image} alt="" className={styles.image} />
          ) : null}
        </section>
      ) : null}
    </article>
  );
};

export default QuestionCard;
