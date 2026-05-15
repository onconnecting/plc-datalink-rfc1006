export interface MachineStateBody {
  active_connection: boolean;
  last_update?: string | null;
}

export interface MachineStateResponse {
  State: MachineStateBody;
}

export interface MachineListResponse {
  machines: string[];
}
