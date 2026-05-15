import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

let uid = 0;

@Component({
  selector: 'oc-field',
  standalone: true,
  templateUrl: './field.component.html',
  styleUrl: './field.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OcFieldComponent {
  @Input({ required: true }) label!: string;
  @Input() help?: string;
  @Input() error?: string | null;
  @Input() inputId = `oc-field-${++uid}`;
  @Input() mono = false;
}
