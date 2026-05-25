const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(email) {
  if (!email || !email.trim()) return 'Email is required.';
  if (!EMAIL_REGEX.test(email.trim())) return 'Please enter a valid email address.';
  return '';
}

export function validateLoginPassword(password) {
  if (!password) return 'Password is required.';
  return '';
}

export function validateNonEmpty(value, label = 'This field') {
  if (!value || !String(value).trim()) return `${label} is required.`;
  return '';
}

export function validateEmailList(rawList) {
  if (!Array.isArray(rawList) || rawList.length === 0) {
    return 'Add at least one recipient.';
  }
  const bad = rawList.find((e) => !EMAIL_REGEX.test(String(e).trim()));
  if (bad) return `"${bad}" is not a valid email address.`;
  return '';
}

export function parseEmailListInput(input) {
  // Accept commas, semicolons, whitespace, and newlines as separators —
  // admins typically paste from a spreadsheet column.
  if (!input) return [];
  return input
    .split(/[\s,;]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export function parseApiError(error, fallback = 'Something went wrong. Please try again.') {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (typeof first === 'string') return first;
    if (first?.msg) return first.msg;
  }
  if (error?.message && error.message !== 'Network Error') return error.message;
  if (error?.message === 'Network Error') {
    return 'Unable to reach the server. Check your connection and try again.';
  }
  return fallback;
}
