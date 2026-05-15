import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { MachineService } from '../../src/app/services/machine.service';

describe('MachineService', () => {
  let service: MachineService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(MachineService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('configured GETs /machine/configured', () => {
    service.configured().subscribe();
    const req = httpMock.expectOne('/machine/configured');
    expect(req.request.method).toBe('GET');
    req.flush({ machines: [] });
  });

  it('standby GETs /machine/standby', () => {
    service.standby().subscribe();
    const req = httpMock.expectOne('/machine/standby');
    expect(req.request.method).toBe('GET');
    req.flush({ machines: [] });
  });

  it('online GETs /machine/online', () => {
    service.online().subscribe();
    const req = httpMock.expectOne('/machine/online');
    expect(req.request.method).toBe('GET');
    req.flush({ machines: [] });
  });

  it.each<['state' | 'start' | 'stop' | 'remove', string]>([
    ['state', '/machine/state'],
    ['start', '/machine/start'],
    ['stop', '/machine/stop'],
    ['remove', '/machine/remove'],
  ])('%s GETs %s with machine_name query param', (method, url) => {
    (service[method]('sample') as { subscribe: () => void }).subscribe();
    const req = httpMock.expectOne((r) => r.url === url);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('machine_name')).toBe('sample');
    req.flush(method === 'state' ? { State: { active_connection: false } } : {});
  });
});
