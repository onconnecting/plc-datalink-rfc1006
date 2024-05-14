import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Configuration {
  machineData: any; // Adjust based on your model
  mqttData: any;
  plcTagData: any[];
}

@Injectable({
  providedIn: 'root'
})
export class BackendRequestService {
  private readonly baseUrl = '/api';

  constructor(private http: HttpClient) {}

  /**
   * Fetch all available configurations.
   */
  readAllConfig(): Observable<any> {
    return this.http.get(`${this.baseUrl}/config/read/all`);
  }

  /**
   * Fetch configured machines.
   */
  readConfiguredMachines(): Observable<any> {
    return this.http.get(`${this.baseUrl}/machine/configured`);
  }

  /**
   * Fetch standby machines.
   */
  readStandbyMachines(): Observable<any> {
    return this.http.get(`${this.baseUrl}/machine/standby`);
  }

  /**
   * Fetch a specific configuration by machine name.
   * @param machineName - The name of the machine whose config is requested.
   */
  readOneConfig(machineName: string): Observable<any> {
    const params = new HttpParams().set('machine_name', machineName);
    return this.http.get(`${this.baseUrl}/config/read/one`, { params });
  }

  /**
   * Create a new machine configuration from a JSON string.
   * @param configurationJson - The JSON string representation of the configuration data.
   */
  storeConfig(configurationJson: string): Observable<any> {
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    return this.http.post(`${this.baseUrl}/config/create`, JSON.stringify(configurationJson), { headers });
  }

  /**
   * Update an existing machine configuration.
   * @param configuration - The updated configuration data.
   */
  updateConfig(configuration: Configuration): Observable<any> {
    const headers = new HttpHeaders({ 'Content-Type': 'application/json' });
    return this.http.put(`${this.baseUrl}/config/update`, JSON.stringify(configuration), { headers });
  }

  /**
   * Remove an existing machine configuration by name.
   * @param machineName - The name of the machine whose config is to be removed.
   */
  removeConfig(machineName: string): Observable<any> {
    const params = new HttpParams().set('machine_name', machineName);
    return this.http.get(`${this.baseUrl}/config/remove`, { params });
  }

  /**
   * Start a machine configuration by name.
   * @param machineName - The name of the machine to start.
   */
  startMachineConfiguration(machineName: string): Observable<any> {
    const params = new HttpParams().set('machine_name', machineName);
    return this.http.get(`${this.baseUrl}/machine/start`, { params });
  }

  /**
   * Stop a machine configuration by name.
   * @param machineName - The name of the machine to stop.
   */
  stopMachineConfiguration(machineName: string): Observable<any> {
    const params = new HttpParams().set('machine_name', machineName);
    return this.http.get(`${this.baseUrl}/machine/stop`, { params });
  }

  // /**
  //  * Get a list of currently active machines.
  //  */
  // getActiveMachines(): Observable<any> {
  //   return this.http.get(`${this.baseUrl}/machine/online`);
  // }

  /**
   * Get the current state of a specific machine by name.
   * @param machineName - The name of the machine whose state is requested.
   */
  getMachineCurrentState(machineName: string): Observable<any> {
    const params = new HttpParams().set('machine_name', machineName);
    return this.http.get(`${this.baseUrl}/machine/state`, { params });
  }

  /**
   * Remove an existing machine by name.
   * @param machineName - The name of the machine whose config is to be removed.
   */
  removeMachine(machineName: string): Observable<any> {
    const params = new HttpParams().set('machine_name', machineName);
    return this.http.get(`${this.baseUrl}/machine/remove`, { params });
  }
}
