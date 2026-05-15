import { Routes } from '@angular/router';

export const appRoutes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'plc-states' },
  {
    path: 'plc-states',
    loadComponent: () =>
      import('./plc-states/plc-states.component').then((m) => m.PlcStatesComponent),
  },
  {
    path: 'configuration-overview',
    loadComponent: () =>
      import('./configuration-overview/configuration-overview.component').then(
        (m) => m.ConfigurationOverviewComponent,
      ),
  },
  {
    path: 'create-configuration',
    loadComponent: () =>
      import('./create-configuration/create-configuration.component').then(
        (m) => m.CreateConfigurationComponent,
      ),
  },
  { path: '**', redirectTo: 'plc-states' },
];
