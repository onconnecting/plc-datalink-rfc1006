import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { PlcStatesComponent } from '../../src/app/plc-states/plc-states.component';
import { MachineService } from '../../src/app/services/machine.service';
import { ConfigService } from '../../src/app/services/config.service';
import { ToastService } from '../../src/app/ui/toast.service';

describe('PlcStatesComponent', () => {
  let machineService: { standby: jest.Mock; state: jest.Mock; start: jest.Mock; stop: jest.Mock; remove: jest.Mock };
  let configService: { readOne: jest.Mock };
  let toast: { success: jest.Mock; error: jest.Mock; warning: jest.Mock; info: jest.Mock };

  beforeEach(async () => {
    machineService = {
      standby: jest.fn().mockReturnValue(of({ machines: [] })),
      state: jest.fn(),
      start: jest.fn(),
      stop: jest.fn(),
      remove: jest.fn(),
    };
    configService = { readOne: jest.fn() };
    toast = { success: jest.fn(), error: jest.fn(), warning: jest.fn(), info: jest.fn() };

    await TestBed.configureTestingModule({
      imports: [PlcStatesComponent],
      providers: [
        provideRouter([]),
        { provide: MachineService, useValue: machineService },
        { provide: ConfigService, useValue: configService },
        { provide: ToastService, useValue: toast },
      ],
    }).compileComponents();
  });

  it('instantiates and asks the backend for standby machines', () => {
    const fixture = TestBed.createComponent(PlcStatesComponent);
    fixture.detectChanges();
    expect(fixture.componentInstance).toBeTruthy();
    expect(machineService.standby).toHaveBeenCalledTimes(1);
    fixture.destroy();
  });

  it('toasts an error when standby fetch fails', () => {
    machineService.standby.mockReturnValueOnce(throwError(() => new Error('boom')));
    const fixture = TestBed.createComponent(PlcStatesComponent);
    fixture.detectChanges();
    expect(toast.error).toHaveBeenCalled();
    fixture.destroy();
  });
});
