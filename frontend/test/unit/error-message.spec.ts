import { HttpErrorResponse } from '@angular/common/http';
import { formatBackendError } from '../../src/app/services/error-message';

describe('formatBackendError', () => {
  it('handles non-HTTP errors by appending a period only', () => {
    expect(formatBackendError('Etwas ging schief', new Error('boom'))).toBe('Etwas ging schief.');
  });

  it('reports "Backend nicht erreichbar" for status 0 (network down)', () => {
    const err = new HttpErrorResponse({ status: 0 });
    expect(formatBackendError('Konfiguration nicht geladen', err)).toBe(
      'Konfiguration nicht geladen (Backend nicht erreichbar).',
    );
  });

  it('appends the HTTP status when no body detail is present', () => {
    const err = new HttpErrorResponse({ status: 404, statusText: 'Not Found' });
    expect(formatBackendError('Konfiguration nicht geladen', err)).toBe(
      'Konfiguration nicht geladen (HTTP 404).',
    );
  });

  it('appends a string body as detail', () => {
    const err = new HttpErrorResponse({ status: 500, error: 'kaboom' });
    expect(formatBackendError('Update fehlgeschlagen', err)).toBe(
      'Update fehlgeschlagen (HTTP 500 — kaboom).',
    );
  });

  it('appends body.error when the body is a JSON object with an error string', () => {
    const err = new HttpErrorResponse({ status: 409, error: { error: 'rev conflict' } });
    expect(formatBackendError('Konflikt', err)).toBe('Konflikt (HTTP 409 — rev conflict).');
  });

  it('omits detail when body.error is not a string', () => {
    const err = new HttpErrorResponse({ status: 500, error: { error: { nested: true } } });
    expect(formatBackendError('Update fehlgeschlagen', err)).toBe('Update fehlgeschlagen (HTTP 500).');
  });
});
