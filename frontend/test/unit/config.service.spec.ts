import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ConfigService } from '../../src/app/services/config.service';
import {
  MachineConfiguration,
  MachineConfigurationDoc,
  MachineConfigurationListResponse,
} from '../../src/app/models/configuration.model';

describe('ConfigService', () => {
  let service: ConfigService;
  let httpMock: HttpTestingController;

  const sampleConfig: MachineConfiguration = {
    machineData: {
      machineName: 'sample',
      plcIp: '192.168.1.1',
      plcPort: 102,
      plcRack: 0,
      plcSlot: 1,
      pduSize: 10,
      requestInterval: 1,
    },
    mqttData: { mqttIp: '192.168.1.2', mqttPort: 1883, mqttTopic: 'on/ot/sample' },
    plcTagData: [{ tagName: 'foo', tagAddress: 'DB1.X0.0' }],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ConfigService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('readAll GETs /config/read/all', () => {
    const response: MachineConfigurationListResponse = { rows: [] };
    service.readAll().subscribe((r) => expect(r).toEqual(response));
    const req = httpMock.expectOne('/config/read/all');
    expect(req.request.method).toBe('GET');
    req.flush(response);
  });

  it('readOne GETs /config/read/one with machine_name query param', () => {
    const doc: MachineConfigurationDoc = { ...sampleConfig };
    service.readOne('sample').subscribe((r) => expect(r).toEqual(doc));
    const req = httpMock.expectOne((r) => r.url === '/config/read/one');
    expect(req.request.params.get('machine_name')).toBe('sample');
    req.flush(doc);
  });

  it('create POSTs a double-encoded JSON body to /config/create', () => {
    service.create(sampleConfig).subscribe();
    const req = httpMock.expectOne('/config/create');
    expect(req.request.method).toBe('POST');
    expect(typeof req.request.body).toBe('string');
    expect(JSON.parse(req.request.body as string)).toBe(JSON.stringify(sampleConfig));
    req.flush({ id: 'sample' });
  });

  it('update PUTs the raw configuration to /config/update', () => {
    service.update(sampleConfig).subscribe();
    const req = httpMock.expectOne('/config/update');
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual(sampleConfig);
    req.flush({ id: 'sample' });
  });

  it('remove GETs /config/remove with machine_name query param', () => {
    service.remove('sample').subscribe();
    const req = httpMock.expectOne((r) => r.url === '/config/remove');
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('machine_name')).toBe('sample');
    req.flush({ id: 'sample' });
  });
});
