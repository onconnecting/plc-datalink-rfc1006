import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule, Routes } from '@angular/router';

import { AppComponent } from './app.component';
import { HeaderComponent } from './header/header.component';
import { PlcStates } from './plc-states/plc-states.component';
import { ConfigurationOverviewComponent } from './configuration-overview/configuration-overview.component';
import { CreateConfigurationComponent } from './create-configuration/create-configuration.component';
import { ConfirmationDialogComponent } from './modals/confirmation-dialog.component';

import { ConfigurationDataService } from './services/configuration-data.service';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';


const appRouters: Routes=[
  {path: '', component: PlcStates},
  {path: 'plc-states', component: PlcStates},
  {path: 'configuration-overview', component:ConfigurationOverviewComponent},
  {path: 'create-configuration', component: CreateConfigurationComponent }
]

@NgModule({
  declarations: [
    AppComponent,
    HeaderComponent,
    PlcStates,
    ConfigurationOverviewComponent,
    CreateConfigurationComponent,
    ConfirmationDialogComponent,
  ],
  imports: [
    BrowserModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule.forRoot(appRouters),
    HttpClientModule
  ],
  exports: [
    RouterModule
  ],
  providers: [ConfigurationDataService],
  bootstrap: [AppComponent]
})
export class AppModule { }
