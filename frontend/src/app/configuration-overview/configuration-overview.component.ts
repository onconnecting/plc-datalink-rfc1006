import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { ConfigService } from '../services/config.service';
import { MachineService } from '../services/machine.service';
import { formatBackendError } from '../services/error-message';
import {
  DialogService,
  OcButtonDirective,
  OcCardComponent,
  ToastService,
} from '../ui';
import {
  MachineConfiguration,
  MachineConfigurationDoc,
} from '../models/configuration.model';

@Component({
  selector: 'oc-configuration-overview',
  standalone: true,
  imports: [OcButtonDirective, OcCardComponent],
  templateUrl: './configuration-overview.component.html',
  styleUrl: './configuration-overview.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConfigurationOverviewComponent implements OnInit {
  private readonly configService = inject(ConfigService);
  private readonly machineService = inject(MachineService);
  private readonly toast = inject(ToastService);
  private readonly dialog = inject(DialogService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly configurations = signal<MachineConfiguration[]>([]);
  protected readonly loaded = signal<boolean>(false);

  ngOnInit(): void {
    this.refresh();
  }

  private refresh(): void {
    this.configService
      .readAll()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (response) => {
          this.configurations.set(
            response.rows.map((row) => this.docToConfiguration(row.doc)),
          );
          this.loaded.set(true);
        },
        error: (err) => {
          this.loaded.set(true);
          this.toast.error(
            formatBackendError('Konfigurationen konnten nicht geladen werden', err),
          );
        },
      });
  }

  private docToConfiguration(doc: MachineConfigurationDoc): MachineConfiguration {
    return {
      machineData: { ...doc.machineData },
      mqttData: { ...doc.mqttData },
      plcTagData: doc.plcTagData.map((tag) => ({ ...tag })),
    };
  }

  protected onStart(machineName: string): void {
    this.machineService
      .start(machineName)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () =>
          this.toast.success(
            `Machine ${machineName} wird gestartet. Telegraf benötigt ca. 20 Sekunden.`,
          ),
        error: (err) =>
          this.toast.error(
            formatBackendError(`Start für Machine ${machineName} fehlgeschlagen`, err),
          ),
      });
  }

  protected onEdit(config: MachineConfiguration): void {
    this.router.navigate(['/create-configuration'], {
      queryParams: { machineName: config.machineData.machineName },
    });
  }

  protected async onRemove(machineName: string): Promise<void> {
    const ok = await this.dialog.confirm({
      title: 'Konfiguration entfernen',
      message: `Konfiguration für ${machineName} unwiderruflich entfernen?`,
      confirmLabel: 'Entfernen',
      cancelLabel: 'Abbrechen',
      tone: 'danger',
    });
    if (!ok) {
      return;
    }
    this.configService
      .remove(machineName)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.configurations.update((list) =>
            list.filter((c) => c.machineData.machineName !== machineName),
          );
          this.toast.success(`Konfiguration für ${machineName} entfernt.`);
        },
        error: (err) =>
          this.toast.error(
            formatBackendError(
              `Konfiguration für ${machineName} konnte nicht entfernt werden`,
              err,
            ),
          ),
      });
  }
}
