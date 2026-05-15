import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'oc-card',
  standalone: true,
  template: `
    @if (title) {
      <header class="oc-card__header">
        <h3 class="oc-card__title">{{ title }}</h3>
        @if (subtitle) {
          <p class="oc-card__subtitle">{{ subtitle }}</p>
        }
      </header>
    }
    <div class="oc-card__body">
      <ng-content />
    </div>
  `,
  styleUrl: './card.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: { class: 'oc-card' },
})
export class OcCardComponent {
  @Input() title?: string;
  @Input() subtitle?: string;
}
