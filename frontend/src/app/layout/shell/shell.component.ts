import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

/* Angular Material */
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';

/* Your component */
import { UploadDialogComponent } from '../../components/upload-dialog/upload-dialog.component';

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [
    RouterOutlet,
    MatToolbarModule,
    MatButtonModule,
    MatDialogModule
  ],
  templateUrl: './shell.component.html',
  styleUrls: ['./shell.component.css']
})
export class ShellComponent {

  constructor(private dialog: MatDialog) {}

  openUpload() {
    this.dialog.open(UploadDialogComponent, {
      width: '400px'
    });
  }
}