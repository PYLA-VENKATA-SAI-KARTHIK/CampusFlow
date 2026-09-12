import { test, expect } from '@playwright/test';

test.describe('CampusFlow SaaS Workspace Redesign Verification', () => {

  test('1. Student Workspace: Sidebar, Navigation, and Dedicated Pages', async ({ page }) => {
    // Seed authenticated student state
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

    // Mock student profile, drives, and applications
    await page.route('**/api/v1/students/me', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: '22222222-2222-2222-2222-222222222222',
            user_id: '11111111-1111-1111-1111-111111111111',
            roll_number: 'SYN26CSE001',
            branch_code: 'CSE',
            batch_year: 2026,
            cgpa: 8.85,
            active_backlogs: 0,
            phone: '+91 9876543210',
            gender: 'Male',
            resume_gcs_path: 'resumes/11111111/resume.pdf',
            resume_uploaded_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'd1111111-1111-1111-1111-111111111111',
              company_name: 'Acme Technologies',
              role_title: 'Software Engineer',
              package_details: { ctc_lpa: 14.5 },
              location: 'Bangalore, India',
              registration_end: new Date(Date.now() + 86400000 * 3).toISOString(),
              status: 'REGISTRATION_OPEN',
              eligibility_criteria: { min_cgpa: 7.5, eligible_branches: ['CSE', 'ECE'], max_backlogs: 0 },
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
          has_next: false,
        }),
      });
    });

    await page.route('**/api/v1/students/me/applications**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'a1111111-1111-1111-1111-111111111111',
              drive_id: 'd1111111-1111-1111-1111-111111111111',
              company_name: 'Acme Technologies',
              role_title: 'Software Engineer',
              status: 'SHORTLISTED',
              current_stage_name: 'Online Assessment',
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

    // 1. Dashboard Command Center
    await page.goto('/');
    await expect(page.locator('text=Welcome back, Synthetic Student One')).toBeVisible();
    await expect(page.locator('text=Stay on top of your placement opportunities.')).toBeVisible();
    await expect(page.locator('text=Eligible Drives')).toBeVisible();
    await expect(page.locator('text=Upcoming Deadlines')).toBeVisible();
    await expect(page.locator('text=Acme Technologies').first()).toBeVisible();

    // 2. Sidebar Navigation to Placement Drives
    await page.click('nav button:has-text("Placement Drives")');
    await page.waitForURL('**/drives');
    await expect(page.getByRole('heading', { name: 'Placement Drives' })).toBeVisible();
    await expect(page.locator('text=Acme Technologies').first()).toBeVisible();
    await expect(page.locator('text=₹14.5 LPA')).toBeVisible();

    // 3. Sidebar Navigation to My Applications
    await page.click('nav button:has-text("My Applications")');
    await page.waitForURL('**/applications');
    await expect(page.getByRole('heading', { name: 'My Applications' })).toBeVisible();
    await expect(page.locator('text=Recruitment Stage Progression')).toBeVisible();
    await expect(page.locator('text=Online Assessment').first()).toBeVisible();

    // 4. Sidebar Navigation to My Profile & Academic Read-Only Verification
    await page.click('nav button:has-text("My Profile")');
    await page.waitForURL('**/profile');
    await expect(page.getByRole('heading', { name: 'My Profile & Career Credentials' })).toBeVisible();
    await expect(page.locator('text=Read-Only • Verified by TPO')).toBeVisible();
    await expect(page.locator('text=SYN26CSE001').first()).toBeVisible();
    await expect(page.locator('text=8.85').first()).toBeVisible();

    // 5. Sidebar Navigation to My Resume
    await page.click('nav button:has-text("My Resume")');
    await page.waitForURL('**/resume');
    await expect(page.locator('text=Resume & Portfolio').first()).toBeVisible();
    await expect(page.locator('text=Official Resume Document on File')).toBeVisible();

    // 6. Sidebar Navigation to Settings
    await page.click('nav button:has-text("Settings")');
    await page.waitForURL('**/settings');
    await expect(page.getByRole('heading', { name: 'Account & Workspace Settings' })).toBeVisible();
    await expect(page.locator('text=RS256 Asymmetric JWT with JWKS')).toBeVisible();

    // 7. Sidebar Collapse/Expand Toggle
    await page.click('button[title="Collapse sidebar"]');
    // Verify collapsed state
    await expect(page.locator('button[title="Expand sidebar"]')).toBeVisible();
    await page.click('button[title="Expand sidebar"]');
    await expect(page.locator('button[title="Collapse sidebar"]')).toBeVisible();
  });

  test('2. Officer Workspace: Management Navigation and Placement Officer Tool', async ({ page }) => {
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

    await page.goto('/');
    await expect(page.locator('text=Placement Officer Tool')).toBeVisible();
    await expect(page.locator('text=Drive Manual Broadcast Management')).toBeVisible();
    await expect(page.locator('#drive-id-input')).toBeVisible();

    // Verify Officer sidebar
    await expect(page.locator('nav button:has-text("Analytics")')).toBeVisible();
    await expect(page.locator('nav button:has-text("Placement Drives")')).toBeVisible();
  });

  test('3. Admin Workspace: Administration Navigation and Management Pages', async ({ page }) => {
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

    await page.goto('/');
    await expect(page.locator('nav button:has-text("Users")')).toBeVisible();
    await expect(page.locator('nav button:has-text("Audit Logs")')).toBeVisible();
    await expect(page.locator('nav button:has-text("Analytics")')).toBeVisible();
  });

  test('4. Mobile Responsive Drawer (< 768px viewport)', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

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

    await page.goto('/');
    const hamburgerBtn = page.locator('button[aria-label="Open navigation drawer"]');
    await expect(hamburgerBtn).toBeVisible();

    // Open mobile drawer
    await hamburgerBtn.click();
    await expect(page.locator('#mobile-drawer').getByText('Synthetic Student One (STUDENT)')).toBeVisible();

    // Click link inside drawer
    await page.locator('#mobile-drawer button:has-text("Placement Drives")').click();
    await expect(page).toHaveURL('/drives');
  });
});
