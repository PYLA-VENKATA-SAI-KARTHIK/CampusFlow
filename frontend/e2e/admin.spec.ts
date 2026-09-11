import { test, expect } from '@playwright/test';

/**
 * Phase 4.4 — Playwright E2E: Admin Workflows
 * 
 * Verifies:
 * - Admin users listing page (/admin/users)
 * - Create User modal interaction
 * - Bulk Import modal interaction
 * - Audit Logs page (/admin/audit-logs)
 */

test.describe('Admin Workflows', () => {

  test.beforeEach(async ({ page }) => {
    // Seed authenticated admin state in localStorage
    await page.addInitScript(() => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-jwt-token-admin',
            refreshToken: 'mock-refresh-token-admin',
            user: {
              id: '44444444-4444-4444-4444-444444444444',
              email: 'admin@campusflow.edu',
              full_name: 'System Admin',
              role: 'ADMIN',
              is_active: true,
            },
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    });
  });

  test('admin views users list table and action buttons', async ({ page }) => {
    await page.route('**/api/v1/admin/users**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: '44444444-4444-4444-4444-444444444444',
              email: 'admin@campusflow.edu',
              full_name: 'System Admin',
              role: 'ADMIN',
              is_active: true,
              must_change_password: false,
              created_at: new Date().toISOString(),
            },
            {
              id: '33333333-3333-3333-3333-333333333333',
              email: 'officer@campusflow.edu',
              full_name: 'Placement Officer',
              role: 'OFFICER',
              is_active: true,
              must_change_password: false,
              created_at: new Date().toISOString(),
            },
          ],
          total: 2,
          page: 1,
          page_size: 15,
          has_next: false,
        }),
      });
    });

    await page.goto('/admin/users');
    await expect(page.locator('text=User Management')).toBeVisible();
    await expect(page.locator('text=admin@campusflow.edu')).toBeVisible();
    await expect(page.locator('text=officer@campusflow.edu')).toBeVisible();

    // Verify Create Staff User and Bulk Import buttons exist
    await expect(page.locator('button:has-text("Add Staff User")')).toBeVisible();
    await expect(page.locator('button:has-text("Bulk Import Students")')).toBeVisible();
  });

  test('admin opens create user modal and bulk import modal', async ({ page }) => {
    await page.route('**/api/v1/admin/users**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 15, has_next: false }),
      });
    });

    await page.goto('/admin/users');

    // Click Add Staff User
    await page.click('button:has-text("Add Staff User")');
    await expect(page.locator('text=Create Staff Account')).toBeVisible();
    // Close modal by clicking close icon or clicking outside
    await page.locator('button:has-text("Cancel")').first().click();

    // Click Bulk Import Students
    await page.click('button:has-text("Bulk Import Students")');
    await expect(page.locator('text=Bulk Student Import')).toBeVisible();
    await expect(page.locator('text=Required CSV Columns:')).toBeVisible();
  });

  test('admin views audit logs page with filter controls', async ({ page }) => {
    await page.route('**/api/v1/admin/audit-logs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'aaaa1111-aaaa-1111-aaaa-111111111111',
              performed_by_user_id: '44444444-4444-4444-4444-444444444444',
              actor_email: 'admin@campusflow.edu',
              actor_name: 'System Admin',
              action: 'USER_CREATED',
              entity_type: 'USER',
              entity_id: '33333333-3333-3333-3333-333333333333',
              ip_address: '127.0.0.1',
              created_at: new Date().toISOString(),
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
          has_next: false,
        }),
      });
    });

    await page.goto('/admin/audit-logs');
    await expect(page.locator('text=System Audit Logs')).toBeVisible();
    await expect(page.locator('text=USER_CREATED')).toBeVisible();
    await expect(page.locator('text=127.0.0.1')).toBeVisible();
  });
});
