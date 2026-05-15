import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ToastService, OcToast } from './toast.service';

@Component({
  selector: 'oc-toast-host',
  standalone: true,
  templateUrl: './toast-host.component.html',
  styleUrl: './toast-host.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OcToastHostComponent {
  private readonly toastService = inject(ToastService);
  protected readonly toasts = this.toastService.toasts;

  dismiss(t: OcToast): void {
    this.toastService.dismiss(t.id);
  }

  trackById(_index: number, t: OcToast): number {
    return t.id;
  }
}
