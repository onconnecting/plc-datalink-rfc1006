import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ConfigurationOverviewComponent } from '../../src/app/configuration-overview/configuration-overview.component';
import { ConfigService } from '../../src/app/services/config.service';
import { MachineService } from '../../src/app/services/machine.service';
import { ToastService } from '../../src/app/ui/toast.service';
import { DialogService } from '../../src/app/ui/dialog.service';
import { MachineConfigurationListResponse } from '../../src/app/models/configuration.model';

describe('ConfigurationOverviewComponent', () => {
  let configService: { readAll: jest.Mock; remove: jest.Mock };
  let machineService: { start: jest.Mock };
  let toast: { success: jest.Mock; error: jest.Mock; warning: jest.Mock; info: jest.Mock };
  let dialog: { confirm: jest.Mock };

  const emptyResponse: MachineConfigurationListResponse = { rows: [] };

  beforeEach(async () => {
    configService = { readAll: jest.fn().mockReturnValue(of(emptyResponse)), remove: jest.fn() };
    machineService = { start: jest.fn() };
    toast = { success: jest.fn(), error: jest.fn(), warning: jest.fn(), info: jest.fn() };
    dialog = { confirm: jest.fn() };

    await TestBed.configureTestingModule({
      imports: [ConfigurationOverviewComponent],
      providers: [
        provideRouter([]),
        { provide: ConfigService, useValue: configService },
        { provide: MachineService, useValue: machineService },
        { provide: ToastService, useValue: toast },
        { provide: DialogService, useValue: dialog },
      ],
    }).compileComponents();
  });

  it('instantiates and reads all configurations on init', () => {
    const fixture = TestBed.createComponent(ConfigurationOverviewComponent);
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
    expect(configService.readAll).toHaveBeenCalledTimes(1);
  });

  it('toasts an error when the read fails', () => {
    configService.readAll.mockReturnValueOnce(throwError(() => new Error('boom')));
    const fixture = TestBed.createComponent(ConfigurationOverviewComponent);
    fixture.detectChanges();
    expect(toast.error).toHaveBeenCalled();
  });
});
