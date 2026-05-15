import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HeaderComponent } from './header/header.component';
import { OcToastHostComponent } from './ui';

@Component({
  selector: 'oc-root',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent, OcToastHostComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent {}
