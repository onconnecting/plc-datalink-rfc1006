import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { DIALOG_DATA, DialogRef } from '@angular/cdk/dialog';
import { OcButtonDirective } from './button.directive';

export interface OcConfirmDialogData {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: 'danger' | 'primary';
}

@Component({
  selector: 'oc-confirm-dialog',
  standalone: true,
  imports: [OcButtonDirective],
  templateUrl: './confirm-dialog.component.html',
  styleUrl: './confirm-dialog.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OcConfirmDialogComponent {
  protected readonly data = inject<OcConfirmDialogData>(DIALOG_DATA);
  private readonly ref = inject<DialogRef<boolean>>(DialogRef);

  protected readonly confirmLabel = this.data.confirmLabel ?? 'Bestätigen';
  protected readonly cancelLabel = this.data.cancelLabel ?? 'Abbrechen';
  protected readonly confirmVariant: 'danger' | 'primary' = this.data.tone ?? 'primary';

  confirm(): void {
    this.ref.close(true);
  }

  cancel(): void {
    this.ref.close(false);
  }
}
