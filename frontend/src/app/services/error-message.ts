import { HttpErrorResponse } from '@angular/common/http';

/**
 * Format a backend HTTP error as a CI-compliant German user-facing string.
 * Includes status + endpoint detail so the user can locate the failure in logs.
 */
export function formatBackendError(prefix: string, err: unknown): string {
  if (err instanceof HttpErrorResponse) {
    const status = err.status === 0 ? 'Backend nicht erreichbar' : `HTTP ${err.status}`;
    const detail = extractDetail(err);
    return detail ? `${prefix} (${status} — ${detail}).` : `${prefix} (${status}).`;
  }
  return `${prefix}.`;
}

function extractDetail(err: HttpErrorResponse): string | null {
  const body: unknown = err.error;
  if (!body) {
    return null;
  }
  if (typeof body === 'string') {
    return body;
  }
  if (typeof body === 'object' && 'error' in body) {
    const message = (body as { error?: unknown }).error;
    if (typeof message === 'string') {
      return message;
    }
  }
  return null;
}
