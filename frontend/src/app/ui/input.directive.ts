import { Directive, HostBinding } from '@angular/core';

@Directive({
  selector: 'input[ocInput], select[ocInput], textarea[ocInput]',
  standalone: true,
})
export class OcInputDirective {
  @HostBinding('class.oc-input') readonly base = true;
}
