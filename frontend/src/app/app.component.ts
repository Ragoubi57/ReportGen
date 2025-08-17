// frontend/src/app/app.component.ts
import { Component } from '@angular/core';
import { RouterModule } from '@angular/router'; 
import { CommonModule } from '@angular/common';
import { ReportFormComponent } from './components/report-form/report-form.component';
import { AnimatedBackgroundComponent } from './components/animated-background/animated-background.component'; // Import the new component

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule, 
    ReportFormComponent,
    AnimatedBackgroundComponent 
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'AI Report Generator';
  currentYear = new Date().getFullYear();
}