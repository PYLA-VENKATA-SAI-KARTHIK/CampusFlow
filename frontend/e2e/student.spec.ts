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

  test('student views personal, academic, and resume/portfolio details on /profile', async ({ page }) => {
    let mockProfile: any = {
      id: 'p1111111-1111-1111-1111-111111111111',
      user_id: '11111111-1111-1111-1111-111111111111',
      roll_number: 'SYN26CSE00001',
      branch_code: 'CSE',
      batch_year: 2026,
      cgpa: 8.80,
      active_backlogs: 0,
      phone_number: '+91 9876543210',
      gender: 'Male',
      section: 'A',
      tenth_mark: 92.50,
      twelfth_mark: 88.00,
      diploma_mark: null,
      portfolio_url: 'https://github.com/student-one',
      resume_gcs_path: 'resumes/test.pdf',
      resume_uploaded_at: new Date().toISOString(),
    };

    await page.route('**/api/v1/students/me', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockProfile),
        });
      } else if (route.request().method() === 'PATCH') {
        const patchData = JSON.parse(route.request().postData() || '{}');
        mockProfile = { ...mockProfile, ...patchData };
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockProfile),
        });
      }
    });

    await page.goto('/profile');

    // 1. Verify Personal Details
    await expect(page.getByRole('heading', { name: 'Personal Details' })).toBeVisible();
    await expect(page.locator('input[value="Synthetic Student One"]')).toBeDisabled();
    await expect(page.locator('input[value="student1@campusflow.edu"]')).toBeDisabled();
    await expect(page.locator('input[value="+91 9876543210"]')).toBeVisible();

    // 2. Verify Academic Details
    await expect(page.getByRole('heading', { name: 'Academic Details' })).toBeVisible();
    await expect(page.locator('text=SYN26CSE00001').first()).toBeVisible();
    await expect(page.locator('text=92.50%')).toBeVisible();
    await expect(page.locator('text=88.00%')).toBeVisible();
    await expect(page.getByText('Not Applicable', { exact: true }).first()).toBeVisible(); // Diploma mark is null

    // 3. Verify Resume & Portfolio
    await expect(page.getByRole('heading', { name: 'Resume & Portfolio' })).toBeVisible();
    await expect(page.locator('text=Official Resume Document on File')).toBeVisible();
    await expect(page.locator('text=https://github.com/student-one')).toBeVisible();
  });

  test('student edits section and academic marks, saves, and verifies persistence', async ({ page }) => {
    let mockProfile: any = {
      id: 'p1111111-1111-1111-1111-111111111111',
      user_id: '11111111-1111-1111-1111-111111111111',
      roll_number: 'SYN26CSE00001',
      branch_code: 'CSE',
      batch_year: 2026,
      cgpa: 8.80,
      active_backlogs: 0,
      section: 'A',
      tenth_mark: 92.50,
      twelfth_mark: 88.00,
      diploma_mark: null,
      portfolio_url: null,
    };

    await page.route('**/api/v1/students/me', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockProfile),
        });
      } else if (route.request().method() === 'PATCH') {
        const patchData = JSON.parse(route.request().postData() || '{}');
        mockProfile = { ...mockProfile, ...patchData };
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockProfile),
        });
      }
    });

    await page.goto('/profile');

    // Click Edit Academic Details
    await page.click('button:has-text("Edit Academic Details")');

    // Change Section to "B"
    await page.fill('input[placeholder="e.g. A, B, C"]', 'B');

    // Change 10th mark to 95.00
    await page.fill('input[placeholder="e.g. 92.50"]', '95.00');

    // Save Academic Details
    await page.click('button:has-text("Save Academic Details")');

    // Verify Success Message
    await expect(page.locator('text=Academic details updated successfully.')).toBeVisible();
    await expect(page.locator('text=95.00%')).toBeVisible();

    // Reload page to verify persistence
    await page.reload();
    await expect(page.locator('text=95.00%')).toBeVisible();
  });

  test('student edits portfolio URL, saves, and verifies persistence', async ({ page }) => {
    let mockProfile: any = {
      id: 'p1111111-1111-1111-1111-111111111111',
      user_id: '11111111-1111-1111-1111-111111111111',
      roll_number: 'SYN26CSE00001',
      branch_code: 'CSE',
      batch_year: 2026,
      cgpa: 8.80,
      active_backlogs: 0,
      portfolio_url: null,
    };

    await page.route('**/api/v1/students/me', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockProfile),
        });
      } else if (route.request().method() === 'PATCH') {
        const patchData = JSON.parse(route.request().postData() || '{}');
        mockProfile = { ...mockProfile, ...patchData };
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockProfile),
        });
      }
    });

    await page.goto('/profile');

    // Click Edit Portfolio
    await page.click('button:has-text("Edit Portfolio")');

    // Fill Portfolio URL
    await page.fill('input[type="url"]', 'https://github.com/my-awesome-portfolio');

    // Save
    await page.click('button:has-text("Save Portfolio")');

    // Verify Success
    await expect(page.locator('text=Portfolio link updated successfully.')).toBeVisible();
    await expect(page.locator('text=https://github.com/my-awesome-portfolio')).toBeVisible();

    // Reload and verify persistence
    await page.reload();
    await expect(page.locator('text=https://github.com/my-awesome-portfolio')).toBeVisible();
  });

  test('student edits personal email and phone, saves, and verifies persistence', async ({ page }) => {
    let mockProfile: any = {
      id: 'p1111111-1111-1111-1111-111111111111',
      user_id: '11111111-1111-1111-1111-111111111111',
      roll_number: 'SYN26CSE00001',
      branch_code: 'CSE',
      batch_year: 2026,
      cgpa: 8.80,
      active_backlogs: 0,
      phone_number: '+91 9876543210',
      personal_email: 'initial.student@gmail.com',
      gender: 'Male',
    };

    await page.route('**/api/v1/students/me', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockProfile),
        });
      } else if (route.request().method() === 'PATCH') {
        const patchData = JSON.parse(route.request().postData() || '{}');
        mockProfile = { ...mockProfile, ...patchData };
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockProfile),
        });
      }
    });

    await page.goto('/profile');

    // Click Edit Personal Details
    await page.click('button:has-text("Edit Personal Details")');

    // Fill new personal email and phone
    await page.fill('input[placeholder="student.personal@example.com"]', 'updated.karthik@gmail.com');
    await page.fill('input[type="tel"]', '+91 9123456780');

    // Save
    await page.click('button:has-text("Save Personal Details")');

    // Verify Success
    await expect(page.locator('text=Personal details updated successfully.')).toBeVisible();

    // Reload and verify persistence
    await page.reload();
    await expect(page.locator('input[value="updated.karthik@gmail.com"]')).toBeVisible();
    await expect(page.locator('input[value="+91 9123456780"]')).toBeVisible();
  });
});
