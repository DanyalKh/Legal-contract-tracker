import { Component, ChangeDetectorRef, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

interface ClauseType {
  id: number;
  name: string;
  color: string;
  shortcut?: string;
}

interface SentenceLabel {
  clauseTypeId: number;
  name: string;
  color: string;
}

interface Sentence {
  id: number;
  text: string;
  label: SentenceLabel | null;
}

interface Contract {
  id: number;
  filename: string;
  uploaded_at: string;
}

@Component({
  selector: 'app-contract-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatMenuModule,
    MatDividerModule,
    MatCheckboxModule,
    MatIconModule,
    MatFormFieldModule,
    MatSelectModule,
    MatTooltipModule
  ],
  templateUrl: './contract-detail.component.html',
  styleUrls: ['./contract-detail.component.css']
})
export class ContractDetailComponent {
  constructor(
    private apiService: ApiService,
    private route: ActivatedRoute,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  goBack() {
    this.router.navigate(['/']);
  }

  contract: Contract | null = null;
  sentences: Sentence[] = [];
  clauseTypes: ClauseType[] = [];

  hoveredSentenceId: number | null = null;
  selectedSentenceId: number | null = null;
  selectedSentence: Sentence | null = null;

  bulkMode = false;
  selectedSentences: Sentence[] = [];
  bulkLabelType: ClauseType | null = null;

  suggestedLabels: (ClauseType & { confidence: number })[] = [];
  selectedSuggestionIndex: number = -1;

  private shortcuts: { [key: string]: ClauseType } = {};

  ngOnInit() {
    const contractId = Number(this.route.snapshot.paramMap.get('id'));

    this.apiService.getContract(contractId).subscribe({
      next: (res) => {
        this.contract = {
          id: res.id,
          filename: res.filename,
          uploaded_at: res.uploaded_at
        };

        this.sentences = res.sentences.map((s: any) => ({
          id: s.id,
          text: s.text,
          label: s.label ? {
            clauseTypeId: s.label.clause_type.id,
            name: s.label.clause_type.name,
            color: s.label.clause_type.color
          } : null
        }));

        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Failed to load contract:', err);
        this.sentences = [];
        this.cdr.detectChanges();
      }
    });

    this.apiService.getClauseTypes().subscribe({
      next: (res) => {
        this.clauseTypes = res.map((type: any, index: number) => ({
          ...type,
          shortcut: String(index)
        }));

        this.shortcuts = {};
        this.clauseTypes.forEach(type => {
          if (type.shortcut) {
            this.shortcuts[type.shortcut] = type;
          }
        });

        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Failed to load clause types:', err);
        this.clauseTypes = [];
        this.cdr.detectChanges();
      }
    });
  }

  hover(id: number | null) {
    this.hoveredSentenceId = id;
  }

  onSentenceClick(sentence: Sentence) {
    if (this.bulkMode) {
      this.toggleSentenceSelection(sentence);
    } else {
      this.selectSentence(sentence);
    }
  }

  selectSentence(sentence: Sentence) {
    this.selectedSentenceId = sentence.id;
    this.selectedSentence = sentence;
    this.selectedSuggestionIndex = -1;

    this.loadSuggestions(sentence);
  }

  isSelected(sentenceId: number): boolean {
    return this.selectedSentences.some(s => s.id === sentenceId);
  }

  toggleBulkMode() {
    this.bulkMode = !this.bulkMode;
    if (!this.bulkMode) {
      this.clearSelection();
    }
  }

  toggleSentenceSelection(sentence: Sentence) {
    const index = this.selectedSentences.findIndex(s => s.id === sentence.id);
    if (index > -1) {
      this.selectedSentences.splice(index, 1);
    } else {
      this.selectedSentences.push(sentence);
    }
  }

  clearSelection() {
    this.selectedSentences = [];
  }

  applyBulkLabel() {
    if (!this.bulkLabelType || this.selectedSentences.length === 0) return;

    const promises = this.selectedSentences.map(sentence =>
      this.apiService.labelSentence(sentence.id, this.bulkLabelType!.id).toPromise()
    );

    Promise.all(promises).then(() => {
      this.selectedSentences.forEach(sentence => {
        sentence.label = {
          clauseTypeId: this.bulkLabelType!.id,
          name: this.bulkLabelType!.name,
          color: this.bulkLabelType!.color
        };
      });
      this.clearSelection();
      this.bulkLabelType = null;
      this.cdr.detectChanges();
    }).catch(err => {
      console.error('Bulk labeling failed:', err);
    });
  }

  applyLabelToSentence(sentence: Sentence, clause: ClauseType) {
    const previous = sentence.label;

    sentence.label = {
      clauseTypeId: clause.id,
      name: clause.name,
      color: clause.color
    };

    this.selectedSentence = null;
    this.selectedSentenceId = null;
    this.suggestedLabels = [];
    this.cdr.detectChanges();

    this.apiService.labelSentence(sentence.id, clause.id)
      .subscribe({
        error: (err) => {
          sentence.label = previous;
          console.error('Failed to apply label:', err);
          this.cdr.detectChanges();
        }
      });
  }

  removeLabelFromSentence(sentence: Sentence) {
    const previous = sentence.label;
    sentence.label = null;
    this.selectedSentence = null;
    this.selectedSentenceId = null;
    this.suggestedLabels = [];
    this.cdr.detectChanges();

    this.apiService.removeLabel(sentence.id)
      .subscribe({
        error: (err) => {
          sentence.label = previous;
          console.error('Failed to remove label:', err);
          this.cdr.detectChanges();
        }
      });
  }

  openMenu(sentence: Sentence) {
    this.selectedSentence = sentence;
  }

  private loadSuggestions(sentence: Sentence) {
    const suggestions: (ClauseType & { confidence: number })[] = [];
    const text = sentence.text.toLowerCase();

    this.clauseTypes.forEach(type => {
      const keywords = this.getKeywordsForClauseType(type.name);
      const matches = keywords.filter(keyword => text.includes(keyword)).length;

      if (matches > 0) {
        const confidence = Math.min(0.9, matches * 0.3);
        suggestions.push({ ...type, confidence });
      }
    });

    this.suggestedLabels = suggestions.sort((a, b) => b.confidence - a.confidence);
  }

  private getKeywordsForClauseType(clauseName: string): string[] {
    const keywordMap: { [key: string]: string[] } = {
      'Payment Terms': ['payment', 'fee', 'compensation', 'rate', 'invoice'],
      'Confidentiality': ['confidential', 'disclose', 'secret', 'proprietary'],
      'Termination': ['terminate', 'end', 'cancel', 'expiration'],
      'Liability': ['liability', 'responsible', 'damage', 'loss', 'indemnify'],
      'Intellectual Property': ['intellectual', 'property', 'copyright', 'patent', 'trademark']
    };

    return keywordMap[clauseName] || [];
  }

  @HostListener('document:keydown', ['$event'])
  onKeyDown(event: KeyboardEvent) {
    if (!this.selectedSentence) return;

    if (this.suggestedLabels.length > 0) {
      if (event.key === 'ArrowDown') {
        this.selectedSuggestionIndex = Math.min(
          this.selectedSuggestionIndex + 1,
          this.suggestedLabels.length - 1
        );
        event.preventDefault();
        return;
      }
      if (event.key === 'ArrowUp') {
        this.selectedSuggestionIndex = Math.max(this.selectedSuggestionIndex - 1, -1);
        event.preventDefault();
        return;
      }
      if (event.key === 'Enter' && this.selectedSuggestionIndex >= 0) {
        const suggestion = this.suggestedLabels[this.selectedSuggestionIndex];
        if (suggestion) {
          this.applyLabelToSentence(this.selectedSentence, suggestion);
          event.preventDefault();
          return;
        }
      }
    }

    const clauseType = this.shortcuts[event.key];
    if (clauseType) {
      this.applyLabelToSentence(this.selectedSentence, clauseType);
      event.preventDefault();
      return;
    }

    if (event.key === 'Escape') {
      this.selectedSentence = null;
      this.selectedSentenceId = null;
      this.suggestedLabels = [];
      this.selectedSuggestionIndex = -1;
      event.preventDefault();
      return;
    }

    if ((event.key === 'Delete' || event.key === 'Backspace') && this.selectedSentence.label) {
      this.removeLabelFromSentence(this.selectedSentence);
      event.preventDefault();
      return;
    }
  }

  onSuggestionKeyDown(event: KeyboardEvent, suggestion: ClauseType & { confidence: number }) {
    if (event.key === 'Enter' || event.key === ' ') {
      this.applyLabelToSentence(this.selectedSentence!, suggestion);
      event.preventDefault();
    }
  }

  getCount(clauseId: number): number {
    return this.sentences.filter(s => s.label?.clauseTypeId === clauseId).length;
  }

  getLabeledCount(): number {
    return this.sentences.filter(s => s.label).length;
  }

  getProgress(): number {
    if (this.sentences.length === 0) return 0;
    return (this.getLabeledCount() / this.sentences.length) * 100;
  }

  getIconForClauseType(clauseName: string): string {
    const iconMap: { [key: string]: string } = {
      'Payment Terms': 'payment',
      'Confidentiality': 'security',
      'Termination': 'cancel',
      'Liability': 'gavel',
      'Intellectual Property': 'copyright',
      'Force Majeure': 'warning',
      'Governing Law': 'account_balance',
      'Dispute Resolution': 'forum'
    };
    return iconMap[clauseName] || 'label';
  }

  getShortcutKey(type: ClauseType): string {
    return type.shortcut || '';
  }

  highlightKeywords(text: string): string {
    if (!this.selectedSentence) return text;

    let highlighted = text;
    this.suggestedLabels.forEach(suggestion => {
      const keywords = this.getKeywordsForClauseType(suggestion.name);
      keywords.forEach(keyword => {
        const regex = new RegExp(`(${keyword})`, 'gi');
        highlighted = highlighted.replace(regex, '<mark>$1</mark>');
      });
    });

    return highlighted;
  }

  trackBySentenceId(index: number, sentence: Sentence): number {
    return sentence.id;
  }

}