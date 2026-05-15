import { AbstractControl, ValidationErrors, ValidatorFn, Validators } from '@angular/forms';

// IPv4 dotted quad with each octet 0-255.
const IPV4_OCTET = '(25[0-5]|2[0-4]\\d|1\\d\\d|[1-9]?\\d)';
const IPV4_REGEX = new RegExp(`^${IPV4_OCTET}(\\.${IPV4_OCTET}){3}$`);

// PLC tag address: <area>.<type><address>[.extra]
// Areas: DB only (per existing legacy regex)
// Types: X, B, C, W, DW, I, DI, R, DT, S
export const PLC_ADDRESS_REGEX = /^DB\d+\.(X|B|C|W|DW|I|DI|R|DT|S)\d+(\.\d+)?$/;

// Tag name: alphanumeric only (matches legacy + backend).
export const TAG_NAME_REGEX = /^[a-zA-Z0-9]+$/;

export function ipv4Validator(control: AbstractControl): ValidationErrors | null {
  const value = control.value;
  if (value === null || value === undefined || value === '') {
    return null;
  }
  return IPV4_REGEX.test(String(value)) ? null : { ipv4: true };
}

export function plcAddressValidator(control: AbstractControl): ValidationErrors | null {
  const value = control.value;
  if (value === null || value === undefined || value === '') {
    return null;
  }
  return PLC_ADDRESS_REGEX.test(String(value)) ? null : { plcAddress: true };
}

export function tagNameValidator(control: AbstractControl): ValidationErrors | null {
  const value = control.value;
  if (value === null || value === undefined || value === '') {
    return null;
  }
  return TAG_NAME_REGEX.test(String(value)) ? null : { tagName: true };
}

export const portValidators: ValidatorFn[] = [
  Validators.required,
  Validators.min(1),
  Validators.max(65535),
];

export const rackValidators: ValidatorFn[] = [
  Validators.required,
  Validators.min(0),
  Validators.max(100),
];

export const slotValidators: ValidatorFn[] = [
  Validators.required,
  Validators.min(0),
  Validators.max(18),
];

export const pduSizeValidators: ValidatorFn[] = [
  Validators.required,
  Validators.min(1),
];

export const requestIntervalValidators: ValidatorFn[] = [
  Validators.required,
  Validators.min(1),
];
