import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { MachineListResponse, MachineStateResponse } from '../models/machine-state.model';

@Injectable({ providedIn: 'root' })
export class MachineService {
  private readonly http = inject(HttpClient);

  configured(): Observable<MachineListResponse> {
    return this.http.get<MachineListResponse>('/machine/configured');
  }

  standby(): Observable<MachineListResponse> {
    return this.http.get<MachineListResponse>('/machine/standby');
  }

  online(): Observable<MachineListResponse> {
    return this.http.get<MachineListResponse>('/machine/online');
  }

  state(machineName: string): Observable<MachineStateResponse> {
    const params = new HttpParams().set('machine_name', machineName);
    return this.http.get<MachineStateResponse>('/machine/state', { params });
  }

  start(machineName: string): Observable<unknown> {
    const params = new HttpParams().set('machine_name', machineName);
    return this.http.get('/machine/start', { params });
  }

  stop(machineName: string): Observable<unknown> {
    const params = new HttpParams().set('machine_name', machineName);
    return this.http.get('/machine/stop', { params });
  }

  remove(machineName: string): Observable<unknown> {
    const params = new HttpParams().set('machine_name', machineName);
    return this.http.get('/machine/remove', { params });
  }
}
