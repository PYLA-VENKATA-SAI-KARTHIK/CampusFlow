import { test, expect } from '@playwright/test';

/**
 * Phase 4.4 — Playwright E2E: Authentication Workflows
 * 
 * Verifies:
 * - Unauthenticated user redirect to /login
 * - Form validation and invalid credential rejection
 * - Successful authentication for Student, Officer, and Admin
 * - Session clearance and redirection on logout
 */

test.describe('Authentication & Session Workflows', () => {

  test('unauthenticated user is redirected to /login', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/.*\/login/);
    await expect(page.locator('text=Sign in to your account')).toBeVisible();
  });

  test('invalid login credentials displays server error', async ({ page }) => {
    // Intercept login to return 401
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid credentials' }),
      });
    });

    await page.goto('/login');
    await page.fill('input[type="email"]', 'unknown@campusflow.edu');
    await page.fill('input[type="password"]', 'WrongPassword123');
    await page.click('button:has-text("Sign in")');

    // Verify error notification or server message
    const errorAlert = page.locator('.bg-red-50');
    await expect(errorAlert).toBeVisible();
  });

  test('student login succeeds and redirects to dashboard', async ({ page }) => {
    // Mock successful student login
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token-student',
          refresh_token: 'mock-refresh-token-student',
          user: {
            id: '11111111-1111-1111-1111-111111111111',
            email: 'student1@campusflow.edu',
            full_name: 'Synthetic Student One',
            role: 'STUDENT',
            is_active: true,
            must_change_password: false,
          },
        }),
      });
    });

    // Mock student profile and drives endpoints
    await page.route('**/api/v1/students/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '22222222-2222-2222-2222-222222222222',
          user_id: '11111111-1111-1111-1111-111111111111',
          roll_number: 'SYN26CSE001',
          branch_code: 'CSE',
          batch_year: 2026,
          cgpa: 8.8,
          active_backlogs: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });

    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20, has_next: false }),
      });
    });

    await page.goto('/login');
    await page.fill('input[type="email"]', 'student1@campusflow.edu');
    await page.fill('input[type="password"]', 'TestStudent@123');
    await page.click('button:has-text("Sign in")');

    await expect(page).toHaveURL('/');
    // Check that user name with role is visible in AppLayout navbar
    await expect(page.locator('nav').getByText('Synthetic Student One (STUDENT)')).toBeVisible();
  });

  test('officer login displays placement officer navigation', async ({ page }) => {
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token-officer',
          refresh_token: 'mock-refresh-token-officer',
          user: {
            id: '33333333-3333-3333-3333-333333333333',
            email: 'officer@campusflow.edu',
            full_name: 'Placement Officer',
            role: 'OFFICER',
            is_active: true,
            must_change_password: false,
          },
        }),
      });
    });

    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20, has_next: false }),
      });
    });

    await page.goto('/login');
    await page.fill('input[type="email"]', 'officer@campusflow.edu');
    await page.fill('input[type="password"]', 'TestOfficer@123');
    await page.click('button:has-text("Sign in")');

    await expect(page).toHaveURL('/');
    await expect(page.locator('nav').getByText('Placement Officer (OFFICER)')).toBeVisible();
    await expect(page.locator('nav button:has-text("Analytics")')).toBeVisible();
  });

  test('admin login displays admin management navigation', async ({ page }) => {
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token-admin',
          refresh_token: 'mock-refresh-token-admin',
          user: {
            id: '44444444-4444-4444-4444-444444444444',
            email: 'admin@campusflow.edu',
            full_name: 'System Admin',
            role: 'ADMIN',
            is_active: true,
            must_change_password: false,
          },
        }),
      });
    });

    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20, has_next: false }),
      });
    });

    await page.goto('/login');
    await page.fill('input[type="email"]', 'admin@campusflow.edu');
    await page.fill('input[type="password"]', 'TestAdmin@123');
    await page.click('button:has-text("Sign in")');

    await expect(page).toHaveURL('/');
    await expect(page.locator('nav').getByText('System Admin (ADMIN)')).toBeVisible();
    await expect(page.locator('nav button:has-text("Users")')).toBeVisible();
    await expect(page.locator('nav button:has-text("Audit Logs")')).toBeVisible();
  });

  test('logout clears session and redirects to /login', async ({ page }) => {
    // Pre-seed authenticated state
    await page.addInitScript(() => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'dummy-token',
            refreshToken: 'dummy-refresh',
            user: {
              id: '11111111-1111-1111-1111-111111111111',
              email: 'student1@campusflow.edu',
              full_name: 'Synthetic Student One',
              role: 'STUDENT',
              is_active: true,
            },
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    });

    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20, has_next: false }),
      });
    });

    await page.route('**/api/v1/auth/logout', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Successfully logged out' }),
      });
    });

    await page.goto('/');
    await expect(page.locator('nav').getByText('Synthetic Student One (STUDENT)')).toBeVisible();

    // Click Logout button
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL(/.*\/login/);

    // Verify localStorage cleared
    const authStorage = await page.evaluate(() => window.localStorage.getItem('campusflow-auth-storage'));
    const parsed = JSON.parse(authStorage || '{}');
    expect(parsed.state?.isAuthenticated).toBe(false);
  });
});
