import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  AbstractControl,
  FormArray,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ConfigService } from '../services/config.service';
import { formatBackendError } from '../services/error-message';
import {
  OcButtonDirective,
  OcCardComponent,
  OcFieldComponent,
  OcInputDirective,
  ToastService,
} from '../ui';
import {
  ipv4Validator,
  plcAddressValidator,
  portValidators,
  rackValidators,
  slotValidators,
  pduSizeValidators,
  requestIntervalValidators,
  tagNameValidator,
} from '../validators/plc-validators';
import {
  MachineConfiguration,
  MachineConfigurationDoc,
} from '../models/configuration.model';

@Component({
  selector: 'oc-create-configuration',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    OcButtonDirective,
    OcInputDirective,
    OcCardComponent,
    OcFieldComponent,
  ],
  templateUrl: './create-configuration.component.html',
  styleUrl: './create-configuration.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreateConfigurationComponent implements OnInit {
  private readonly fb = inject(FormBuilder).nonNullable;
  private readonly route = inject(ActivatedRoute);
  private readonly configService = inject(ConfigService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly isEditing = signal<boolean>(false);
  protected readonly submitting = signal<boolean>(false);

  protected readonly form = this.fb.group({
    machineData: this.fb.group({
      machineName: ['', [Validators.required, Validators.pattern(/^[A-Za-z0-9_-]+$/)]],
      plcIp: ['', [Validators.required, ipv4Validator]],
      plcPort: [102, portValidators],
      plcRack: [0, rackValidators],
      plcSlot: [1, slotValidators],
      pduSize: [10, pduSizeValidators],
      requestInterval: [1, requestIntervalValidators],
    }),
    mqttData: this.fb.group({
      mqttIp: ['', [Validators.required, ipv4Validator]],
      mqttPort: [1883, portValidators],
      mqttTopic: ['', [Validators.required]],
    }),
    plcTagData: this.fb.array([this.makeTag()]),
  });

  ngOnInit(): void {
    this.route.queryParamMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((params) => {
        const machineName = params.get('machineName');
        if (machineName) {
          this.isEditing.set(true);
          this.loadConfiguration(machineName);
          this.machineNameControl.disable({ emitEvent: false });
        } else {
          this.isEditing.set(false);
          this.machineNameControl.enable({ emitEvent: false });
        }
      });
  }

  private loadConfiguration(machineName: string): void {
    this.configService
      .readOne(machineName)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (doc) => this.patchFromDoc(doc),
        error: (err) =>
          this.toast.error(
            formatBackendError(`Konfiguration für ${machineName} konnte nicht geladen werden`, err),
          ),
      });
  }

  private patchFromDoc(doc: MachineConfigurationDoc): void {
    this.form.patchValue({
      machineData: doc.machineData,
      mqttData: doc.mqttData,
    });
    this.plcTagsArray.clear();
    for (const tag of doc.plcTagData) {
      this.plcTagsArray.push(this.makeTag(tag.tagName, tag.tagAddress));
    }
  }

  private makeTag(name = '', address = ''): FormGroup {
    return this.fb.group({
      tagName: [name, [Validators.required, tagNameValidator]],
      tagAddress: [address, [Validators.required, plcAddressValidator]],
    });
  }

  get plcTagsArray(): FormArray<FormGroup> {
    return this.form.controls.plcTagData;
  }

  get machineNameControl(): AbstractControl {
    return this.form.controls.machineData.controls.machineName;
  }

  protected addTag(): void {
    this.plcTagsArray.push(this.makeTag());
  }

  protected removeTag(index: number): void {
    if (this.plcTagsArray.length > 1) {
      this.plcTagsArray.removeAt(index);
    } else {
      this.plcTagsArray.at(0).reset({ tagName: '', tagAddress: '' });
    }
  }

  protected submit(): void {
    this.form.markAllAsTouched();
    if (this.form.invalid) {
      this.toast.warning('Formular unvollständig. Pflichtfelder und Formate prüfen.');
      return;
    }

    const value = this.form.getRawValue() as MachineConfiguration;
    this.submitting.set(true);

    const request$ = this.isEditing()
      ? this.configService.update(value)
      : this.configService.create(value);

    request$.pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (response) => {
        this.submitting.set(false);
        if (this.isEditing()) {
          this.toast.success(`Konfiguration für ${response.id} aktualisiert.`);
        } else {
          this.toast.success(`Konfiguration für ${response.id} angelegt.`);
        }
      },
      error: (err) => {
        this.submitting.set(false);
        const prefix = this.isEditing()
          ? 'Konfiguration nicht aktualisiert'
          : 'Konfiguration nicht angelegt';
        this.toast.error(formatBackendError(prefix, err));
      },
    });
  }

  // --- Per-field error message helpers (CI tonality) ---

  protected machineDataError(name: keyof MachineConfiguration['machineData']): string | null {
    const ctrl = this.form.controls.machineData.get(name as string);
    if (!ctrl || !ctrl.touched || ctrl.valid) return null;
    if (ctrl.hasError('required')) return this.requiredMessage(name as string);
    if (ctrl.hasError('ipv4')) return 'Ungültiges IPv4-Format (z. B. 192.168.1.1).';
    if (ctrl.hasError('min') || ctrl.hasError('max')) {
      return this.numericRangeMessage(name as string);
    }
    if (ctrl.hasError('pattern')) {
      return 'Nur Buchstaben, Ziffern, _ und - erlaubt.';
    }
    return 'Ungültiger Wert.';
  }

  protected mqttError(name: keyof MachineConfiguration['mqttData']): string | null {
    const ctrl = this.form.controls.mqttData.get(name as string);
    if (!ctrl || !ctrl.touched || ctrl.valid) return null;
    if (ctrl.hasError('required')) return this.requiredMessage(name as string);
    if (ctrl.hasError('ipv4')) return 'Ungültiges IPv4-Format (z. B. 192.168.1.1).';
    if (ctrl.hasError('min') || ctrl.hasError('max')) {
      return 'Port außerhalb des gültigen Bereichs 1–65535.';
    }
    return 'Ungültiger Wert.';
  }

  protected tagNameError(index: number): string | null {
    const ctrl = this.plcTagsArray.at(index).get('tagName');
    if (!ctrl || !ctrl.touched || ctrl.valid) return null;
    if (ctrl.hasError('required')) return 'Tag-Name erforderlich.';
    if (ctrl.hasError('tagName')) return 'Nur Buchstaben und Ziffern erlaubt (z. B. lightBarrier).';
    return 'Ungültiger Wert.';
  }

  protected tagAddressError(index: number): string | null {
    const ctrl = this.plcTagsArray.at(index).get('tagAddress');
    if (!ctrl || !ctrl.touched || ctrl.valid) return null;
    if (ctrl.hasError('required')) return 'Tag-Adresse erforderlich.';
    if (ctrl.hasError('plcAddress')) {
      return 'Ungültiges PLC-Adressformat (z. B. DB9.X1732.1 oder DB47.S30.13).';
    }
    return 'Ungültiger Wert.';
  }

  private requiredMessage(field: string): string {
    switch (field) {
      case 'machineName': return 'Machine-Name erforderlich.';
      case 'plcIp': return 'PLC IP erforderlich.';
      case 'plcPort': return 'PLC Port erforderlich.';
      case 'plcRack': return 'Rack erforderlich.';
      case 'plcSlot': return 'Slot erforderlich.';
      case 'pduSize': return 'Batch-Größe erforderlich.';
      case 'requestInterval': return 'Intervall erforderlich.';
      case 'mqttIp': return 'MQTT IP erforderlich.';
      case 'mqttPort': return 'MQTT Port erforderlich.';
      case 'mqttTopic': return 'MQTT Topic erforderlich.';
      default: return 'Pflichtfeld.';
    }
  }

  private numericRangeMessage(field: string): string {
    switch (field) {
      case 'plcPort': return 'PLC Port außerhalb 1–65535.';
      case 'plcRack': return 'PLC Rack außerhalb 0–100.';
      case 'plcSlot': return 'PLC Slot außerhalb 0–18.';
      case 'pduSize': return 'Batch-Größe muss ≥ 1 sein.';
      case 'requestInterval': return 'Intervall muss ≥ 1 Sekunde sein.';
      default: return 'Wert außerhalb des gültigen Bereichs.';
    }
  }
}
