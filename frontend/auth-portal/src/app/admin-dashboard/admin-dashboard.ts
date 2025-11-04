import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../services/api';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-dashboard.html',
  styleUrls: ['./admin-dashboard.css']
})
export class AdminDashboardComponent {
  isLoggedIn = false;
  username = '';
  password = '';

  newUsername = '';
  newPassword = '';
  resetRequests: string[] = [];

  constructor(public api: ApiService) {}

  // Hardcoded login for admin
  login() {
    if (this.username === 'admin' && this.password === 'admin123') {
      this.isLoggedIn = true;
      alert('Admin login successful!');
      this.loadResetRequests();
    } else {
      alert('Invalid admin credentials!');
    }
  }

  addUser() {
    if (this.newUsername && this.newPassword) {
      this.api.addUser(this.newUsername, this.newPassword);
      alert(`✅ User Created:
Username: ${this.newUsername}
Password: ${this.newPassword}`);
      this.newUsername = '';
      this.newPassword = '';
    } else {
      alert('Please fill in all fields.');
    }
  }

  loadResetRequests() {
    this.resetRequests = this.api.getResetRequests();
  }
  logout() {
  this.isLoggedIn = false;
  this.username = '';
  this.password = '';
  this.newPassword = '';
  
}


  resetPassword(user: string) {
    const newPass = 'newPass' + Math.floor(Math.random() * 1000);
    this.api.updateUserPassword(user, newPass);
    alert(`Password reset for ${user}. New password: ${newPass}`);
    this.loadResetRequests();
  }
}
