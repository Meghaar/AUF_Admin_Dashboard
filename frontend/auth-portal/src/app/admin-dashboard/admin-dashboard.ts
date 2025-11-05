import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../services/api';
 
interface User {
  slno: number;
  username: string;
  is_admin: boolean;
  must_reset: boolean;
  reset_requested: boolean;
  last_login_time: string;
  reset_password_time: string;
  created_at: string;
  forgot_request_status: string;
  forgot_request_time: string;
  admin_note: string;
}
 
interface ResetRequest {
  user_id: number;
  username: string;
  requested_at: string;
  status: string;
  admin_note: string;
}
 
@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-dashboard.html',
  styleUrls: ['./admin-dashboard.css']
})
export class AdminDashboardComponent implements OnInit {
  isLoggedIn = false;
  username = '';
  password = '';
  isLoading = false;
  // Modal states
  showUpdateCredentialsModal = false;
  showCreateUserModal = false;
  showUsersListModal = false;
  showResetPasswordModal = false;
  // Update credentials form
  currentPassword = '';
  newAdminUsername = '';
  newAdminPassword = '';
  confirmAdminPassword = '';
  // Create user form
  newUsername = '';
  newPassword = '';
  // Data from API
  users: User[] = [];
  resetRequests: ResetRequest[] = [];
  currentAdminUsername = '';
  selectedResetRequest: ResetRequest | null = null;
  newResetPassword = '';
 
  constructor(private api: ApiService) {}
 
  ngOnInit() {
    // Check if already logged in
    if (this.api.isLoggedIn()) {
      this.isLoggedIn = true;
      this.loadData();
    }
  }
 
  loadData() {
    this.loadUsers();
    this.loadResetRequests();
  }
 
loadUsers() {
  this.api.getAllUsers().subscribe({
    next: (response) => {
      this.users = response.users as any; // Quick fix
      // Or more specifically:
      // this.users = response.users as User[];
      
      // Find admin username
      const admin = this.users.find(u => u.is_admin);
      if (admin) {
        this.currentAdminUsername = admin.username;
      }
    },
    error: (error) => {
      console.error('Error loading users:', error);
      if (error.status === 401) {
        alert('Session expired. Please login again.');
        this.logout();
      }
    }
  });
}
 
  loadResetRequests() {
    this.api.getResetRequests().subscribe({
      next: (response) => {
        this.resetRequests = response.requests;
      },
      error: (error) => {
        console.error('Error loading reset requests:', error);
      }
    });
  }
 
  // Login with credentials
  login() {
    if (!this.username || !this.password) {
      alert('Please enter username and password');
      return;
    }
 
    this.isLoading = true;
    this.api.login(this.username, this.password).subscribe({
      next: (response) => {
        console.log(response)
        localStorage.setItem('admin_token',response.access_token)
        this.isLoggedIn = true;
        this.currentAdminUsername = this.username;
        this.loadData();
        alert('Admin login successful!');
        this.isLoading = false;
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Login error:', error);
        if (error.error?.error) {
          alert(error.error.error);
        } else {
          alert('Invalid admin credentials!');
        }
      }
    });
  }
 
  // Open Update Credentials Modal
  openUpdateCredentialsModal() {
    this.showUpdateCredentialsModal = true;
    this.currentPassword = '';
    this.newAdminUsername = '';
    this.newAdminPassword = '';
    this.confirmAdminPassword = '';
  }
 
  // Update Admin Credentials
  updateAdminCredentials() {
    if (!this.currentPassword) {
      alert('Please enter your current password.');
      return;
    }
 
    if (!this.newAdminUsername && !this.newAdminPassword) {
      alert('Please enter at least new username or new password.');
      return;
    }
    if (this.newAdminPassword && this.newAdminPassword !== this.confirmAdminPassword) {
      alert('New passwords do not match!');
      return;
    }
 
    this.isLoading = true;
    this.api.updateAdminCredentials(
      this.currentPassword,
      this.newAdminUsername || undefined,
      this.newAdminPassword || undefined
    ).subscribe({
      next: (response) => {
        this.isLoading = false;
        const updatedUsername = this.newAdminUsername || this.currentAdminUsername;
        alert(`✅ Admin credentials updated successfully!
 
${this.newAdminUsername ? `New Username: ${this.newAdminUsername}` : ''}
${this.newAdminPassword ? `New Password: ${this.newAdminPassword}` : ''}
 
Please use these credentials for your next login.`);
        this.currentAdminUsername = updatedUsername;
        this.closeUpdateCredentialsModal();
        this.loadData();
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Update credentials error:', error);
        if (error.error?.error) {
          alert('Error: ' + error.error.error);
        } else {
          alert('Failed to update credentials. Please try again.');
        }
      }
    });
  }
 
  closeUpdateCredentialsModal() {
    this.showUpdateCredentialsModal = false;
  }
 
  // Open Create User Modal
  openCreateUserModal() {
    this.showCreateUserModal = true;
    this.newUsername = '';
    this.newPassword = '';
  }
 
  // Create new user
  createUser() {
    if (!this.newUsername || !this.newPassword) {
      alert('Please fill in all fields.');
      return;
    }
 
    this.isLoading = true;
    this.api.createUser(this.newUsername, this.newPassword).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.loadData(); // Refresh users list
        alert(`✅ User Created Successfully!
Username: ${this.newUsername}
Password: ${this.newPassword}
 
✓ User has been added to the system
✓ User can now login immediately with these credentials
✓ Please share these credentials with the user securely`);
        this.closeCreateUserModal();
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Create user error:', error);
        if (error.error?.error) {
          alert('Error: ' + error.error.error);
        } else {
          alert('Failed to create user. Please try again.');
        }
      }
    });
  }
 
  closeCreateUserModal() {
    this.showCreateUserModal = false;
    this.newUsername = '';
    this.newPassword = '';
  }
 
  // Open Users List Modal
  openUsersListModal() {
    this.loadUsers(); // Refresh data
    this.showUsersListModal = true;
  }
 
  closeUsersListModal() {
    this.showUsersListModal = false;
  }
 
  // Get total user count
  getTotalUsers(): number {
    return this.users.length;
  }
 
  // Open Reset Password Modal
  openResetPasswordModal() {
    this.loadResetRequests(); // Refresh reset requests
    this.showResetPasswordModal = true;
    this.selectedResetRequest = null;
    this.newResetPassword = '';
  }
 
  // Select user for password reset
  selectUserForReset(request: ResetRequest) {
    this.selectedResetRequest = request;
    this.newResetPassword = '';
  }
 
  // Reset user password
  resetUserPassword() {
    if (!this.selectedResetRequest || !this.newResetPassword) {
      alert('Please select a user and enter a new password.');
      return;
    }
 
    this.isLoading = true;
    this.api.resetUserPassword(
      this.selectedResetRequest.user_id,
      this.newResetPassword,
      `Password reset by admin on ${new Date().toLocaleString()}`
    ).subscribe({
      next: (response) => {
        this.isLoading = false;
        this.loadData(); // Refresh data
        alert(`✅ Password Reset Successfully!
 
Username: ${this.selectedResetRequest!.username}
New Password: ${this.newResetPassword}
 
The user can now login with these new credentials.
Please send these credentials to the user.`);
        this.selectedResetRequest = null;
        this.newResetPassword = '';
        this.loadResetRequests(); // Refresh to remove resolved request
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Reset password error:', error);
        if (error.error?.error) {
          alert('Error: ' + error.error.error);
        } else {
          alert('Failed to reset password. Please try again.');
        }
      }
    });
  }
 
  closeResetPasswordModal() {
    this.showResetPasswordModal = false;
    this.selectedResetRequest = null;
    this.newResetPassword = '';
  }
 
  // Logout
  logout() {
    this.api.logout();
    this.isLoggedIn = false;
    this.username = '';
    this.password = '';
    this.users = [];
    this.resetRequests = [];
    this.currentAdminUsername = '';
  }
 
  // Format date helper
  formatDate(dateString: string): string {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  }
 
  // Get user type label
  getUserTypeLabel(user: User): string {
    return user.is_admin ? '👑 Admin' : '👤 User';
  }
}