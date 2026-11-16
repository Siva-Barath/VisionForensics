export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export function extractApiError(err: unknown): string {
  if (typeof err === 'object' && err !== null) {
    const e = err as Record<string, unknown>;
    if (e.response && typeof e.response === 'object') {
      const res = e.response as Record<string, unknown>;
      if (res.data && typeof res.data === 'object') {
        const data = res.data as Record<string, unknown>;
        if (typeof data.error === 'string') return data.error;
        if (typeof data.detail === 'string') return data.detail;
      }
    }
    if (typeof e.message === 'string') return e.message;
  }
  return 'An unexpected error occurred.';
}
