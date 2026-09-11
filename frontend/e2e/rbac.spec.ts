import { test, expect } from '@playwright/test';

/**
 * Phase 4.4 — Playwright E2E: Client-side RBAC Guard Verification
 * 
 * Verifies that role-protected client routes block unauthorized roles:
 * - STUDENT attempting direct navigation to /admin/users -> /unauthorized
 * - STUDENT attempting direct navigation to /admin/audit-logs -> /unauthorized
 * - STUDENT attempting direct navigation to /analytics -> /unauthorized
 * - OFFICER attempting direct navigation to /admin/users -> /unauthorized
 * - OFFICER attempting direct navigation to /admin/audit-logs -> /unauthorized
 */

test.describe('Client-Side RBAC & Route Protection', () => {

  test('student is blocked from admin routes and redirected to /unauthorized', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-jwt-token-student',
            refreshToken: 'mock-refresh-token-student',
            user: {
              id: '11111111-1111-1111-1111-111111111111',
              email: 'student1@campusflow.edu',
              full_name: 'Student Candidate',
              role: 'STUDENT',
              is_active: true,
            },
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    });

    await page.goto('/admin/users');
    await expect(page).toHaveURL(/.*\/unauthorized/);
    await expect(page.locator('text=Access Denied')).toBeVisible();

    await page.goto('/admin/audit-logs');
    await expect(page).toHaveURL(/.*\/unauthorized/);
    await expect(page.locator('text=Access Denied')).toBeVisible();

    await page.goto('/analytics');
    await expect(page).toHaveURL(/.*\/unauthorized/);
    await expect(page.locator('text=Access Denied')).toBeVisible();
  });

  test('officer is blocked from admin routes and redirected to /unauthorized', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-jwt-token-officer',
            refreshToken: 'mock-refresh-token-officer',
            user: {
              id: '33333333-3333-3333-3333-333333333333',
              email: 'officer@campusflow.edu',
              full_name: 'Placement Officer',
              role: 'OFFICER',
              is_active: true,
            },
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    });

    await page.goto('/admin/users');
    await expect(page).toHaveURL(/.*\/unauthorized/);
    await expect(page.locator('text=Access Denied')).toBeVisible();

    await page.goto('/admin/audit-logs');
    await expect(page).toHaveURL(/.*\/unauthorized/);
    await expect(page.locator('text=Access Denied')).toBeVisible();
  });

  test('unauthenticated user is redirected to /login when attempting to access /admin/users', async ({ page }) => {
    await page.goto('/admin/users');
    await expect(page).toHaveURL(/.*\/login/);
  });
});
