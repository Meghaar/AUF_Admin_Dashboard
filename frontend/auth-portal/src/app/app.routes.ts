import { Routes } from '@angular/router';
import { LandingPageComponent } from './landing-page/landing-page';
import { AdminDashboardComponent } from './admin-dashboard/admin-dashboard';
import { UserDashboardComponent } from './user-dashboard/user-dashboard';

export const routes: Routes = [
  { path: '', component: LandingPageComponent },
  { path: 'admin', component: AdminDashboardComponent },
  { path: 'user', component: UserDashboardComponent }
];
