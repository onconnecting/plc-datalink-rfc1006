import { Component, EventEmitter, OnInit, Output } from '@angular/core';

@Component({
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrl: './header.component.css'
})
export class HeaderComponent implements OnInit{

  @Output() featureSelected=new EventEmitter<string>();
  constructor(){}

  onSelect(feature:string){
    this.featureSelected.emit(feature);

  }


  ngOnInit() {
  }
  collapsed = true;

}
