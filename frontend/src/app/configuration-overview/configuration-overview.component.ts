import { Component, OnInit } from '@angular/core';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { ItemConfigurationModel } from '../models/item-configuration.model';
import { BackendRequestService } from '../services/backend-request.service';
import { ConfigurationDataService } from '../services/configuration-data.service';

const fadeOutAnimation = trigger('fadeOut', [
  state('active', style({ opacity: 1 })),
  state('inactive', style({ opacity: 0 })),
  transition('active => inactive', animate('3s'))
]);

@Component({
  selector: 'configuration-overview',
  templateUrl: './configuration-overview.component.html',
  styleUrls: ['./configuration-overview.component.css'],
  animations: [fadeOutAnimation]
})

export class ConfigurationOverviewComponent implements OnInit {
    mappedData: ItemConfigurationModel[] = [];
    submissionState = { success: false, error: false };
    toastNotifyMessage = '';
    showConfirmationDialog = false;
    pendingDeletionMachineName: string | null = null;

    constructor(
        private router: Router,
        private configurationDataService: ConfigurationDataService,
        private backendRequestService: BackendRequestService
    ) {}

    ngOnInit(): void {
        this.fetchAllConfigurations();
    }

    /**
     * Fetch all configurations from the backend and map them to ItemConfigurationModel objects.
     */
    fetchAllConfigurations(): void {
        this.backendRequestService.readAllConfig().subscribe(
        response => {
            this.mappedData = response.rows.map(row => this.configurationDataService.createItemConfiguration(row.doc));
        },
        error => this.displayErrorMessage('Error fetching configurations', error)
        );
    }

    /**
     * Start the machine configuration.
     */
    onStartConfiguration(machineName: string): void {
        this.backendRequestService.startMachineConfiguration(machineName).subscribe(
            response => {
                this.displaySuccessMessage(`Starting machine ${machineName} takes 20 seconds`);
            },
            error => this.displayErrorMessage(`Error starting machine ${machineName}, ${error}`)
        );
    }

    /**
     * Initiate the removal of a configuration after confirmation.
     */
    onRemoveConfigurationInitiate(machineName: string): void {
        this.pendingDeletionMachineName = machineName;
        this.showConfirmationDialog = true;
    }

    /**
     * Confirm the deletion of a configuration.
     */
    confirmDeletion(): void {
        if (this.pendingDeletionMachineName) {
            this.backendRequestService.removeConfig(this.pendingDeletionMachineName).subscribe(
                response => {
                    this.mappedData = this.mappedData.filter(config => config.machineData.machineName !== this.pendingDeletionMachineName);
                    this.displaySuccessMessage('Configuration removed successfully.');
                    this.showConfirmationDialog = false;
                    this.pendingDeletionMachineName = null;
                },
                error => this.displayErrorMessage('Error removing configuration', error)
            );
        }
    }

    /**
     * Cancel the deletion process and close the dialog.
     */
    cancelDeletion(): void {
        this.showConfirmationDialog = false;
        this.pendingDeletionMachineName = null;
        this.displayErrorMessage('Configuration removal aborted.');
    }

    /**
     * Navigate to the create-configuration page.
     */
    onEditConfiguration(config: ItemConfigurationModel): void {
        this.router.navigate(['/create-configuration'], { queryParams: { machineName: config.machineData.machineName } });
    }

    /**
     * Display a success message.
     */
    private displaySuccessMessage(message: string): void {
        this.submissionState = { success: true, error: false };
        this.toastNotifyMessage = message;
        setTimeout(() => (this.submissionState.success = false), 10000);
    }

    /**
     * Display an error message.
     */
    private displayErrorMessage(defaultMessage: string, error?: HttpErrorResponse): void {
        let errorMessage = defaultMessage;
        if (error) {
            errorMessage += ` Error: ${error.error?.error || error.message}`;
        }
        this.submissionState = { success: false, error: true };
        this.toastNotifyMessage = errorMessage;
        setTimeout(() => (this.submissionState.error = false), 6000);

        if (error) {
            console.error('Status Code:', error.status);
            console.error('Error Message:', error.message);
        }
    }

}