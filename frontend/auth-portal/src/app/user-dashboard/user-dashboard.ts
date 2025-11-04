import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../services/api';

@Component({
  selector: 'app-user-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './user-dashboard.html',
  styleUrls: ['./user-dashboard.css']
})
export class UserDashboardComponent {
  username = '';
  password = '';
  newPassword = '';
  isLoggedIn = false;

  constructor(private api: ApiService) {}

  login() {
    if (this.api.validateUser(this.username, this.password)) {
      this.isLoggedIn = true;
      alert('Login successful!');
    } else {
      alert('Invalid username or password.');
    }
  }

  forgotPassword() {
    if (!this.username) {
      alert('Please enter your username first.');
      return;
    }
    this.api.requestPasswordReset(this.username);
    alert('Password reset request sent to admin.');
  }
logout() {
  this.isLoggedIn = false;
  this.username = '';
  this.password = '';
  this.newPassword = '';
}

  changePassword() {
    if (this.newPassword) {
      this.api.updateUserPassword(this.username, this.newPassword);
      alert('Password updated successfully!');
      this.newPassword = '';
    } else {
      alert('Enter a new password.');
    }
  }
}
