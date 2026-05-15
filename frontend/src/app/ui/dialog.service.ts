import { Injectable, inject } from '@angular/core';
import { Dialog } from '@angular/cdk/dialog';
import { firstValueFrom } from 'rxjs';
import { OcConfirmDialogComponent, OcConfirmDialogData } from './confirm-dialog.component';

@Injectable({ providedIn: 'root' })
export class DialogService {
  private readonly dialog = inject(Dialog);

  async confirm(data: OcConfirmDialogData): Promise<boolean> {
    const ref = this.dialog.open<boolean>(OcConfirmDialogComponent, {
      data,
      disableClose: false,
      hasBackdrop: true,
      backdropClass: 'oc-dialog__backdrop',
      panelClass: 'oc-dialog__panel',
      autoFocus: 'first-tabbable',
    });
    return (await firstValueFrom(ref.closed)) ?? false;
  }
}
