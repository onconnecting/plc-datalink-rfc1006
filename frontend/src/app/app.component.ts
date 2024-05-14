import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'plc-datalink-rfc1006';

  loadedPlcConfiguration='plc-configuration';
  loadedPlcState='plc-state'
  loadedConfigurationOverview='configuration-overview'
  loadedCreateConfiguration='create-configuration'

  onNavigate(feature:string){
    this.loadedPlcConfiguration=feature;
    this.loadedPlcState=feature;
    this.loadedConfigurationOverview=feature;
    this.loadedCreateConfiguration=feature;
  }
}
