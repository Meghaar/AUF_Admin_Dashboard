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
  oldPassword = '';
  confirmPassword = '';
  isLoggedIn = false;
  
  // Modal states
  showForgotPasswordModal = false;
  showChangePasswordModal = false;
  
  // Forgot password
  forgotPasswordUsername = '';
  forgotPasswordEmail = '';
  
  // Loading states
  isLoading = false;
  loginError = '';
  changePasswordError = '';
  forgotPasswordError = '';

  constructor(private api: ApiService) {}

  // User login - Backend integration
  login() {
    if (!this.username || !this.password) {
      this.loginError = 'Please enter both username and password';
      return;
    }

    this.isLoading = true;
    this.loginError = '';

    this.api.userLogin(this.username, this.password).subscribe({
      next: (response) => {
        this.isLoading = false;
        if (response.access_token) {
          this.isLoggedIn = true;
          this.loginError = '';
          console.log('Login successful:', response);
        } else {
          this.loginError = response.message || 'Login failed';
        }
      },
      error: (error) => {
        this.isLoading = false;
        this.loginError = error.error?.error || 'Login failed. Please try again.';
        console.error('Login error:', error);
      }
    });
  }

  // Open Forgot Password Modal
  openForgotPasswordModal() {
    this.showForgotPasswordModal = true;
    this.forgotPasswordUsername = '';
    this.forgotPasswordEmail = '';
    this.forgotPasswordError = '';
  }

  // Submit forgot password request
  submitForgotPassword() {
    if (!this.forgotPasswordUsername || !this.forgotPasswordEmail) {
      this.forgotPasswordError = 'Please enter both username and email.';
      return;
    }

    this.isLoading = true;
    this.forgotPasswordError = '';

    this.api.requestPasswordReset(this.forgotPasswordUsername, this.forgotPasswordEmail).subscribe({
      next: (response) => {
        this.isLoading = false;
        if (response.success) {
          alert(`✅ Password Reset Request Submitted!\n\nYour request has been sent to the admin.\nUsername: ${this.forgotPasswordUsername}\nEmail: ${this.forgotPasswordEmail}\n\nThe admin will review your request and send new credentials to your email.`);
          this.closeForgotPasswordModal();
        } else {
          this.forgotPasswordError = response.message || 'Failed to submit reset request';
        }
      },
      error: (error) => {
        this.isLoading = false;
        this.forgotPasswordError = error.error?.error || 'Failed to submit reset request. Please try again.';
        console.error('Forgot password error:', error);
      }
    });
  }

  closeForgotPasswordModal() {
    this.showForgotPasswordModal = false;
    this.forgotPasswordError = '';
  }

  // Open Change Password Modal
  openChangePasswordModal() {
    this.showChangePasswordModal = true;
    this.newPassword = '';
    this.confirmPassword = '';
    this.changePasswordError = '';
  }

  // Change password
  changePassword() {
    if (!this.newPassword || !this.confirmPassword) {
      this.changePasswordError = 'Please fill in all fields.';
      return;
    }
    
    if (this.newPassword !== this.confirmPassword) {
      this.changePasswordError = 'Passwords do not match!';
      return;
    }
    
    if (this.newPassword.length < 6) {
      this.changePasswordError = 'Password must be at least 6 characters long.';
      return;
    }

    this.isLoading = true;
    this.changePasswordError = '';

    this.api.changeOwnPassword(this.username,this.oldPassword, this.newPassword).subscribe({
      next: (response) => {
        this.isLoading = false;
        if (response.success) {
          alert(`✅ Password Changed Successfully!\n\nYour password has been updated. You can now use this password for future logins.`);
          this.closeChangePasswordModal();
        } else {
          this.changePasswordError = response.message || 'Failed to change password';
        }
      },
      error: (error) => {
        this.isLoading = false;
        this.changePasswordError = error.error?.error || 'Failed to change password. Please try again.';
        console.error('Change password error:', error);
      }
    });
  }

  closeChangePasswordModal() {
    this.showChangePasswordModal = false;
    this.newPassword = '';
    this.confirmPassword = '';
    this.changePasswordError = '';
  }

  // Logout
  logout() {
    this.api.logout();
    this.isLoggedIn = false;
    this.username = '';
    this.password = '';
    this.newPassword = '';
    this.confirmPassword = '';
    this.loginError = '';
  }
}