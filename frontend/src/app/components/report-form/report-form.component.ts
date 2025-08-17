// frontend/src/app/components/report-form/report-form.component.ts
import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators, FormArray, ReactiveFormsModule, AbstractControl } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ReportGeneratorService } from '../../services/report-generator.service';
import { ReportRequest } from '../../models/report-request.model';
import { saveAs } from 'file-saver';
import { LoadingSpinnerComponent } from '../loading-spinner/loading-spinner.component';
import { trigger, style, animate, transition, query, stagger, keyframes } from '@angular/animations';
import { Subject } from 'rxjs';

interface ProgressStep {
  message: string;
  duration: number;
  svgIcon?: string;
}

@Component({
  selector: 'app-report-form',
  standalone: true,
  imports: [ CommonModule, ReactiveFormsModule, LoadingSpinnerComponent ],
  templateUrl: './report-form.component.html',
  styleUrls: ['./report-form.component.scss'],
  animations: [ /* Your existing animations */
    trigger('fadeInOut', [
      transition(':enter', [ style({ opacity: 0, transform: 'translateY(-10px)' }), animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' })) ]),
      transition(':leave', [ animate('300ms ease-in', style({ opacity: 0, transform: 'translateY(-10px)' })) ])
    ]),
    trigger('formArrayItem', [
      transition(':enter', [ style({ opacity: 0, transform: 'translateX(-20px)' }), animate('300ms ease-out', style({ opacity: 1, transform: 'translateX(0)' })) ]),
      transition(':leave', [ animate('300ms ease-in', style({ opacity: 0, transform: 'scale(0.9)' })) ])
    ]),
    trigger('loadingMessageAnimation', [
      transition('* => *', [
        query(':leave', [
          stagger(100, [ animate('350ms ease-in', style({ opacity: 0, transform: 'translateY(20px) scale(0.95)' })) ])
        ], { optional: true }),
        query(':enter', [
          style({ opacity: 0, transform: 'translateY(-20px) scale(0.95)' }),
          stagger(100, [ animate('350ms 100ms cubic-bezier(0.175, 0.885, 0.32, 1.275)', style({ opacity: 1, transform: 'translateY(0) scale(1)' })) ])
        ], { optional: true })
      ])
    ])
  ]
})
export class ReportFormComponent implements OnInit, OnDestroy {
  reportForm!: FormGroup;
  isLoading = false;
  errorMessage: string | null = null;
  successMessage: string | null = null;
  selectedLogoFile: File | null = null;
  selectedUserFigureFile: File | null = null;
  userFigurePreview: string | ArrayBuffer | null = null;

  private ICONS = { /* Your ICONS object */
    BRAIN: "M8.25 3.75H5.25a1.5 1.5 0 00-1.5 1.5v13.5a1.5 1.5 0 001.5 1.5h13.5a1.5 1.5 0 001.5-1.5v-1.5A1.5 1.5 0 0018.75 18H15a1.5 1.5 0 00-1.5 1.5v.75A1.5 1.5 0 0112 21v0a1.5 1.5 0 01-1.5-1.5v-.75a1.5 1.5 0 00-1.5-1.5h-3.75a1.5 1.5 0 00-1.5 1.5v1.5H3.75m0-13.5h16.5m-16.5 0a1.5 1.5 0 011.5-1.5h3.75a1.5 1.5 0 011.5 1.5v1.5A1.5 1.5 0 019 9.75h-.75A1.5 1.5 0 016.75 12v1.5a1.5 1.5 0 01-1.5 1.5H3.75m16.5-7.5h-3.75a1.5 1.5 0 00-1.5 1.5v1.5a1.5 1.5 0 001.5 1.5h.75A1.5 1.5 0 0018 12v-1.5a1.5 1.5 0 00-1.5-1.5m-5.25 0v0a1.5 1.5 0 011.5 1.5v1.5a1.5 1.5 0 01-1.5 1.5h-1.5a1.5 1.5 0 01-1.5-1.5v-1.5A1.5 1.5 0 019.75 6h1.5z",
    SEARCH: "M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z",
    DOCUMENT_TEXT: "M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z",
    PENCIL_SQUARE: "M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10",
    BOOK_OPEN: "M12 6.042A8.955 8.955 0 003.75 3.75c-1.012 0-1.99.264-2.85.738m18.15-.738a8.955 8.955 0 01-8.25 2.292M3.75 3.75a8.955 8.955 0 018.25 2.292m0 0a8.955 8.955 0 008.25-2.292m0 0v1.5M3.75 5.25v1.5m15-3A8.955 8.955 0 0112 6.042m0 0v12.75m0 0a8.955 8.955 0 01-8.25 2.292m8.25-2.292a8.955 8.955 0 008.25-2.292M3.75 18.75a8.955 8.955 0 008.25-2.292m0 0A8.955 8.955 0 0120.25 18.75",
    CLIPBOARD_DOCUMENT_LIST: "M16.5 3.75V16.5L12 14.25 7.5 16.5V3.75m9 0H18A2.25 2.25 0 0120.25 6v12A2.25 2.25 0 0118 20.25H6A2.25 2.25 0 013.75 18V6A2.25 2.25 0 016 3.75h1.5m9 0h-9",
    SPARKLES: "M10.89 3.469c.552-1.001 1.665-1.001 2.218 0l.474.861c.27.492.768.838 1.32.876l.95.063c1.067.071 1.531 1.053.823 1.71l-.735.682a1.523 1.523 0 00-.438 1.695l.288.971c.286.967-.521 1.639-1.432 1.182l-.85-.447a1.523 1.523 0 00-1.705 0l-.85.447c-.91.457-1.718-.215-1.432-1.182l.288-.971a1.523 1.523 0 00-.438-1.695l-.735-.682c-.708-.657-.244-1.639.823-1.71l.95-.063a1.523 1.523 0 001.32-.876l.474-.861zM16.5 7.5c.552-1.001 1.665-1.001 2.218 0l.474.861c.27.492.768.838 1.32.876l.95.063c1.067.071 1.531 1.053.823 1.71l-.735.682a1.523 1.523 0 00-.438 1.695l.288.971c.286.967-.521 1.639-1.432 1.182l-.85-.447a1.523 1.523 0 00-1.705 0l-.85.447c-.91.457-1.718-.215-1.432-1.182l.288-.971a1.523 1.523 0 00-.438-1.695l-.735-.682c-.708-.657-.244-1.639.823-1.71l.95-.063a1.523 1.523 0 001.32-.876l.474-.861zM7.5 16.5c.552-1.001 1.665-1.001 2.218 0l.474.861c.27.492.768.838 1.32.876l.95.063c1.067.071 1.531 1.053.823 1.71l-.735.682a1.523 1.523 0 00-.438 1.695l.288.971c.286.967-.521 1.639-1.432 1.182l-.85-.447a1.523 1.523 0 00-1.705 0l-.85.447c-.91.457-1.718-.215-1.432-1.182l.288-.971a1.523 1.523 0 00-.438-1.695l-.735-.682c-.708-.657-.244-1.639.823-1.71l.95-.063a1.523 1.523 0 001.32-.876l.474-.861z",
    COG: "M10.343 3.94c.09-.542.56-1.007 1.11-.962a8.958 8.958 0 017.332 7.332c.046.55-.42.996-.962 1.11-.245.062-.498.102-.748.152l-.544.119a8.958 8.958 0 00-7.332-7.332c-.05-.25-.09-.496-.152-.748l-.119-.544zM12 12.75a1.5 1.5 0 100-3 1.5 1.5 0 000 3z"
  };
  public baseProgressSteps: ProgressStep[] = [ /* Your baseProgressSteps array */
    { message: "Initializing AI Cores...", duration: 2500, svgIcon: this.ICONS.BRAIN },
    { message: "Analyzing Your Query...", duration: 3500, svgIcon: this.ICONS.SEARCH },
    { message: "Structuring Report Outline...", duration: 5000, svgIcon: this.ICONS.PENCIL_SQUARE },
    { message: "Drafting Introduction...", duration: 4000, svgIcon: this.ICONS.DOCUMENT_TEXT },
    { message: "Generating Core Content Sections...", duration: 10000, svgIcon: this.ICONS.BOOK_OPEN },
    { message: "Crafting Supplementary Materials...", duration: 4500, svgIcon: this.ICONS.CLIPBOARD_DOCUMENT_LIST },
    { message: "Finalizing & Polishing Details...", duration: 5000, svgIcon: this.ICONS.SPARKLES },
    { message: "Compiling Your Masterpiece...", duration: 6000, svgIcon: this.ICONS.COG }
  ];
  currentProgressStep: ProgressStep = this.baseProgressSteps[0];
  private progressTimeoutId: any;
  public currentProgressIndex = 0;
  private destroy$ = new Subject<void>();

  initialColorHex = '#7F00FF';
  initialColorRgb = '127, 0, 255';

  constructor(
    private fb: FormBuilder,
    private reportService: ReportGeneratorService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.reportForm = this.fb.group({
      title: ['', [Validators.required, Validators.minLength(5)]],
      query: ['', [Validators.required, Validators.minLength(20)]],
      authors: this.fb.array([this.createAuthorItem()], Validators.required),
      date: [''],
      mentors: this.fb.array([]),
      university: [''],
      colorHex: [this.initialColorHex],
      colorRgb: [this.initialColorRgb, [Validators.required, Validators.pattern(/^\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*$/)]],
      no_rag: [false],
      userFigureCaption: ['']
    });
  }

  ngOnDestroy(): void { clearTimeout(this.progressTimeoutId); this.destroy$.next(); this.destroy$.complete(); }
  createAuthorItem(name: string = ''): FormGroup { return this.fb.group({ name: [name, Validators.required] }); }
  createMentorItem(name: string = ''): FormGroup { return this.fb.group({ name: [name] }); }
  getControl(formArrayName: string, index: number, controlName: string): AbstractControl | null {
    const fa = this.reportForm.get(formArrayName) as FormArray; return fa.at(index)?.get(controlName);
  }
  get authors(): FormArray { return this.reportForm.get('authors') as FormArray; }
  addAuthor(): void { this.authors.push(this.createAuthorItem()); }
  removeAuthor(index: number): void { if (this.authors.length > 1) { this.authors.removeAt(index); } }
  get mentors(): FormArray { return this.reportForm.get('mentors') as FormArray; }
  addMentor(): void { this.mentors.push(this.createMentorItem()); }
  removeMentor(index: number): void { this.mentors.removeAt(index); }
  onLogoFileSelected(event: Event): void {
    const el = event.currentTarget as HTMLInputElement;
    this.selectedLogoFile = (el.files && el.files.length > 0) ? el.files[0] : null;
  }
  clearLogoFile(): void {
    this.selectedLogoFile = null;
    const logoInput = document.getElementById('logo-upload-trigger') as HTMLInputElement;
    if (logoInput) logoInput.value = '';
  }
  onUserFigureSelected(event: Event): void {
    const element = event.currentTarget as HTMLInputElement;
    const fileList: FileList | null = element.files;
    if (fileList && fileList.length > 0) {
      this.selectedUserFigureFile = fileList[0];
      const reader = new FileReader();
      reader.onload = () => { this.userFigurePreview = reader.result; this.cdr.detectChanges(); };
      reader.readAsDataURL(this.selectedUserFigureFile);
    } else {
      this.selectedUserFigureFile = null; this.userFigurePreview = null;
    }
  }
  clearUserFigureFile(): void {
    this.selectedUserFigureFile = null; this.userFigurePreview = null;
    this.reportForm.get('userFigureCaption')?.setValue('');
    const figureInput = document.getElementById('user-figure-upload-trigger') as HTMLInputElement;
    if (figureInput) figureInput.value = '';
  }
  onColorHexChange(event: Event): void {
    const hex = (event.target as HTMLInputElement).value; const rgb = this.hexToRgbArray(hex);
    if (rgb) { this.reportForm.get('colorRgb')?.setValue(`${rgb[0]}, ${rgb[1]}, ${rgb[2]}`, { emitEvent: false }); }
  }
  onColorRgbChange(event: Event): void {
    const rgb = (event.target as HTMLInputElement).value; const hex = this.rgbStringToHex(rgb);
    if (hex && this.reportForm.get('colorRgb')?.valid) { this.reportForm.get('colorHex')?.setValue(hex, { emitEvent: false }); }
  }
  private hexToRgbArray(h:string):[number,number,number]|null{const r=/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(h);return r?[parseInt(r[1],16),parseInt(r[2],16),parseInt(r[3],16)]:null;}
  private cTH(c:number):string{const h=c.toString(16);return h.length===1?"0"+h:h;}
  private rgbStringToHex(rgb:string):string|null{const arr=rgb.split(',').map(s=>parseInt(s.trim(),10));return arr.length===3&&arr.every(n=>!isNaN(n)&&n>=0&&n<=255)?"#"+this.cTH(arr[0])+this.cTH(arr[1])+this.cTH(arr[2]):null;}
  private startProgressSimulation(isRagEnabled:boolean):void{
    let actualProgressSteps=[...this.baseProgressSteps];if(isRagEnabled){actualProgressSteps.splice(2,0,{message:"Retrieving Contextual Documents (RAG)...",duration:7000,svgIcon:this.ICONS.BOOK_OPEN});}
    this.currentProgressIndex=0;this.currentProgressStep=actualProgressSteps[this.currentProgressIndex];this.cdr.detectChanges();
    const nextStep=()=>{this.currentProgressIndex++;if(this.currentProgressIndex<actualProgressSteps.length&&this.isLoading){this.currentProgressStep=actualProgressSteps[this.currentProgressIndex];this.cdr.detectChanges();this.progressTimeoutId=setTimeout(nextStep,this.currentProgressStep.duration);}else if(this.isLoading){this.currentProgressStep=actualProgressSteps[actualProgressSteps.length-1];this.cdr.detectChanges();}};
    this.progressTimeoutId=setTimeout(nextStep,this.currentProgressStep.duration);
  }

  onSubmit(): void {
    this.errorMessage = null; this.successMessage = null; clearTimeout(this.progressTimeoutId);
    if (this.reportForm.invalid) {
      this.errorMessage = "Please review the form. Some fields are invalid or missing.";
      this.reportForm.markAllAsTouched();
      const firstInvalid = document.querySelector('.ng-invalid[formControlName], .ng-invalid[formGroupName]');
      if (firstInvalid) { (firstInvalid as HTMLElement).focus(); firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
      return;
    }
    this.isLoading = true; const isRagEnabled = !this.reportForm.value.no_rag; this.startProgressSimulation(isRagEnabled);

    const formVal = this.reportForm.value;
    const requestPayload: ReportRequest = {
      title: formVal.title,
      query: formVal.query,
      authors: formVal.authors.map((a: { name: string }) => a.name).filter(Boolean),
      date: formVal.date || undefined,
      mentors: formVal.mentors.map((m: { name: string }) => m.name).filter(Boolean),
      university: formVal.university || undefined,
      logo: this.selectedLogoFile,
      color: formVal.colorRgb,
      no_rag: formVal.no_rag, // This is correct as per your model
      user_figure: this.selectedUserFigureFile,
      user_figure_caption: formVal.userFigureCaption || undefined
    };

    this.reportService.generateReport(requestPayload).subscribe({
      next: (blob) => {
        clearTimeout(this.progressTimeoutId); this.isLoading = false;
        const reportTitle = (requestPayload.title || 'report').replace(/[^a-z0-9_.-]/gi, '_').toLowerCase();
        saveAs(blob, `${reportTitle}.pdf`);
        this.successMessage = 'Masterpiece Complete! Your report is downloading.';
        setTimeout(() => this.successMessage = null, 8000);
      },
      error: (err) => {
        clearTimeout(this.progressTimeoutId); this.isLoading = false;
        this.errorMessage = `Report Generation Failed: ${err.message || 'An unexpected issue occurred.'}`;
        console.error('Report generation error (component):', err);
      }
    });
  }
}