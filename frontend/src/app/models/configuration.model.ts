export interface PlcTag {
  tagName: string;
  tagAddress: string;
}

export interface MachineData {
  machineName: string;
  plcIp: string;
  plcPort: number;
  plcRack: number;
  plcSlot: number;
  pduSize: number;
  requestInterval: number;
}

export interface MqttData {
  mqttIp: string;
  mqttPort: number;
  mqttTopic: string;
}

export interface MachineConfiguration {
  machineData: MachineData;
  mqttData: MqttData;
  plcTagData: PlcTag[];
}

export interface MachineConfigurationDoc extends MachineConfiguration {
  _id?: string;
  _rev?: string;
}

export interface MachineConfigurationListRow {
  doc: MachineConfigurationDoc;
}

export interface MachineConfigurationListResponse {
  rows: MachineConfigurationListRow[];
}
