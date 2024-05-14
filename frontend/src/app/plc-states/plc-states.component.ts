import { Component, OnInit, OnDestroy } from '@angular/core';
import { interval, Observable, Subscription, forkJoin } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { HttpErrorResponse } from '@angular/common/http';
import { BackendRequestService } from '../services/backend-request.service';
import { ConfigurationDataService } from '../services/configuration-data.service';

const fadeOutAnimation = trigger('fadeOut', [
  state('active', style({ opacity: 1 })),
  state('inactive', style({ opacity: 0 })),
  transition('active => inactive', animate('3s'))
]);

// Structure to hold the machine name and state
interface MachineState {
  name: string;
  state: any;
}

@Component({
  selector: 'plc-states',
  templateUrl: './plc-states.component.html',
  styleUrl: './plc-states.component.css',
  animations: [fadeOutAnimation]
})
export class PlcStates implements OnInit{

  machines: string[] = [];
  machineStates: MachineState[] = [];
  submissionState = { success: false, error: false };
  toastNotifyMessage = '';
  expandedMachine: string | null = null;
  private subscription: Subscription | null = null;
  machineConfig: any = null;

  constructor(
      private configurationDataService: ConfigurationDataService,
      private backendRequestService: BackendRequestService
  ) {}

  ngOnInit() {
    this.fetchAllConfigurations();
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  /**
   * Fetch the state of a single machine as an observable.
   * @param machineName - The name of the machine to fetch the state for.
   * @returns An observable representing the state of the given machine.
   */
  private fetchMachineStateObservable(machineName: string): Observable<any> {
    return this.backendRequestService.getMachineCurrentState(machineName);
  }

  /**
   *  Fetch all configured machines and then retrieve the state for each.
   */
  fetchAllConfigurations(): void {
    this.backendRequestService.readStandbyMachines().subscribe(
      response => {
        this.machines = response.machines || [];
  
        this.fetchAllMachineStatesOnce();
  
        if (this.subscription) {
          this.subscription.unsubscribe();
        }
  
        if (this.machines.length > 0) {
          this.subscription = interval(5000).pipe(
            switchMap(() => {
              const machineStateObservables = this.machines.map(machineName => 
                this.fetchMachineStateObservable(machineName)
              );
  
              return forkJoin(machineStateObservables);
            })
          ).subscribe(
            results => {
              this.machineStates = this.machines.map((machineName, index) => ({
                name: machineName,
                state: results[index]
              }));
            },
            error => this.displayErrorMessage('Error fetching machine states.', error)
          );
        } else {
          this.displaySuccessMessage('No machines configured.');
        }
      },
      error => this.displayErrorMessage('Error fetching configured machines.', error)
    );
  }

  /**
   * Immediately fetch the states of all configured machines once.
   */
  private fetchAllMachineStatesOnce(): void {
    if (this.machines.length === 0) {
        this.machineStates = [];
        this.displaySuccessMessage('No machines configured.');
        return;
    }

    const machineStateObservables = this.machines.map(machineName => 
        this.fetchMachineStateObservable(machineName)
    );

    forkJoin(machineStateObservables).subscribe(
        results => {
            if (results.length === 0) {
                this.displaySuccessMessage('No machines configured.');
                this.machineStates = [];
            } else {
                this.machineStates = this.machines.map((machineName, index) => ({
                    name: machineName,
                    state: results[index]
                }));
            }
        },
        error => this.displayErrorMessage('Error fetching machine states.', error)
    );
  }

  /**
   * Fetch the current state of a single machine and store the result.
   * @param machineName - The name of the machine whose state is being fetched.
   */
  fetchMachineState(machineName: string): void {
    this.backendRequestService.getMachineCurrentState(machineName).subscribe(
      response => {
        this.machineStates = [
          ...this.machineStates.filter(ms => ms.name !== machineName),
          { name: machineName, state: response }
        ];
      },
      error => this.displayErrorMessage(`Error fetching state of ${machineName}`, error)
    );
  }

  /**
   * Fetch all configurations from the backend and map them to ItemConfigurationModel objects.
   */
  fetchMachineConfiguration(machineName: string): void {
    this.backendRequestService.readOneConfig(machineName).subscribe(
      response => {
        this.machineConfig = response;
      },
      (error: HttpErrorResponse) => {
        this.displayErrorMessage('An error occurred while loading the configuration.', error);
      }
    );
  }

  onStartMachine(machineName: string, event: Event): void {
    event.stopPropagation();
    this.backendRequestService.startMachineConfiguration(machineName).subscribe(
      response => {
        this.displaySuccessMessage(`Starting machine ${machineName} takes 20 seconds`);
      },
      error => this.displayErrorMessage(`Error starting machine ${machineName}`, error)
    );
  }

  onStopMachine(machineName: string, event: Event): void {
    event.stopPropagation();
    this.backendRequestService.stopMachineConfiguration(machineName).subscribe(
      response => {
        this.displaySuccessMessage(`Machine ${machineName} stopped successfully.`);
      },
      error => this.displayErrorMessage(`Error stopping machine ${machineName}`, error)
    );
  }

  onRemoveMachine(machineName: string, event: Event): void {
    event.stopPropagation();
    this.backendRequestService.removeMachine(machineName).subscribe(
      response => {
        this.machines = this.machines.filter(name => name !== machineName);
        this.machineStates = this.machineStates.filter(ms => ms.name !== machineName);
        this.displaySuccessMessage(`Machine ${machineName} removed successfully.`);
      },
      error => this.displayErrorMessage(`Error removing machine ${machineName}`, error)
    );
  }

  /**
   * Toggle the expanded state of the machine card and fetch its configuration if expanded.
   * @param machineName - The name of the machine whose configuration is to be fetched.
   */
  toggleMachineConfig(machineName: string): void {
    if (this.expandedMachine === machineName) {
      this.expandedMachine = null;
    } else {
      this.expandedMachine = machineName;
      this.fetchMachineConfiguration(machineName);
    }
  }

  /**
   * Display a success message and update the submission state.
   * @param message - The success message to display.
   */
  private displaySuccessMessage(message: string): void {
    this.submissionState = { success: true, error: false };
    this.toastNotifyMessage = message;
    setTimeout(() => (this.submissionState.success = false), 10000);
  }

  /**
   * Log and display an error message, and update the submission state.
   * @param defaultMessage - The default error message.
   * @param error - The HTTP error response object.
   */
  private displayErrorMessage(defaultMessage: string, error: HttpErrorResponse): void {
      this.submissionState = { success: false, error: true };
      this.toastNotifyMessage = error.error?.error || defaultMessage;
      setTimeout(() => (this.submissionState.error = false), 6000);

      console.error('Status Code:', error.status);
      console.error('Error Message:', error.message);
  }
}