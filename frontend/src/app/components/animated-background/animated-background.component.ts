import { Component, OnInit, OnDestroy, HostListener, ChangeDetectionStrategy, ChangeDetectorRef, Inject, PLATFORM_ID, NgZone, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { isPlatformBrowser, CommonModule } from '@angular/common';
import { trigger, style, animate, transition, keyframes } from '@angular/animations';
import { Subject, interval, takeUntil } from 'rxjs';

interface Point { x: number; y: number; id: number; }
interface Line { p1: Point; p2: Point; id: number; state: 'entering' | 'visible' | 'leaving'; }

@Component({
  selector: 'app-animated-background',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './animated-background.component.html',
  styleUrls: ['./animated-background.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('lineAnimation', [
      transition('* => entering', [
        style({ opacity: 0, strokeDasharray: '1000', strokeDashoffset: '1000' }),
        animate('800ms ease-out', keyframes([
          style({ opacity: 0.4, strokeDashoffset: '1000', offset: 0 }),
          style({ opacity: 0.8, strokeDashoffset: '0', offset: 0.7 }),
          style({ opacity: 0.6, strokeDashoffset: '0', offset: 1.0 })
        ]))
      ]),
      transition('visible => leaving', [
        animate('800ms ease-in', keyframes([
          style({ opacity: 0.6, strokeDashoffset: '0', offset: 0 }),
          style({ opacity: 0.2, strokeDashoffset: '-1000', offset: 0.3 }),
          style({ opacity: 0, strokeDashoffset: '-1000', offset: 1.0 })
        ]))
      ]),
    ])
  ]
})
export class AnimatedBackgroundComponent implements OnInit, OnDestroy {
  svgWidth: number = 0; svgHeight: number = 0; points: Point[] = []; lines: Line[] = [];
  private readonly MAX_POINTS = 35; private readonly MAX_LINES = 20;
  private readonly CONNECTION_RADIUS = 220; private readonly POINT_LIFE_MIN = 4000;
  private readonly POINT_LIFE_MAX = 8000; private readonly LINE_UPDATE_INTERVAL = 1000;
  private readonly POINT_ADD_INTERVAL = 750; private readonly LINE_ANIMATION_DURATION = 800;
  private destroy$ = new Subject<void>(); private pointIdCounter = 0; private lineIdCounter = 0;
  private isBrowser: boolean;

  constructor(private cdr: ChangeDetectorRef, @Inject(PLATFORM_ID) platformId: Object, private ngZone: NgZone) {
    this.isBrowser = isPlatformBrowser(platformId);
    if (this.isBrowser) { this.svgWidth = window.innerWidth; this.svgHeight = window.innerHeight; }
    else { this.svgWidth = 1920; this.svgHeight = 1080; }
  }
  @HostListener('window:resize', ['$event']) onResize(event?: Event): void {
    if (this.isBrowser) { this.ngZone.run(() => { this.svgWidth = window.innerWidth; this.svgHeight = window.innerHeight; this.cdr.detectChanges(); }); }
  }
  ngOnInit(): void { if (this.isBrowser) { this.generateInitialPoints(); this.startPointLifecycle(); this.startLineFormation(); } }
  ngOnDestroy(): void { this.destroy$.next(); this.destroy$.complete(); }
  private generateInitialPoints(): void { if (!this.isBrowser) return; for (let i = 0; i < this.MAX_POINTS; i++) { this.addPoint(); } }
  private addPoint(): Point | null {
    if (!this.isBrowser) return null;
    const newPoint: Point = { x: Math.random() * this.svgWidth, y: Math.random() * this.svgHeight, id: this.pointIdCounter++ };
    this.points.push(newPoint);
    setTimeout(() => {
      this.points = this.points.filter(p => p.id !== newPoint.id);
      this.removeLinesConnectedToPoint(newPoint.id); this.cdr.detectChanges();
    }, Math.random() * (this.POINT_LIFE_MAX - this.POINT_LIFE_MIN) + this.POINT_LIFE_MIN);
    return newPoint;
  }
  private startPointLifecycle(): void {
    if (!this.isBrowser) return;
    this.ngZone.runOutsideAngular(() => {
      interval(this.POINT_ADD_INTERVAL).pipe(takeUntil(this.destroy$)).subscribe(() => {
        if (this.points.length < this.MAX_POINTS) { this.ngZone.run(() => { this.addPoint(); this.cdr.detectChanges(); }); }
      });
    });
  }
  private startLineFormation(): void {
    if (!this.isBrowser) return;
    this.ngZone.runOutsideAngular(() => {
      interval(this.LINE_UPDATE_INTERVAL).pipe(takeUntil(this.destroy$)).subscribe(() => {
        this.ngZone.run(() => { this.formNewLines(); this.cdr.detectChanges(); });
      });
    });
  }
  private formNewLines(): void {
    if (!this.isBrowser) return; const newLines: Line[] = []; const availablePoints = [...this.points];
    if (this.lines.length > this.MAX_LINES * 0.6) {
      const linesToRemoveCount = Math.max(0, this.lines.length - Math.floor(this.MAX_LINES * 0.4));
      for (let i = 0; i < linesToRemoveCount; i++) {
        const idx = Math.floor(Math.random() * this.lines.length);
        if (this.lines[idx] && this.lines[idx].state === 'visible') { this.lines[idx].state = 'leaving'; }
      }
    }
    setTimeout(() => { this.lines = this.lines.filter(l => l.state !== 'leaving'); this.cdr.detectChanges(); }, this.LINE_ANIMATION_DURATION);
    for (let i = 0; i < availablePoints.length; i++) {
      for (let j = i + 1; j < availablePoints.length; j++) {
        if (this.lines.filter(l => l.state !== 'leaving').length + newLines.length >= this.MAX_LINES) break;
        const p1 = availablePoints[i]; const p2 = availablePoints[j];
        const dist = Math.sqrt(Math.pow(p1.x - p2.x, 2) + Math.pow(p1.y - p2.y, 2));
        if (dist < this.CONNECTION_RADIUS && dist > 20) {
          const exists = this.lines.some(l => (l.p1.id === p1.id && l.p2.id === p2.id) || (l.p1.id === p2.id && l.p2.id === p1.id)) || newLines.some(l => (l.p1.id === p1.id && l.p2.id === p2.id) || (l.p1.id === p2.id && l.p2.id === p1.id));
          if (!exists) {
            const nL: Line = { p1, p2, id: this.lineIdCounter++, state: 'entering' }; newLines.push(nL);
            setTimeout(() => { const line = this.lines.find(l => l.id === nL.id); if (line) line.state = 'visible'; this.cdr.detectChanges(); }, this.LINE_ANIMATION_DURATION);
          }
        }
      } if (this.lines.filter(l => l.state !== 'leaving').length + newLines.length >= this.MAX_LINES) break;
    } this.lines = [...this.lines, ...newLines];
  }
  private removeLinesConnectedToPoint(pointId: number): void {
    if (!this.isBrowser) return;
    this.lines.forEach(l => { if ((l.p1.id === pointId || l.p2.id === pointId) && l.state === 'visible') { l.state = 'leaving'; } });
    setTimeout(() => { this.lines = this.lines.filter(l => l.p1.id !== pointId && l.p2.id !== pointId && l.state !== 'leaving'); this.cdr.detectChanges(); }, this.LINE_ANIMATION_DURATION);
  }
  trackByLineId(index: number, line: Line): number { return line.id; }
  trackByPointId(index: number, point: Point): number { return point.id; }
}