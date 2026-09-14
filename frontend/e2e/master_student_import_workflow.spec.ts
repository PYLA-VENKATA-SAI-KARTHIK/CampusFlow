import { test, expect } from '@playwright/test';

test.describe('Master Student List & Import Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock student listing endpoint
    await page.route('**/api/v1/officers/students*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: '11111111-1111-1111-1111-111111111111',
              user_id: '22222222-2222-2222-2222-222222222222',
              roll_number: '99230041249',
              branch_code: 'CSE',
              batch_year: 2026,
              cgpa: 8.95,
              active_backlogs: 0,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              user: {
                id: '22222222-2222-2222-2222-222222222222',
                email: '99230041249@klu.ac.in',
                full_name: 'Synthetic Student One',
                role: 'STUDENT',
                is_active: true,
              },
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
          has_next: false,
        }),
      });
    });
  });

  test('Officer views Master Student List, sees table, and interacts with Import Modal', async ({ page }) => {
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

    await page.goto('/students/master');
    await expect(page.locator('h1')).toHaveText(/Master Student List/i);

    // Verify Metric Card & Table content
    await expect(page.locator('[data-testid="metric-total-students"]')).toHaveText('1');
    await expect(page.getByRole('cell', { name: '99230041249', exact: true })).toBeVisible();
    await expect(page.locator('text=Synthetic Student One')).toBeVisible();
    await expect(page.locator('text=99230041249@klu.ac.in')).toBeVisible();

    // Verify Search Input & Import Button
    await expect(page.locator('[data-testid="input-search-student"]')).toBeVisible();
    await expect(page.locator('[data-testid="btn-import-excel"]')).toBeVisible();

    // Open Import Modal
    await page.click('[data-testid="btn-import-excel"]');
    await expect(page.locator('h3')).toHaveText(/Import Master Student List/i);
    await expect(page.locator('[data-testid="file-upload-input"]')).toBeAttached();

    // Close Modal
    await page.click('button:has-text("Cancel")');
    await expect(page.locator('h3:has-text("Import Master Student List")')).not.toBeVisible();
  });

  test('Student is redirected when attempting to access Master Student List (RBAC)', async ({ page }) => {
    // Seed student state
    await page.addInitScript(() => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-jwt-token-student',
            refreshToken: 'mock-refresh-token-student',
            user: {
              id: '44444444-4444-4444-4444-444444444444',
              email: 'student@campusflow.edu',
              full_name: 'Student User',
              role: 'STUDENT',
              is_active: true,
            },
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    });

    await page.goto('/students/master');
    await expect(page).toHaveURL(/\/unauthorized/);
  });
});
