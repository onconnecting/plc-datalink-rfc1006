import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
    selector: 'confirmation-dialog',  
    templateUrl: './confirmation-dialog.component.html',
    styleUrls: ['./confirmation-dialog.component.css'],
})
export class ConfirmationDialogComponent {
    @Input() title: string;
    @Input() message: string;
    @Output() onConfirm: EventEmitter<any> = new EventEmitter();
    @Output() onDecline: EventEmitter<any> = new EventEmitter();

    confirm() {
        this.onConfirm.emit();
    }

    decline() {
        this.onDecline.emit();
    }
}
