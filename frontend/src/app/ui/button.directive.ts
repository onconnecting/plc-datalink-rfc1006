import { Directive, HostBinding, Input } from '@angular/core';

export type OcButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';

@Directive({
  selector: 'button[ocButton], a[ocButton]',
  standalone: true,
})
export class OcButtonDirective {
  @Input() variant: OcButtonVariant = 'primary';
  @Input() compact = false;

  @HostBinding('class.oc-button') readonly base = true;

  @HostBinding('class.oc-button--primary')
  get isPrimary(): boolean {
    return this.variant === 'primary';
  }

  @HostBinding('class.oc-button--secondary')
  get isSecondary(): boolean {
    return this.variant === 'secondary';
  }

  @HostBinding('class.oc-button--danger')
  get isDanger(): boolean {
    return this.variant === 'danger';
  }

  @HostBinding('class.oc-button--ghost')
  get isGhost(): boolean {
    return this.variant === 'ghost';
  }

  @HostBinding('class.oc-button--compact')
  get isCompact(): boolean {
    return this.compact;
  }
}
