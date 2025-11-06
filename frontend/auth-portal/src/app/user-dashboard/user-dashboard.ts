import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../services/api';
import { Router } from '@angular/router'; 

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

  // Property to track if password change is mandatory
  isMandatoryPasswordChange = false;

   constructor(private api: ApiService, private router: Router) {} // Inject Router

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
          
          // Check if this is first login after admin reset
          if (response.must_reset) {
            console.log('Must reset password:', response.must_reset);
            // Navigate to change password modal directly with mandatory flag
            this.isMandatoryPasswordChange = true;
            this.openChangePasswordModal();
          } else {
            this.isMandatoryPasswordChange = false;
          }
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

  // Open Change Password Modal
  openChangePasswordModal() {
    this.showChangePasswordModal = true;
    this.newPassword = '';
    this.confirmPassword = '';
    this.changePasswordError = '';
    
    // Pre-fill old password with current password for mandatory reset
    if (this.isMandatoryPasswordChange) {
      this.oldPassword = this.password; // Use the password they just logged in with
    } else {
      this.oldPassword = '';
    }
  }
changePassword() {
  if (!this.oldPassword || !this.newPassword || !this.confirmPassword) {
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

  // Don't allow same password
  if (this.oldPassword === this.newPassword) {
    this.changePasswordError = 'New password must be different from old password.';
    return;
  }

  this.isLoading = true;
  this.changePasswordError = '';

  this.api.changeOwnPassword(this.username, this.oldPassword, this.newPassword).subscribe(
    {
    next: (response) => {
      this.isLoading = false;
      if (response.success) {
        // For mandatory password change, just navigate to root
        if (this.isMandatoryPasswordChange) {
          this.isMandatoryPasswordChange = false;
          this.showChangePasswordModal = false;
          // Simply navigate to root path - no logout, no alerts
          this.router.navigate(['/']);
        } else {
          // For voluntary changes, just close the modal
          alert('✅ Password Changed Successfully!');
          this.closeChangePasswordModal();
        }
      } else {
        this.changePasswordError = response.message || 'Failed to change password';
      }
    },
    error: (error) => {
      this.isLoading = false;
      this.changePasswordError = error.error?.error || 'Failed to change password. Please try again.';
      console.error('Change password error:', error);
    }
  }
)
}

  // Modified closeChangePasswordModal to prevent closing during mandatory reset
  closeChangePasswordModal() {
    if (this.isMandatoryPasswordChange) {
      // Don't allow closing if password change is mandatory
      this.changePasswordError = 'You must change your password before proceeding.';
      return;
    }
    
    this.showChangePasswordModal = false;
    this.newPassword = '';
    this.confirmPassword = '';
    this.oldPassword = '';
    this.changePasswordError = '';
  }

  // Helper method to perform logout and reset state
  performLogout() {
    // Call API logout to clear token
    this.api.logout();
    
    // Close all modals first
    this.showChangePasswordModal = false;
    this.showForgotPasswordModal = false;
    
    // Reset all component state
    this.isLoggedIn = false; // This will trigger the login screen to show
    this.username = '';
    this.password = '';
    this.newPassword = '';
    this.confirmPassword = '';
    this.oldPassword = '';
    this.loginError = '';
    this.isMandatoryPasswordChange = false;
    this.changePasswordError = '';
    this.forgotPasswordError = '';
    
    console.log('User logged out successfully - returning to login screen');
  }

  // Modified logout to handle mandatory password change
  logout() {
    if (this.isMandatoryPasswordChange) {
      // Don't allow logout during mandatory password change
      this.changePasswordError = 'You must change your password before logging out.';
      return;
    }
    
    this.performLogout();
  }

  // Open Forgot Password Modal
  openForgotPasswordModal() {
    if (this.isMandatoryPasswordChange) {
      this.changePasswordError = 'You must change your password first.';
      return;
    }
    this.showForgotPasswordModal = true;
    this.forgotPasswordUsername = '';
    this.forgotPasswordEmail = '';
    this.forgotPasswordError = '';
  }

  // Submit forgot password request
  submitForgotPassword() {
    if (!this.forgotPasswordUsername) {
      this.forgotPasswordError = 'Please enter Username';
      return;
    }

    this.isLoading = true;
    this.forgotPasswordError = '';

    this.api.requestPasswordReset(this.forgotPasswordUsername).subscribe({
      next: (response) => {
        this.isLoading = false;
        if (response.success) {
          alert(`✅ Password Reset Request Submitted!\n\nYour request has been sent to the admin.\nUsername: ${this.forgotPasswordUsername}\n`);
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
}