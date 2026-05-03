import { Component, ChangeDetectorRef, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { UploadDialogComponent } from '../../components/upload-dialog/upload-dialog.component';
import { ApiService } from '../../services/api.service';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';

/* Material */
import { MatCardModule } from '@angular/material/card';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    MatCardModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatSelectModule,
    MatProgressBarModule,
    MatSlideToggleModule,
    MatChipsModule,
    MatTooltipModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})

export class DashboardComponent implements OnInit, OnDestroy {

  search = '';
  selectedClauseTypeId: number | null = null;
  sortBy = 'uploaded_desc';
  viewMode: 'grid' | 'list' = 'grid';
  groupByClause = false;

  contracts: any[] = [];
  clauseTypes: any[] = [];
  filteredContracts: any[] = [];
  progressChange: number = 0;
  labelingTrend: number = 0;

  private searchSubject = new Subject<string>();
  private destroy$ = new Subject<void>();

  constructor(
    private dialog: MatDialog,
    private apiService: ApiService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit() {
    // Load initial data
    this.loadContracts();
    this.loadClauseTypes();

    // Initialize mock data
    this.progressChange = Math.floor(Math.random() * 20) - 5;
    this.labelingTrend = Math.floor(Math.random() * 10);

    // Setup debounced search
    this.searchSubject
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        takeUntil(this.destroy$)
      )
      .subscribe(() => {
        this.loadContracts();
      });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onSearchChange(value: string) {
    this.search = value;
    this.searchSubject.next(value);
  }

  onClauseTypeChange(clauseTypeId: number | null) {
    this.selectedClauseTypeId = clauseTypeId;
    this.loadContracts();
  }

  onSortChange(sortBy: string) {
    this.sortBy = sortBy;
    this.applyFilters();
  }

  clearFilters() {
    this.search = '';
    this.selectedClauseTypeId = null;
    this.sortBy = 'uploaded_desc';
    this.groupByClause = false;
    this.loadContracts();
  }

  toggleGroupView() {
    this.loadContracts();
  }


  setViewMode(mode: 'grid' | 'list') {
    this.viewMode = mode;
  }

  loadContracts() {
    this.apiService.getContracts(
      this.search || undefined,
      this.selectedClauseTypeId || undefined,
      this.groupByClause
    )
    .pipe(takeUntil(this.destroy$))
    .subscribe({
      next: (data) => {
        console.log('loadContracts received data:', data);
        console.log('First contract structure:', data && data.length > 0 ? data[0] : 'No contracts');
        if (data && data.length > 0) {
          console.log('First contract keys:', Object.keys(data[0]));
          console.log('First contract filename:', data[0].filename);
          console.log('First contract uploaded_at:', data[0].uploaded_at);
          console.log('First contract total_sentences:', data[0].total_sentences);
          console.log('First contract labeled_count:', data[0].labeled_count);
        }
        if (this.groupByClause) {
          this.contracts = data || [];
          this.filteredContracts = [];
        } else {
          this.contracts = data || [];
          this.applyFilters();
        }
        console.log('contracts set to:', this.contracts);
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Failed to load contracts:', err);
        this.contracts = [];
        this.filteredContracts = [];
      }
    });
  }

  loadClauseTypes() {
    this.apiService.getClauseTypes()
    .pipe(takeUntil(this.destroy$))
    .subscribe({
      next: (data) => {
        this.clauseTypes = (data || []).filter((type: any) => type && type.id && type.name && type.color);
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Failed to load clause types:', err);
        this.clauseTypes = [];
      }
    });
  }

  applyFilters() {
    if (!this.contracts) {
      this.filteredContracts = [];
      return;
    }
    let filtered = [...this.contracts];

    // Apply search filter
    if (this.search) {
      const searchLower = this.search.toLowerCase();
      filtered = filtered.filter(c =>
        c && c.filename && c.filename.toLowerCase().includes(searchLower)
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      if (!a || !b) return 0;
      switch (this.sortBy) {
        case 'uploaded_desc':
          const aTime = a.uploaded_at ? new Date(a.uploaded_at).getTime() : 0;
          const bTime = b.uploaded_at ? new Date(b.uploaded_at).getTime() : 0;
          return bTime - aTime;
        case 'uploaded_asc':
          const aTimeAsc = a.uploaded_at ? new Date(a.uploaded_at).getTime() : 0;
          const bTimeAsc = b.uploaded_at ? new Date(b.uploaded_at).getTime() : 0;
          return aTimeAsc - bTimeAsc;
        case 'filename':
          const aName = a.filename || '';
          const bName = b.filename || '';
          return aName.localeCompare(bName);
        case 'progress_desc':
          return this.getProgress(b) - this.getProgress(a);
        case 'progress_asc':
          return this.getProgress(a) - this.getProgress(b);
        default:
          return 0;
      }
    });

    this.filteredContracts = filtered;
    this.cdr.detectChanges();
  }

  getProgress(c: any) {
    if (!c || !c.total_sentences || !c.labeled_count) return 0;
    return c.total_sentences > 0 ? (c.labeled_count / c.total_sentences) * 100 : 0;
  }

  getUnlabeledCount(c: any) {
    if (!c || !c.total_sentences || !c.labeled_count) return 0;
    return c.total_sentences - c.labeled_count;
  }

  getAverageProgress() {
    if (!this.contracts || this.contracts.length === 0) return 0;
    const validContracts = this.contracts.filter(c => c && c.total_sentences !== undefined && c.labeled_count !== undefined);
    if (validContracts.length === 0) return 0;
    const total = validContracts.reduce((sum, c) => sum + this.getProgress(c), 0);
    return total / validContracts.length;
  }

  getRecentActivity() {
    // Mock recent activity - in real app, check contracts modified today
    if (!this.contracts) return 0;
    return this.contracts.filter(c => {
      if (!c || !c.uploaded_at) return false;
      const today = new Date();
      const uploadDate = new Date(c.uploaded_at);
      return uploadDate.toDateString() === today.toDateString();
    }).length;
  }

  getStatusColor(c: any) {
    const progress = this.getProgress(c);
    if (progress === 100) return 'warn'; // green
    if (progress > 50) return 'accent'; // yellow
    return 'primary'; // blue
  }

  getStatusText(c: any) {
    const progress = this.getProgress(c);
    if (progress === 100) return 'Complete';
    if (progress > 50) return 'In Progress';
    return 'Not Started';
  }

  getGroupTotalSentences(group: any) {
    return group.contracts?.reduce((sum: number, contract: any) => sum + (contract.total_sentences || 0), 0) || 0;
  }

  getGroupTotalLabeled(group: any) {
    return group.contracts?.reduce((sum: number, contract: any) => sum + (contract.labeled_count || 0), 0) || 0;
  }

  getGroupAverageProgress(group: any) {
    if (!group.contracts || group.contracts.length === 0) return 0;
    const totalProgress = group.contracts.reduce((sum: number, contract: any) => sum + this.getProgress(contract), 0);
    return totalProgress / group.contracts.length;
  }

  trackByTypeId(index: number, group: any) {
    return group.clause_type?.id || index;
  }

  trackByContractId(index: number, contract: any) {
    return contract.id || index;
  }

  getTrendIcon(change: number) {
    return change > 0 ? 'trending_up' : 'trending_down';
  }

  refreshData() {
    this.loadContracts();
    this.loadClauseTypes();
  }

  downloadContract(contract: any) {
    this.apiService.downloadContract(contract.id).subscribe({
      next: (blob: Blob) => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = contract.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      },
      error: (err) => {
        console.error('Failed to download contract:', err);
        alert('Failed to download contract. Please try again.');
      }
    });
  }

  deleteContract(contract: any) {
    if (confirm(`Are you sure you want to delete "${contract.filename}"?`)) {
      this.apiService.deleteContract(contract.id).subscribe({
        next: () => {
          this.loadContracts();
        },
        error: (err) => {
          console.error('Failed to delete contract:', err);
        }
      });
    }
  }

  openUpload() {
    this.dialog.open(UploadDialogComponent, {
      panelClass: 'upload-modal'
    })
    .afterClosed()
    .subscribe(file => {

      if (!file) return;

      console.log('File received in dashboard:', file);

      this.apiService.uploadContract(file).subscribe({
        next: (res) => {
          console.log('Upload successful:', res);

          // 🔄 refresh dashboard data
          this.loadContracts();
        },
        error: (err) => {
          console.error('Upload failed:', err);
        }
      });

    });
  }
}