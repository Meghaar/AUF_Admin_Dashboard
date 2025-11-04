import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-landing-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './landing-page.html',
  styleUrls: ['./landing-page.css']
})
export class LandingPageComponent {
  constructor(private router: Router) {}

  navigateTo(role: string) {
    if (role === 'admin') this.router.navigate(['/admin']);
    else if (role === 'user') this.router.navigate(['/user']);
  }
}
