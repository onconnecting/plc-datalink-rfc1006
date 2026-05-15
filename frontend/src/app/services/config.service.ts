import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import {
  MachineConfiguration,
  MachineConfigurationDoc,
  MachineConfigurationListResponse,
} from '../models/configuration.model';

@Injectable({ providedIn: 'root' })
export class ConfigService {
  private readonly http = inject(HttpClient);
  private readonly jsonHeaders = new HttpHeaders({ 'Content-Type': 'application/json' });

  readAll(): Observable<MachineConfigurationListResponse> {
    return this.http.get<MachineConfigurationListResponse>('/config/read/all');
  }

  readOne(machineName: string): Observable<MachineConfigurationDoc> {
    const params = new HttpParams().set('machine_name', machineName);
    return this.http.get<MachineConfigurationDoc>('/config/read/one', { params });
  }

  // The backend route /config/create calls json.loads(request.get_json()),
  // i.e. the body is a JSON-encoded string that itself contains JSON. We
  // double-stringify here to match that contract; do not "fix" without a
  // coordinated backend change.
  create(configuration: MachineConfiguration): Observable<{ id: string }> {
    return this.http.post<{ id: string }>(
      '/config/create',
      JSON.stringify(JSON.stringify(configuration)),
      { headers: this.jsonHeaders },
    );
  }

  update(configuration: MachineConfiguration): Observable<{ id: string }> {
    return this.http.put<{ id: string }>('/config/update', configuration, {
      headers: this.jsonHeaders,
    });
  }

  remove(machineName: string): Observable<{ id: string }> {
    const params = new HttpParams().set('machine_name', machineName);
    return this.http.get<{ id: string }>('/config/remove', { params });
  }
}
