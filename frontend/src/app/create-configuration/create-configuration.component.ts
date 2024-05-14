import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormArray, Validators } from '@angular/forms';
import { ItemConfigurationModel } from '../models/item-configuration.model';
import { ConfigurationDataService } from '../services/configuration-data.service';
import { BackendRequestService } from '../services/backend-request.service';
import { HttpErrorResponse } from '@angular/common/http';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { ActivatedRoute } from '@angular/router';


const fadeOutAnimation = trigger('fadeOut', [
  state('active', style({ opacity: 1 })),
  state('inactive', style({ opacity: 0 })),
  transition('active => inactive', animate('3s'))
]);

@Component({
  selector: 'create-configuration',
  templateUrl: './create-configuration.component.html',
  styleUrls: ['./create-configuration.component.css'],
  animations: [fadeOutAnimation]
})

export class CreateConfigurationComponent implements OnInit {
    form: FormGroup;
    submissionState = { success: false, error: false };
    toastNotifyMessage = '';
    isEditing: boolean = false; 

    constructor(
      private fb: FormBuilder,
      private route: ActivatedRoute,
      private configurationDataService: ConfigurationDataService,
      private backendRequestService: BackendRequestService
    ) {}

    ngOnInit(): void {
      this.initializeForm();

      this.route.queryParams.subscribe(params => {
        const machineName = params['machineName'];
        if (machineName) {
          this.isEditing = true;
          this.loadConfiguration(machineName);
        } else {
          this.isEditing = false;
        }
      });
    }

    /**
     * Request configuration for defined machine.
     */
    private loadConfiguration(machineName: string): void {
      this.backendRequestService.readOneConfig(machineName).subscribe(
        response => {
          this.form.patchValue(response);
    
          const tagsArray = this.plcTagData;
          tagsArray.clear();
          response.plcTagData.forEach((tag: any) => {
            tagsArray.push(this.fb.group({
              tagName: [tag.tagName, [Validators.required, Validators.pattern(/^[a-zA-Z0-9]+$/)]],
              tagAddress: [tag.tagAddress, [Validators.required, Validators.pattern(/^DB\d+\.(X|B|C|W|DW|I|DI|R|DT|S)\d+(\.\d+)?$/)]]
            }));
          });
        },
        (error: HttpErrorResponse) => {
          this.displayErrorMessage('An error occurred while loading the configuration.', error);
        }
      );
    }

    /**
     * Initialize the main form and its nested form groups.
     */
    private initializeForm(): void {
      this.form = this.fb.group({
        machineData: this.fb.group({
          machineName: ['', [Validators.required]],
          plcIp: ['', [Validators.required, Validators.pattern(/^\d{1,3}(\.\d{1,3}){3}$/)]],
          plcPort: ['', [Validators.required, Validators.min(1), Validators.max(65535)]],
          plcRack: ['', [Validators.required, Validators.min(0), Validators.max(100)]],
          plcSlot: ['', [Validators.required, Validators.min(0), Validators.max(18)]],
          pduSize: ['', [Validators.required]],
          requestInterval: ['', [Validators.required]]
        }),
        mqttData: this.fb.group({
          mqttTopic: ['', [Validators.required]],
          mqttIp: ['', [Validators.required, Validators.pattern(/^\d{1,3}(\.\d{1,3}){3}$/)]],
          mqttPort: ['', [Validators.required, Validators.min(1), Validators.max(65535)]]
        }),
        plcTagData: this.fb.array([this.createPLCTag()])
      });
    }
    
    /**
     * Create a PLC tag form group.
     * @returns A FormGroup representing a PLC tag.
     */
    createPLCTag(): FormGroup {
      return this.fb.group({
        tagName: ['', [Validators.required, Validators.pattern(/^[a-zA-Z0-9]+$/)]],
        tagAddress: ['', [Validators.required, Validators.pattern(/^DB\d+\.(X|B|C|W|DW|I|DI|R|DT|S)\d+(\.\d+)?$/)]]
      });
    }

    /**
     * Retrieve the PLC tag data form array.
     * @returns The FormArray of PLC tags.
     */
    get plcTagData(): FormArray {
      return this.form.get('plcTagData') as FormArray;
    }

    /**
     * Submit the form data to the backend, and update the current configuration state.
     */
    onSubmit(): void {
      if (this.form.valid) {
        const formData = this.form.value as ItemConfigurationModel;
  
        if (this.isEditing) {
          this.backendRequestService.updateConfig(formData).subscribe(
            response => {
              this.displaySuccessMessage(`Configuration successfully updated for: ${response.id}`);
            },
            (error: HttpErrorResponse) => {
              this.displayErrorMessage('An error occurred while updating the configuration.', error);
            }
          );
        } else {
            const formData = this.form.value as ItemConfigurationModel;
            this.configurationDataService.setConfiguration(formData);
            const currentData = this.configurationDataService.getConfigurationAsJson();
            this.backendRequestService.storeConfig(currentData).subscribe(
              response => {
                this.displaySuccessMessage(`Configuration successfully created for: ${response.id}`);
              },
              (error: HttpErrorResponse) => {
                this.displayErrorMessage('An error occurred while creating the configuration.', error);
              }
            );
        }
      }
    }

    /**
     * Add a new tag to the form array.
     */
    onAddTag(): void {
      this.plcTagData.push(this.createPLCTag());
    }

    /**
     * Remove a tag from the form array by index.
     * @param index - The index of the tag to remove.
     */
    onRemoveTag(index: number): void {
      this.plcTagData.removeAt(index);
    }

    /**
     * Display a success message and update the submission state.
     * @param message - The success message to display.
     */
    private displaySuccessMessage(message: string): void {
      this.submissionState = { success: true, error: false };
      this.toastNotifyMessage = message;
      setTimeout(() => (this.submissionState.success = false), 3000);
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

    /**
     * Initialize the main form and its nested form groups.
     */
    private debugInitializeForm(): void {
      this.form = this.fb.group({
        machineData: this.fb.group({
          machineName: ['devBoard', [Validators.required]],
          plcIp: ['192.168.4.100', [Validators.required, Validators.pattern(/^\d{1,3}(\.\d{1,3}){3}$/)]],
          plcPort: [102, [Validators.required, Validators.min(1), Validators.max(65535)]],
          plcRack: [0, [Validators.required, Validators.min(0), Validators.max(100)]],
          plcSlot: [1, [Validators.required, Validators.min(0), Validators.max(18)]],
          pduSize: [10, [Validators.required]],
          requestInterval: [1, [Validators.required]]
        }),
        mqttData: this.fb.group({
          mqttTopic: ['on/ot/devboard', [Validators.required]],
          mqttIp: ['192.168.4.172', [Validators.required, Validators.pattern(/^\d{1,3}(\.\d{1,3}){3}$/)]],
          mqttPort: [1883, [Validators.required, Validators.min(1), Validators.max(65535)]]
        }),
        plcTagData: this.fb.array([this.createPLCTag()])
      });
    }

    /**
     * Create a PLC tag form group.
     * @returns A FormGroup representing a PLC tag.
     */
    debugCreatePLCTag(): FormGroup {
      return this.fb.group({
        tagName: ['lightBarrier', [Validators.required, Validators.pattern(/^[a-zA-Z0-9]+$/)]],
        tagAddress: ['DB9.X1732.1', [Validators.required, Validators.pattern(/^DB\d+\.(X|B|C|W|DW|I|DI|R|DT|S)\d+(\.\d+)?$/)]]
      });
    }
}
