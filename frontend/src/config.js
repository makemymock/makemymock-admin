// Central app configuration. Services should pull values from here
// instead of reading `import.meta.env` directly.

const DEFAULT_API_BASE_URL = 'http://localhost:8001/api/v1';

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL;
