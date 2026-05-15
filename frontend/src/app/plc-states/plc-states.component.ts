import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { EMPTY, forkJoin, interval, of, switchMap } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { MachineService } from '../services/machine.service';
import { ConfigService } from '../services/config.service';
import { formatBackendError } from '../services/error-message';
import {
  OcButtonDirective,
  OcCardComponent,
  OcStatusPillComponent,
  ToastService,
} from '../ui';
import { MachineConfigurationDoc } from '../models/configuration.model';
import { MachineStateBody } from '../models/machine-state.model';

interface MachineRow {
  name: string;
  state: MachineStateBody | null;
}

const POLL_INTERVAL_MS = 5000;

@Component({
  selector: 'oc-plc-states',
  standalone: true,
  imports: [RouterLink, OcButtonDirective, OcCardComponent, OcStatusPillComponent],
  templateUrl: './plc-states.component.html',
  styleUrl: './plc-states.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PlcStatesComponent implements OnInit {
  private readonly machineService = inject(MachineService);
  private readonly configService = inject(ConfigService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly rows = signal<MachineRow[]>([]);
  protected readonly loaded = signal<boolean>(false);
  protected readonly expandedName = signal<string | null>(null);
  protected readonly expandedConfig = signal<MachineConfigurationDoc | null>(null);

  ngOnInit(): void {
    this.bootstrap();
  }

  private bootstrap(): void {
    this.machineService
      .standby()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (response) => {
          const names = response.machines ?? [];
          this.rows.set(names.map((name) => ({ name, state: null })));
          this.loaded.set(true);
          if (names.length === 0) {
            return;
          }
          this.fetchStatesOnce(names);
          this.startPolling(names);
        },
        error: (err) => {
          this.loaded.set(true);
          this.toast.error(
            formatBackendError('Konfigurierte Machines konnten nicht geladen werden', err),
          );
        },
      });
  }

  private fetchStatesOnce(names: string[]): void {
    forkJoin(
      names.map((name) =>
        this.machineService.state(name).pipe(
          catchError(() => of({ State: { active_connection: false, last_update: null } })),
        ),
      ),
    )
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((responses) => {
        this.rows.set(
          names.map((name, index) => ({ name, state: responses[index].State })),
        );
      });
  }

  private startPolling(initialNames: string[]): void {
    let names = initialNames;
    interval(POLL_INTERVAL_MS)
      .pipe(
        switchMap(() => {
          names = this.rows().map((row) => row.name);
          if (names.length === 0) {
            return EMPTY;
          }
          return forkJoin(
            names.map((name) =>
              this.machineService.state(name).pipe(
                catchError(() => of({ State: { active_connection: false, last_update: null } })),
              ),
            ),
          );
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((responses) => {
        this.rows.set(
          names.map((name, index) => ({ name, state: responses[index].State })),
        );
      });
  }

  protected toggle(name: string): void {
    if (this.expandedName() === name) {
      this.expandedName.set(null);
      this.expandedConfig.set(null);
      return;
    }
    this.expandedName.set(name);
    this.expandedConfig.set(null);
    this.configService
      .readOne(name)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (doc) => this.expandedConfig.set(doc),
        error: (err) =>
          this.toast.error(
            formatBackendError(`Konfiguration für ${name} konnte nicht geladen werden`, err),
          ),
      });
  }

  protected start(name: string, event: Event): void {
    event.stopPropagation();
    this.machineService
      .start(name)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () =>
          this.toast.success(`Machine ${name} wird gestartet. Telegraf benötigt ca. 20 Sekunden.`),
        error: (err) =>
          this.toast.error(formatBackendError(`Start für Machine ${name} fehlgeschlagen`, err)),
      });
  }

  protected stop(name: string, event: Event): void {
    event.stopPropagation();
    this.machineService
      .stop(name)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.toast.success(`Machine ${name} gestoppt. Telegraf inaktiv.`),
        error: (err) =>
          this.toast.error(formatBackendError(`Stop für Machine ${name} fehlgeschlagen`, err)),
      });
  }

  protected remove(name: string, event: Event): void {
    event.stopPropagation();
    this.machineService
      .remove(name)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.rows.update((rows) => rows.filter((r) => r.name !== name));
          if (this.expandedName() === name) {
            this.expandedName.set(null);
            this.expandedConfig.set(null);
          }
          this.toast.success(`Machine ${name} entfernt.`);
        },
        error: (err) =>
          this.toast.error(
            formatBackendError(`Entfernen von Machine ${name} fehlgeschlagen`, err),
          ),
      });
  }

  protected stateTone(state: MachineStateBody | null): 'success' | 'error' | 'neutral' {
    if (!state) return 'neutral';
    return state.active_connection ? 'success' : 'error';
  }

  protected stateLabel(state: MachineStateBody | null): string {
    if (!state) return 'unbekannt';
    return state.active_connection ? 'connected' : 'disconnected';
  }

  protected lastUpdate(state: MachineStateBody | null): string {
    if (!state || !state.last_update) return '—';
    return state.last_update;
  }
}
