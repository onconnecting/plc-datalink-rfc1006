import { ChangeDetectionStrategy, Component, Input, computed, signal } from '@angular/core';

export type OcStatusTone = 'success' | 'warning' | 'error' | 'neutral';

@Component({
  selector: 'oc-status-pill',
  standalone: true,
  template: `
    <span class="oc-status-pill__dot" [attr.aria-hidden]="true"></span>
    <span class="oc-status-pill__label">{{ label }}</span>
  `,
  styleUrl: './status-pill.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    class: 'oc-status-pill',
    '[class.oc-status-pill--success]': 'isTone("success")',
    '[class.oc-status-pill--warning]': 'isTone("warning")',
    '[class.oc-status-pill--error]': 'isTone("error")',
    '[class.oc-status-pill--neutral]': 'isTone("neutral")',
    role: 'status',
  },
})
export class OcStatusPillComponent {
  private readonly tone$ = signal<OcStatusTone>('neutral');

  @Input({ required: true }) label!: string;

  @Input()
  set tone(value: OcStatusTone) {
    this.tone$.set(value);
  }
  get tone(): OcStatusTone {
    return this.tone$();
  }

  protected readonly resolvedTone = computed(() => this.tone$());

  isTone(value: OcStatusTone): boolean {
    return this.resolvedTone() === value;
  }
}
