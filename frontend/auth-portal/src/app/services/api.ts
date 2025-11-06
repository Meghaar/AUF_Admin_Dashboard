import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, Subscription } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Router } from '@angular/router';

interface User {
  slno: number;
  username: string;
  is_admin: boolean;
  must_reset: boolean;
  reset_requested: boolean;
  last_login_time: string | null;
  reset_password_time: string | null;
  created_at: string;
  forgot_request_status: string;
  forgot_request_time: string | null;
  admin_note: string;
}

interface ResetRequest {
  user_id: number;
  username: string;
  requested_at: string;
  status: string;
  admin_note: string;
}

interface LoginResponse {
  access_token: string;
  message: string;
  user?: any;
}

// User-specific interfaces
interface UserLoginResponse {
  access_token: string;
  message: string;
  user?: any;
  must_reset?: boolean;
}

interface PasswordChangeResponse {
  message: string;
  success: boolean;
}

interface ForgotPasswordResponse {
  message: string;
  success: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:5000/api'; 
  private tokenKey = 'admin_token';
  private currentUserSubject = new BehaviorSubject<any>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor(private http: HttpClient, private router: Router) {
    const token = this.getToken();
    if (token) {
      // Token exists, user was previously logged in
    }
  }

  // Get authorization headers with JWT token
  private getHeaders(): HttpHeaders {
    const token = this.getToken();
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    });
  }

  // Token management
  private getToken(): string | null {
    return sessionStorage.getItem(this.tokenKey);
  }

  private setToken(token: string): void {
    sessionStorage.setItem(this.tokenKey, token);
  }

  private removeToken(): void {
    sessionStorage.removeItem(this.tokenKey);
  }

  // Check if user is logged in
  isLoggedIn(): boolean {
    return !!this.getToken();
  }

  // ===== EXISTING ADMIN API CALLS (unchanged) =====
  
  // Admin Login
  login(username: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.baseUrl}/login`, {
      username: username,
      is_admin: true,
      password: password
    }).pipe(
      tap(response => {
        if (response.access_token) {
          this.setToken(response.access_token);
          this.currentUserSubject.next({ username });
        }
      })
    );
  }

  // Logout
  logout(): void {
    this.removeToken();
    this.currentUserSubject.next(null);
    console.log('Token removed, user logged out');
  }

  // Update Admin Credentials
  updateAdminCredentials(currentPassword: string, newUsername?: string, newPassword?: string): Observable<any> {
    const body: any = {
      current_password: currentPassword
    };
    
    if (newUsername) {
      body.new_username = newUsername;
    }
    
    if (newPassword) {
      body.new_password = newPassword;
    }

    return this.http.put(`${this.baseUrl}/admin/change_credentials`, body, { 
      headers: this.getHeaders() 
    });
  }

  // Create new user (admin only)
  createUser(username: string, password: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/admin/create_user`, {
      username: username,
      password: password
    }, { 
      headers: this.getHeaders() 
    });
  }

  // Get all users (admin only)
  getAllUsers(): Observable<{ users: User[] }> {
    return this.http.get<{ users: User[] }>(`${this.baseUrl}/users`, {
      headers: this.getHeaders()
    });
  }

  // Get password reset requests (admin only)
  getResetRequests(): Observable<{ requests: ResetRequest[] }> {
    return this.http.get<{ requests: ResetRequest[] }>(`${this.baseUrl}/admin/forgot_requests`, {
      headers: this.getHeaders()
    });
  }

  // Reset user password (admin only)
  resetUserPassword(userId: number, newPassword: string, adminNote?: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/admin/reset_user_password`, {
      user_id: userId,
      new_password: newPassword,
      admin_note: adminNote || ''
    }, { 
      headers: this.getHeaders() 
    });
  }

  // ===== NEW USER API CALLS (Backend Integration Only) =====

  // User Login (Flask endpoint)
  userLogin(username: string, password: string): Observable<UserLoginResponse> {
    return this.http.post<UserLoginResponse>(`${this.baseUrl}/login`, {
      username: username,
      password: password
    }).pipe(
      tap(response => {
        if (response.access_token) {
          this.setToken(response.access_token);
          this.currentUserSubject.next({ username, isUser: true });
          console.log('User logged in, token stored');
        }
      })
    );
  }

  // Change own password (Flask endpoint) - WITH AUTHORIZATION HEADER
  changeOwnPassword(username: string, oldPassword: string, newPassword: string): Observable<ForgotPasswordResponse> {
    return this.http.put<PasswordChangeResponse>(
      `${this.baseUrl}/change_password`, 
      {
        username,
        old_password: oldPassword,
        new_password: newPassword
      },
      { 
        headers: this.getHeaders()  // Added authorization header
      }
    )
  }

  // Forgot password request (Flask endpoint)
  requestPasswordReset(username: string): Observable<ForgotPasswordResponse> {
    return this.http.post<ForgotPasswordResponse>(`${this.baseUrl}/forgot_request`, {
      username: username,
    });
  }

  // Get user profile/info
  getUserProfile(): Observable<any> {
    return this.http.get(`${this.baseUrl}/user/profile`, {
      headers: this.getHeaders()
    });
  }

  // Validate user token/session
  validateUserSession(): Observable<any> {
    return this.http.get(`${this.baseUrl}/user/validate`, {
      headers: this.getHeaders()
    });
  }
}