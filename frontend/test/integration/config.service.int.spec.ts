/**
 * Integration tests: /config/* endpoints end-to-end.
 *
 * Stack: docker compose -f dc-plc-datalink-rfc1006-test.yml up -d database-int backend-int
 *        docker compose -f dc-plc-datalink-rfc1006-test.yml run --rm frontend-test-int
 *
 * These specs hit the real Flask backend (which talks to a real CouchDB) and
 * verify the OpenAPI contract the Angular ConfigService relies on. The service
 * code itself is covered by the unit suite; here we make sure the wire contract
 * still matches reality.
 *
 * Importantly: this includes the awkward double-JSON-encoding the /config/create
 * route expects (see ConfigService.create() comment).
 */
import type { MachineConfiguration, MachineConfigurationDoc, MachineConfigurationListResponse } from '../../src/app/models/configuration.model';

const BACKEND_URL = process.env['BACKEND_URL'] ?? 'http://plc-datalink-rfc1006-backend-int:5000';

async function backendIsReachable(): Promise<boolean> {
  try {
    const r = await fetch(`${BACKEND_URL}/config/read/all`, { method: 'GET' });
    return r.ok || r.status === 404;
  } catch {
    return false;
  }
}

async function postCreate(config: MachineConfiguration): Promise<{ id: string }> {
  // The /config/create route does json.loads(request.get_json()) — the body
  // must be a JSON-encoded string that itself contains JSON. The Angular
  // ConfigService.create double-encodes; we mirror that here.
  const r = await fetch(`${BACKEND_URL}/config/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(JSON.stringify(config)),
  });
  if (!r.ok) throw new Error(`POST /config/create → ${r.status} ${await r.text()}`);
  return r.json() as Promise<{ id: string }>;
}

async function getReadAll(): Promise<MachineConfigurationListResponse> {
  const r = await fetch(`${BACKEND_URL}/config/read/all`);
  if (!r.ok) throw new Error(`GET /config/read/all → ${r.status}`);
  return r.json() as Promise<MachineConfigurationListResponse>;
}

async function getReadOne(machineName: string): Promise<MachineConfigurationDoc> {
  const r = await fetch(`${BACKEND_URL}/config/read/one?machine_name=${encodeURIComponent(machineName)}`);
  if (!r.ok) throw new Error(`GET /config/read/one → ${r.status}`);
  return r.json() as Promise<MachineConfigurationDoc>;
}

async function putUpdate(config: MachineConfiguration): Promise<{ id: string }> {
  const r = await fetch(`${BACKEND_URL}/config/update`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!r.ok) throw new Error(`PUT /config/update → ${r.status} ${await r.text()}`);
  return r.json() as Promise<{ id: string }>;
}

async function getRemove(machineName: string): Promise<void> {
  const r = await fetch(`${BACKEND_URL}/config/remove?machine_name=${encodeURIComponent(machineName)}`);
  if (!r.ok) throw new Error(`GET /config/remove → ${r.status}`);
}

describe('config endpoints [integration]', () => {
  const machineName = `int-test-${Date.now()}`;
  let reachable = false;

  beforeAll(async () => {
    reachable = await backendIsReachable();
  });

  afterAll(async () => {
    if (!reachable) return;
    await getRemove(machineName).catch(() => undefined);
  });

  const sampleConfig: MachineConfiguration = {
    machineData: {
      machineName,
      plcIp: '127.0.0.1',
      plcPort: 102,
      plcRack: 0,
      plcSlot: 1,
      pduSize: 10,
      requestInterval: 1,
    },
    mqttData: { mqttIp: '127.0.0.1', mqttPort: 1883, mqttTopic: `on/ot/${machineName}` },
    plcTagData: [{ tagName: 'sample', tagAddress: 'DB1.X0.0' }],
  };

  it('backend is reachable on /config/read/all', async () => {
    expect(reachable).toBe(true);
    const response = await getReadAll();
    expect(response).toHaveProperty('rows');
    expect(Array.isArray(response.rows)).toBe(true);
  });

  it('create → readOne → update → remove round-trip', async () => {
    if (!reachable) {
      console.warn('Backend not reachable — skipping round-trip');
      return;
    }

    const created = await postCreate(sampleConfig);
    expect(created.id).toBe(machineName);

    const fetched = await getReadOne(machineName);
    expect(fetched.machineData.machineName).toBe(machineName);
    expect(fetched.mqttData.mqttTopic).toBe(`on/ot/${machineName}`);
    expect(fetched.plcTagData).toHaveLength(1);
    expect(fetched.plcTagData[0].tagAddress).toBe('DB1.X0.0');

    const updated: MachineConfiguration = {
      ...sampleConfig,
      machineData: { ...sampleConfig.machineData, requestInterval: 5 },
    };
    const updateResponse = await putUpdate(updated);
    expect(updateResponse.id).toBe(machineName);

    const refetched = await getReadOne(machineName);
    expect(refetched.machineData.requestInterval).toBe(5);

    await getRemove(machineName);
    await expect(getReadOne(machineName)).rejects.toThrow();
  });
});
