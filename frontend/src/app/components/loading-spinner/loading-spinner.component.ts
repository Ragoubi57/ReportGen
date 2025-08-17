// frontend/src/app/components/loading-spinner/loading-spinner.component.ts
import { Component } from '@angular/core';
// CommonModule is not strictly necessary if the template is just <div class="spinner"></div>
// but doesn't hurt to include it if you might add *ngIf etc. later.
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './loading-spinner.component.html',
  styleUrls: ['./loading-spinner.component.scss']
})
export class LoadingSpinnerComponent {}