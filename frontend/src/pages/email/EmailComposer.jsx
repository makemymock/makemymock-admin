import { useState } from 'react';
import { emailService } from '../../services/emailService';
import { userService } from '../../services/userService';
import {
  parseApiError,
  parseEmailListInput,
  validateEmailList,
  validateNonEmpty,
} from '../../utils/validators';
import Button from '../../components/common/Button/Button';
import InputField from '../../components/common/InputField/InputField';
import ErrorMessage from '../../components/common/ErrorMessage/ErrorMessage';
import styles from './email.module.css';

const EmailComposer = () => {
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [recipientsRaw, setRecipientsRaw] = useState('');
  const [useTemplate, setUseTemplate] = useState(true);

  const [errors, setErrors] = useState({ subject: '', body: '', recipients: '' });
  const [formError, setFormError] = useState('');
  const [previewHtml, setPreviewHtml] = useState('');

  const [sending, setSending] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [loadingAll, setLoadingAll] = useState(false);
  const [result, setResult] = useState(null);

  const recipientList = parseEmailListInput(recipientsRaw);

  const handlePreview = async () => {
    const subjErr = validateNonEmpty(subject, 'Subject');
    const bodyErr = validateNonEmpty(body, 'Body');
    setErrors((prev) => ({ ...prev, subject: subjErr, body: bodyErr }));
    if (subjErr || bodyErr) return;

    setPreviewing(true);
    setFormError('');
    try {
      const res = await emailService.preview({
        subject,
        body,
        use_template: useTemplate,
        preserve_line_breaks: true,
      });
      setPreviewHtml(res.html);
    } catch (err) {
      setFormError(parseApiError(err, 'Could not render preview.'));
    } finally {
      setPreviewing(false);
    }
  };

  const handleLoadAll = async () => {
    setLoadingAll(true);
    setFormError('');
    try {
      const res = await userService.allEmails();
      setRecipientsRaw(res.emails.join('\n'));
    } catch (err) {
      setFormError(parseApiError(err, 'Could not load user emails.'));
    } finally {
      setLoadingAll(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    const subjErr = validateNonEmpty(subject, 'Subject');
    const bodyErr = validateNonEmpty(body, 'Body');
    const recErr = validateEmailList(recipientList);
    setErrors({ subject: subjErr, body: bodyErr, recipients: recErr });
    if (subjErr || bodyErr || recErr) return;

    if (!window.confirm(
      `Send "${subject}" to ${recipientList.length} recipient${recipientList.length === 1 ? '' : 's'}?`
    )) return;

    setSending(true);
    setFormError('');
    setResult(null);
    try {
      const res = await emailService.send({
        subject,
        body,
        recipients: recipientList,
        use_template: useTemplate,
        preserve_line_breaks: true,
      });
      setResult(res);
    } catch (err) {
      setFormError(parseApiError(err, 'Send failed.'));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Promotional email</h1>
        <p className={styles.subtitle}>
          Compose a message and dispatch it to a list of recipients. Each
          recipient gets their own copy — addresses are never visible to other
          recipients.
        </p>
      </header>

      <form className={styles.layout} onSubmit={handleSend} noValidate>
        <section className={styles.formColumn}>
          <InputField
            label="Subject"
            value={subject}
            onChange={(e) => {
              setSubject(e.target.value);
              if (errors.subject) setErrors((p) => ({ ...p, subject: '' }));
            }}
            placeholder="A short, compelling subject line"
            error={errors.subject}
            maxLength={200}
          />

          <div className={styles.field}>
            <label className={styles.label}>Body</label>
            <textarea
              className={`${styles.textarea} ${errors.body ? styles.textareaError : ''}`}
              value={body}
              onChange={(e) => {
                setBody(e.target.value);
                if (errors.body) setErrors((p) => ({ ...p, body: '' }));
              }}
              placeholder={useTemplate
                ? "Write your message in plain text. Blank lines become paragraphs.\n\nA second paragraph here…"
                : "Paste raw HTML — sent verbatim."}
              rows={12}
            />
            {errors.body ? (
              <p role="alert" className={styles.errorText}>{errors.body}</p>
            ) : null}

            <label className={styles.checkboxRow}>
              <input
                type="checkbox"
                checked={useTemplate}
                onChange={(e) => setUseTemplate(e.target.checked)}
              />
              <span>Wrap in branded template</span>
            </label>
          </div>

          <div className={styles.field}>
            <label className={styles.label}>
              Recipients ({recipientList.length})
            </label>
            <textarea
              className={`${styles.textarea} ${errors.recipients ? styles.textareaError : ''}`}
              value={recipientsRaw}
              onChange={(e) => {
                setRecipientsRaw(e.target.value);
                if (errors.recipients) setErrors((p) => ({ ...p, recipients: '' }));
              }}
              placeholder="alice@example.com, bob@example.com&#10;or one per line"
              rows={6}
            />
            {errors.recipients ? (
              <p role="alert" className={styles.errorText}>{errors.recipients}</p>
            ) : null}
            <div className={styles.recipientsActions}>
              <Button
                type="button"
                variant="outline"
                onClick={handleLoadAll}
                loading={loadingAll}
              >
                Load all users
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setRecipientsRaw('')}
                disabled={!recipientsRaw}
              >
                Clear list
              </Button>
            </div>
          </div>

          {formError ? <ErrorMessage message={formError} /> : null}

          <div className={styles.actions}>
            <Button
              type="button"
              variant="outline"
              onClick={handlePreview}
              loading={previewing}
            >
              Preview
            </Button>
            <Button type="submit" variant="primary" loading={sending}>
              Send to {recipientList.length || 0}
            </Button>
          </div>

          {result ? (
            <div className={`${styles.resultCard} ${result.failed ? styles.resultMixed : styles.resultOk}`}>
              <strong>Sent:</strong> {result.sent} / {result.requested}.{' '}
              {result.failed > 0 ? <strong>{result.failed} failed.</strong> : null}
              {result.failed > 0 ? (
                <details className={styles.resultDetails}>
                  <summary>Show failures</summary>
                  <ul>
                    {result.results
                      .filter((r) => r.status === 'failed')
                      .map((r) => (
                        <li key={r.email}>
                          <code>{r.email}</code>: {r.error || 'unknown error'}
                        </li>
                      ))}
                  </ul>
                </details>
              ) : null}
            </div>
          ) : null}
        </section>

        <aside className={styles.previewColumn}>
          <header className={styles.previewHeader}>
            <h2 className={styles.previewTitle}>Live preview</h2>
            <p className={styles.previewSubtitle}>
              Click <strong>Preview</strong> to render with the template.
            </p>
          </header>
          <div className={styles.previewFrame}>
            {previewHtml ? (
              <iframe
                title="Email preview"
                srcDoc={previewHtml}
                className={styles.previewIframe}
                sandbox=""
              />
            ) : (
              <div className={styles.previewEmpty}>
                <p>Preview appears here.</p>
              </div>
            )}
          </div>
        </aside>
      </form>
    </div>
  );
};

export default EmailComposer;
