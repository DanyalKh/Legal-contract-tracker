import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

/* Material */
import { MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-upload-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule
  ],
  templateUrl: './upload-dialog.component.html',
  styleUrls: ['./upload-dialog.component.css']
})
export class UploadDialogComponent {

  file: File | null = null;

  constructor(private dialogRef: MatDialogRef<UploadDialogComponent>) {}

  onFileSelected(event: any) {
    this.file = event.target.files[0];
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    if (event.dataTransfer?.files.length) {
      this.file = event.dataTransfer.files[0];
    }
  }

  allowDrop(event: DragEvent) {
    event.preventDefault();
  }

  submit() {
    if (!this.file) return;

    // TODO: API call later
    console.log('Uploading:', this.file);

    this.dialogRef.close(this.file);
  }

  close() {
    this.dialogRef.close();
  }
}