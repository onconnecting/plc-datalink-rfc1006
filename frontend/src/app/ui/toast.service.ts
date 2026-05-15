import { Injectable, signal } from '@angular/core';

export type OcToastTone = 'success' | 'warning' | 'error' | 'info';

export interface OcToast {
  id: number;
  tone: OcToastTone;
  message: string;
}

const DEFAULT_DURATION_MS: Record<OcToastTone, number> = {
  success: 6000,
  info: 6000,
  warning: 8000,
  error: 10000,
};

@Injectable({ providedIn: 'root' })
export class ToastService {
  private readonly _toasts = signal<OcToast[]>([]);
  readonly toasts = this._toasts.asReadonly();
  private nextId = 1;

  success(message: string): void {
    this.push('success', message);
  }

  warning(message: string): void {
    this.push('warning', message);
  }

  error(message: string): void {
    this.push('error', message);
  }

  info(message: string): void {
    this.push('info', message);
  }

  dismiss(id: number): void {
    this._toasts.update((list) => list.filter((t) => t.id !== id));
  }

  private push(tone: OcToastTone, message: string): void {
    const id = this.nextId++;
    this._toasts.update((list) => [...list, { id, tone, message }]);
    setTimeout(() => this.dismiss(id), DEFAULT_DURATION_MS[tone]);
  }
}
