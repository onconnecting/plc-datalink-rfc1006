// Interface for PLC Tag
export interface PLCTag {
  tagName: string;
  tagAddress: string;
}

// Interface for Machine Data Section
export interface MachineData {
  machineName: string;
  plcIp: string;
  plcPort: number;
  plcRack: number;
  plcSlot: number;
  pduSize: number;
  requestInterval: number;
}

// Interface for MQTT Data Section
export interface MQTTData {
  mqttTopic: string;
  mqttIp: string;
  mqttPort: number;
}

// Interface for Complete Form
export interface ItemConfigurationModel {
  machineData: MachineData;
  mqttData: MQTTData;
  plcTagData: PLCTag[];
}
