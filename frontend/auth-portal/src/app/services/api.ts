import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private users: { username: string; password: string }[] = [
    { username: 'user1', password: 'user123' },
  ];
  private resetRequests: string[] = [];

  addUser(username: string, password: string) {
    this.users.push({ username, password });
  }

  validateUser(username: string, password: string) {
    return this.users.some(u => u.username === username && u.password === password);
  }

  requestPasswordReset(username: string) {
    if (!this.resetRequests.includes(username)) {
      this.resetRequests.push(username);
    }
  }

  getResetRequests() {
    return this.resetRequests;
  }

  updateUserPassword(username: string, newPass: string) {
    const user = this.users.find(u => u.username === username);
    if (user) user.password = newPass;
    this.resetRequests = this.resetRequests.filter(u => u !== username);
  }

  updateUser(oldName: string, newName: string, newPass: string) {
    const user = this.users.find(u => u.username === oldName);
    if (user) {
      user.username = newName;
      user.password = newPass;
    }
  }
}
