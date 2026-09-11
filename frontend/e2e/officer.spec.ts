import { test, expect } from '@playwright/test';

/**
 * Phase 4.4 — Playwright E2E: Officer Workflows
 * 
 * Verifies:
 * - Placement Officer dashboard and Tool panel display
 * - Manual broadcast trigger and modal interaction
 * - Analytics Dashboard navigation and platform metrics display
 */

test.describe('Officer Workflows', () => {

  test.beforeEach(async ({ page }) => {
    // Seed authenticated officer state in localStorage
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
  });

  test('officer views dashboard with Placement Officer Tool', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=Placement Officer Tool')).toBeVisible();
    await expect(page.locator('text=Drive Manual Broadcast Management')).toBeVisible();
  });

  test('officer opens manual broadcast modal', async ({ page }) => {
    await page.goto('/');
    await page.fill('#drive-id-input', '12345678-1234-1234-1234-1234567890ab');
    await page.click('button:has-text("Compose Broadcast")');

    // Verify modal is displayed
    await expect(page.locator('text=Manual Notification Broadcast')).toBeVisible();
    await expect(page.locator('text=Broadcast Title')).toBeVisible();
    await expect(page.locator('text=Target Audience')).toBeVisible();
  });

  test('officer navigates to analytics dashboard and views metrics', async ({ page }) => {
    await page.route('**/api/v1/analytics/overview', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          drives_summary: {
            total_drives: 12,
            active_drives: 5,
            completed_drives: 7,
          },
          placement_metrics: {
            overall_placement_percentage: 69.1,
            total_placed_students: 145,
            total_active_students: 210,
            total_applications_submitted: 420,
          },
          branch_placement_stats: [
            {
              branch_code: 'CSE',
              branch_name: 'Computer Science and Engineering',
              total_students: 100,
              placed_students: 85,
              placement_percentage: 85.0,
            },
          ],
          recent_drives_activity: [],
        }),
      });
    });

    await page.goto('/analytics');
    await expect(page.locator('text=Institutional Placement Analytics')).toBeVisible();
    await expect(page.locator('text=Placed Students')).toBeVisible();
    await expect(page.getByText('145', { exact: true }).first()).toBeVisible();
    await expect(page.locator('text=Total Drives')).toBeVisible();
    await expect(page.getByText('12', { exact: true }).first()).toBeVisible();
  });
});
