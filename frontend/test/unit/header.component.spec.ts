import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { HeaderComponent } from '../../src/app/header/header.component';

describe('HeaderComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HeaderComponent],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('instantiates', () => {
    const fixture = TestBed.createComponent(HeaderComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('renders the three primary navigation links', () => {
    const fixture = TestBed.createComponent(HeaderComponent);
    fixture.detectChanges();
    const links: HTMLElement[] = Array.from(
      fixture.nativeElement.querySelectorAll('a[routerLink]'),
    );
    const targets = links.map((a) => a.getAttribute('routerLink') ?? a.getAttribute('ng-reflect-router-link'));
    expect(targets).toEqual(
      expect.arrayContaining(['/plc-states', '/configuration-overview', '/create-configuration']),
    );
  });
});
