import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';
import { CreateConfigurationComponent } from '../../src/app/create-configuration/create-configuration.component';
import { ConfigService } from '../../src/app/services/config.service';
import { ToastService } from '../../src/app/ui/toast.service';

describe('CreateConfigurationComponent', () => {
  let configService: { create: jest.Mock; update: jest.Mock; readOne: jest.Mock };
  let toast: { success: jest.Mock; warning: jest.Mock; error: jest.Mock; info: jest.Mock };

  beforeEach(async () => {
    configService = {
      create: jest.fn().mockReturnValue(of({ id: 'sample' })),
      update: jest.fn().mockReturnValue(of({ id: 'sample' })),
      readOne: jest.fn(),
    };
    toast = { success: jest.fn(), warning: jest.fn(), error: jest.fn(), info: jest.fn() };

    await TestBed.configureTestingModule({
      imports: [CreateConfigurationComponent],
      providers: [
        provideRouter([]),
        { provide: ActivatedRoute, useValue: { queryParamMap: of(new Map() as never) } },
        { provide: ConfigService, useValue: configService },
        { provide: ToastService, useValue: toast },
      ],
    }).compileComponents();
  });

  it('instantiates with defaults and one empty tag row', () => {
    const fixture = TestBed.createComponent(CreateConfigurationComponent);
    fixture.detectChanges();
    const instance = fixture.componentInstance;
    expect(instance).toBeTruthy();
    expect(instance.plcTagsArray.length).toBe(1);

    const machineData = instance['form'].controls.machineData.getRawValue();
    expect(machineData.plcPort).toBe(102);
    expect(machineData.plcRack).toBe(0);
    expect(machineData.plcSlot).toBe(1);

    const mqttData = instance['form'].controls.mqttData.getRawValue();
    expect(mqttData.mqttPort).toBe(1883);
  });

  it('warns and does not call create when the form is invalid', () => {
    const fixture = TestBed.createComponent(CreateConfigurationComponent);
    fixture.detectChanges();
    fixture.componentInstance['submit']();
    expect(toast.warning).toHaveBeenCalled();
    expect(configService.create).not.toHaveBeenCalled();
  });
});
