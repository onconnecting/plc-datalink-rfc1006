/**
 * Integration tests: /machine/* endpoints end-to-end.
 *
 * The ZKS-touching test (`/machine/start` against a real S7 server) is skipped
 * automatically when $ZKS_S7_HOST is empty or unreachable. Bring up ZKS-Mock
 * from its own repo (docs/machines-db-layout/zks-machine-mock/) to run the full
 * path.
 */
import * as net from 'node:net';
import type { MachineConfiguration } from '../../src/app/models/configuration.model';
import type { MachineListResponse, MachineStateResponse } from '../../src/app/models/machine-state.model';

const BACKEND_URL = process.env['BACKEND_URL'] ?? 'http://plc-datalink-rfc1006-backend-int:5000';
const ZKS_HOST = process.env['ZKS_S7_HOST'] ?? '';
const ZKS_PORT = Number(process.env['ZKS_S7_PORT'] ?? 102);

async function backendIsReachable(): Promise<boolean> {
  try {
    const r = await fetch(`${BACKEND_URL}/machine/configured`);
    return r.ok || r.status === 404;
  } catch {
    return false;
  }
}

async function getMachineList(endpoint: string): Promise<MachineListResponse> {
  const r = await fetch(`${BACKEND_URL}${endpoint}`);
  if (!r.ok) throw new Error(`GET ${endpoint} → ${r.status}`);
  return r.json() as Promise<MachineListResponse>;
}

async function postConfig(config: MachineConfiguration): Promise<void> {
  const r = await fetch(`${BACKEND_URL}/config/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(JSON.stringify(config)),
  });
  if (!r.ok) throw new Error(`POST /config/create → ${r.status} ${await r.text()}`);
}

async function machineStart(name: string): Promise<void> {
  const r = await fetch(`${BACKEND_URL}/machine/start?machine_name=${encodeURIComponent(name)}`);
  if (!r.ok) throw new Error(`GET /machine/start → ${r.status}`);
}

async function machineStop(name: string): Promise<void> {
  await fetch(`${BACKEND_URL}/machine/stop?machine_name=${encodeURIComponent(name)}`).catch(() => undefined);
}

async function machineRemove(name: string): Promise<void> {
  await fetch(`${BACKEND_URL}/machine/remove?machine_name=${encodeURIComponent(name)}`).catch(() => undefined);
}

async function configRemove(name: string): Promise<void> {
  await fetch(`${BACKEND_URL}/config/remove?machine_name=${encodeURIComponent(name)}`).catch(() => undefined);
}

async function machineState(name: string): Promise<MachineStateResponse | null> {
  try {
    const r = await fetch(`${BACKEND_URL}/machine/state?machine_name=${encodeURIComponent(name)}`);
    if (!r.ok) return null;
    return r.json() as Promise<MachineStateResponse>;
  } catch {
    return null;
  }
}

async function zksReachable(): Promise<boolean> {
  if (!ZKS_HOST) return false;
  return await new Promise((resolve) => {
    const sock = net.createConnection({ host: ZKS_HOST, port: ZKS_PORT, timeout: 1500 });
    sock.once('connect', () => { sock.destroy(); resolve(true); });
    sock.once('error', () => resolve(false));
    sock.once('timeout', () => { sock.destroy(); resolve(false); });
  });
}

describe('machine endpoints [integration]', () => {
  let backendReachable = false;
  let zksAvailable = false;

  beforeAll(async () => {
    backendReachable = await backendIsReachable();
    zksAvailable = await zksReachable();
  });

  it('GET /machine/configured returns an array', async () => {
    if (!backendReachable) return;
    const response = await getMachineList('/machine/configured');
    expect(Array.isArray(response.machines)).toBe(true);
  });

  it('GET /machine/standby returns an array', async () => {
    if (!backendReachable) return;
    const response = await getMachineList('/machine/standby');
    expect(Array.isArray(response.machines)).toBe(true);
  });

  it('GET /machine/online returns an array', async () => {
    if (!backendReachable) return;
    const response = await getMachineList('/machine/online');
    expect(Array.isArray(response.machines)).toBe(true);
  });

  it('start against the ZKS-Mock yields active_connection=true within 30 s', async () => {
    if (!backendReachable) return;
    if (!zksAvailable) {
      console.warn(`ZKS-Mock not reachable at ${ZKS_HOST}:${ZKS_PORT} — skipping`);
      return;
    }

    const machineName = `int-zks-${Date.now()}`;
    const config: MachineConfiguration = {
      machineData: {
        machineName,
        plcIp: ZKS_HOST,
        plcPort: ZKS_PORT,
        plcRack: 0,
        plcSlot: 1,
        pduSize: 10,
        requestInterval: 1,
      },
      mqttData: { mqttIp: '127.0.0.1', mqttPort: 1883, mqttTopic: `on/ot/${machineName}` },
      plcTagData: [
        { tagName: 'State', tagAddress: 'DB1.I0' },
        { tagName: 'PartCounter', tagAddress: 'DB1.DI4' },
        { tagName: 'Yield', tagAddress: 'DB1.R28' },
      ],
    };

    try {
      await postConfig(config);
      await machineStart(machineName);

      let active = false;
      for (let attempt = 0; attempt < 30; attempt++) {
        await new Promise((r) => setTimeout(r, 1000));
        const state = await machineState(machineName);
        if (state?.State.active_connection) {
          active = true;
          break;
        }
      }
      expect(active).toBe(true);
    } finally {
      await machineStop(machineName);
      await machineRemove(machineName);
      await configRemove(machineName);
    }
  });
});
