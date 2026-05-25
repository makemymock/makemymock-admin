import { memo, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import styles from './MarkdownText.module.css';

const REMARK_PLUGINS = [remarkGfm, remarkMath];
const REHYPE_PLUGINS = [rehypeKatex];

// Some bbd_db rows store LaTeX with single-dollar inline (`$x^2$`) and
// double-dollar block (`$$...$$`), others use \( ... \) and \[ ... \].
// remark-math's defaults handle both. We also normalise Windows newlines.
function normalize(text) {
  if (text == null) return '';
  return String(text).replace(/\r\n?/g, '\n');
}

// In inline contexts we flatten paragraphs so the text doesn't generate
// <p> blocks with vertical margins.
const INLINE_COMPONENTS = {
  p: ({ children }) => <>{children}</>,
};

const MarkdownText = ({ text, inline = false, className = '' }) => {
  const value = useMemo(() => normalize(text), [text]);
  if (!value) return null;
  const Tag = inline ? 'span' : 'div';
  return (
    <Tag className={`${styles.root} ${inline ? styles.inline : ''} ${className}`}>
      <ReactMarkdown
        remarkPlugins={REMARK_PLUGINS}
        rehypePlugins={REHYPE_PLUGINS}
        components={inline ? INLINE_COMPONENTS : undefined}
      >
        {value}
      </ReactMarkdown>
    </Tag>
  );
};

export default memo(MarkdownText);
