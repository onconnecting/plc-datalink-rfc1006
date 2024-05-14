import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { ItemConfigurationModel, MachineData, MQTTData, PLCTag } from '../models/item-configuration.model';

@Injectable({
  providedIn: 'root'
})
export class ConfigurationDataService {
  private defaultConfiguration: ItemConfigurationModel = {
    machineData: {
      machineName: '',
      plcIp: '',
      plcPort: 102,
      plcRack: 0,
      plcSlot: 0,
      pduSize: 10,
      requestInterval: 1,
    },
    mqttData: {
      mqttTopic: '',
      mqttIp: '',
      mqttPort: 1883,
    },
    plcTagData: [
      { tagName: '', tagAddress: '' },
    ],
  };

  private configurationSubject = new BehaviorSubject<ItemConfigurationModel>(this.defaultConfiguration);
  configuration$ = this.configurationSubject.asObservable();

  constructor() {}

  /**
   * Sets a new configuration form data model
   * @param newConfiguration The updated form data model to be set
   */
  setConfiguration(newConfiguration: ItemConfigurationModel): void {
    this.configurationSubject.next(newConfiguration);
  }

  /**
   * Retrieves the current configuration form data model
   * @returns The current ItemConfigurationModel data
   */
  getConfiguration(): ItemConfigurationModel {
    return this.configurationSubject.value;
  }

  /**
   * Retrieves the current configuration as a JSON string
   * @returns The JSON string representation of the current ItemConfigurationModel
   */
  getConfigurationAsJson(): string {
    const currentConfiguration = this.getConfiguration();
    return JSON.stringify(currentConfiguration, null, 2);
  }

  /**
   * Resets to the default configuration
   */
  resetConfiguration(): void {
    this.configurationSubject.next(this.defaultConfiguration);
  }

  /**
   * Creates an ItemConfigurationModel object from the provided document
   * @param doc - The source data document containing machine, MQTT, and PLC tag information
   * @returns A new ItemConfigurationModel object
   */
  createItemConfiguration(doc: any): ItemConfigurationModel {
    const machineData: MachineData = {
      machineName: doc.machineData.machineName,
      plcIp: doc.machineData.plcIp,
      plcPort: doc.machineData.plcPort,
      plcRack: doc.machineData.plcRack,
      plcSlot: doc.machineData.plcSlot,
      pduSize: doc.machineData.pduSize,
      requestInterval: doc.machineData.requestInterval
    };

    const mqttData: MQTTData = {
      mqttTopic: doc.mqttData.mqttTopic,
      mqttIp: doc.mqttData.mqttIp,
      mqttPort: doc.mqttData.mqttPort
    };

    const plcTagData: PLCTag[] = doc.plcTagData.map((tag: { tagName: string; tagAddress: string }) => ({
      tagName: tag.tagName,
      tagAddress: tag.tagAddress
    }));

    return {
      machineData,
      mqttData,
      plcTagData
    };
  }
}
