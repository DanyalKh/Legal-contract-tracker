import { Routes } from '@angular/router';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { ContractDetailComponent } from './pages/contract-detail/contract-detail.component';

export const routes: Routes = [
	{ path: '', component: DashboardComponent },
	{ path: 'contracts/:id', component: ContractDetailComponent },
	{ path: '**', redirectTo: '' }
];
