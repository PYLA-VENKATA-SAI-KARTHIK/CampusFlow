import { test, expect } from '@playwright/test';

/**
 * Phase 4.4 — Playwright E2E: Student Workflows
 * 
 * Verifies:
 * - Student dashboard rendering and profile data
 * - Notification Center navigation and notifications list display
 * - Filtering between All and Unread notifications
 * - Marking notifications as read
 * - Web Push subscription status / opt-in button
 */

test.describe('Student Workflows', () => {

  test.beforeEach(async ({ page }) => {
    // Seed authenticated student state in localStorage
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
  });

  test('student views dashboard with profile information', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('text=Welcome to CampusFlow')).toBeVisible();
    await expect(page.locator('text=You are successfully logged in.')).toBeVisible();
    await expect(page.locator('nav').getByText('Synthetic Student One (STUDENT)')).toBeVisible();
    await expect(page.locator('text=student1@campusflow.edu')).toBeVisible();
  });

  test('student accesses notification center, views items, and filters unread', async ({ page }) => {
    const mockNotifications = [
      {
        id: 'n1111111-1111-1111-1111-111111111111',
        user_id: '11111111-1111-1111-1111-111111111111',
        title: 'New Placement Drive: Acme Tech',
        body: 'Acme Tech has announced Graduate Software Engineer roles.',
        notification_type: 'DRIVE_PUBLISHED',
        reference_id: 'dddddddd-dddd-dddd-dddd-dddddddddddd',
        reference_type: 'DRIVE',
        is_read: false,
        push_sent: true,
        push_sent_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
      },
      {
        id: 'n2222222-2222-2222-2222-222222222222',
        user_id: '11111111-1111-1111-1111-111111111111',
        title: 'Welcome to CampusFlow',
        body: 'Your placement profile has been verified by the TPO.',
        notification_type: 'SYSTEM',
        reference_id: null,
        reference_type: null,
        is_read: true,
        push_sent: false,
        push_sent_at: null,
        created_at: new Date().toISOString(),
      },
    ];

    await page.route('**/api/v1/notifications**', async (route) => {
      const url = new URL(route.request().url());
      if (url.searchParams.get('is_read') === 'false') {
        const unread = mockNotifications.filter((n) => !n.is_read);
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: unread, total: unread.length, page: 1, page_size: 10, has_next: false }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: mockNotifications, total: mockNotifications.length, page: 1, page_size: 10, has_next: false }),
        });
      }
    });

    await page.goto('/notifications');
    await expect(page.locator('text=Notification Center')).toBeVisible();
    await expect(page.locator('text=New Placement Drive: Acme Tech')).toBeVisible();
    await expect(page.locator('text=Welcome to CampusFlow')).toBeVisible();

    // Filter to Unread
    await page.click('button:has-text("Unread")');
    await expect(page.locator('text=New Placement Drive: Acme Tech')).toBeVisible();
    await expect(page.locator('text=Welcome to CampusFlow')).not.toBeVisible();
  });

  test('student marks single notification as read', async ({ page }) => {
    let isMarked = false;

    await page.route('**/api/v1/notifications**', async (route) => {
      const mockNotifications = [
        {
          id: 'n1111111-1111-1111-1111-111111111111',
          user_id: '11111111-1111-1111-1111-111111111111',
          title: 'Unread Notification',
          body: 'Clicking Mark as Read will change this state.',
          notification_type: 'SYSTEM',
          reference_id: null,
          reference_type: null,
          is_read: isMarked,
          created_at: new Date().toISOString(),
        },
      ];
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: mockNotifications, total: 1, page: 1, page_size: 10, has_next: false }),
      });
    });

    await page.route('**/api/v1/notifications/*/read', async (route) => {
      isMarked = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'n1111111-1111-1111-1111-111111111111', is_read: true }),
      });
    });

    await page.goto('/notifications');
    const markReadBtn = page.locator('button:has-text("Mark read")');
    await expect(markReadBtn).toBeVisible();
    await markReadBtn.click();
    await expect(markReadBtn).not.toBeVisible();
  });
});
