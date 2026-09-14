import { test, expect } from '@playwright/test';

test.describe('Placement Drive Multi-Round Qualified List Upload Workflow', () => {
  const mockDriveId = '11111111-2222-3333-4444-555555555555';
  const mockStage1Id = 'aaaa1111-2222-3333-4444-555555555555';
  const mockStage2Id = 'bbbb2222-3333-4444-5555-666666666666';

  test.beforeEach(async ({ page }) => {
    // Mock Drive details
    await page.route(`**/api/v1/drives/${mockDriveId}`, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: mockDriveId,
            company_id: 'comp-123',
            title: 'TCS Digital Recruitment 2026',
            job_role: 'AI/ML Engineer',
            status: 'PUBLISHED',
            ctc_lpa: 12.0,
            is_registered: true,
            company: {
              name: 'TCS',
              industry: 'Technology',
            },
            eligibility_criteria: {
              min_cgpa: 7.0,
              max_active_backlogs: 0,
              eligible_branches: ['CSE'],
              eligible_batch_years: [2026],
            },
            created_by_user_id: 'officer-1',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.continue();
      }
    });

    // Mock Stages
    await page.route(`**/api/v1/drives/${mockDriveId}/stages`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: mockStage1Id,
            drive_id: mockDriveId,
            name: 'Aptitude Assessment',
            stage_type: 'APTITUDE',
            sequence_order: 1,
            is_published: true,
            student_count: 150,
            my_status: 'SHORTLISTED',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: mockStage2Id,
            drive_id: mockDriveId,
            name: 'Technical Assessment',
            stage_type: 'TECHNICAL',
            sequence_order: 2,
            is_published: true,
            student_count: 80,
            my_status: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ]),
      });
    });

    // Mock Branches
    await page.route('**/api/v1/branches', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([{ code: 'CSE', name: 'Computer Science and Engineering', is_active: true }]),
      });
    });

    // Mock Registrations
    await page.route(`**/api/v1/drives/${mockDriveId}/registrations*`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          has_next: false,
        }),
      });
    });
  });

  test('Officer views Drive Details, sees Round Management cards and interacts with Round Upload Modal', async ({ page }) => {
    // Authenticate as Placement Officer
    await page.addInitScript(() => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-officer-token',
            refreshToken: 'mock-officer-refresh',
            user: {
              id: 'officer-1',
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

    await page.goto(`/drives/${mockDriveId}`);

    // Verify Round / Stage Management Section is visible
    await expect(page.locator('text=Round / Stage Management')).toBeVisible();
    await expect(page.locator('text=ROUND 1')).toBeVisible();
    await expect(page.locator('text=Aptitude Assessment')).toBeVisible();
    await expect(page.locator('text=150 Students')).toBeVisible();

    await expect(page.locator('text=ROUND 2')).toBeVisible();
    await expect(page.locator('text=Technical Assessment')).toBeVisible();
    await expect(page.locator('text=80 Students')).toBeVisible();

    // Verify Upload Buttons
    const uploadBtn1 = page.locator('[data-testid="upload-stage-btn-1"]');
    await expect(uploadBtn1).toBeVisible();
    await expect(uploadBtn1).toHaveText('Upload Updated List');

    // Click Upload button for Round 1
    await uploadBtn1.click();

    // Verify Modal Opens
    await expect(page.locator('h3:has-text("Upload Qualified Students: Aptitude Assessment")')).toBeVisible();
    await expect(page.locator('[data-testid="stage-file-upload-input"]')).toBeAttached();

    // Close Modal
    await page.click('button:has-text("Cancel")');
    await expect(page.locator('h3:has-text("Upload Qualified Students: Aptitude Assessment")')).not.toBeVisible();
  });

  test('Student views Drive Details and sees dynamic Placement Updates progression', async ({ page }) => {
    // Authenticate as Student
    await page.addInitScript(() => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-student-token',
            refreshToken: 'mock-student-refresh',
            user: {
              id: 'student-1',
              email: '009923001@klu.ac.in',
              full_name: 'Student 009923001',
              role: 'STUDENT',
              is_active: true,
            },
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    });

    await page.goto(`/drives/${mockDriveId}`);

    // Verify Placement Updates Progression
    await expect(page.locator('text=Placement Updates & Selection Progression')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Application Submitted' })).toBeVisible();
    await expect(page.locator('text=Applied')).toBeVisible();

    // Round 1 is Qualified
    await expect(page.locator('text=Aptitude Assessment')).toBeVisible();
    await expect(page.getByText('Qualified', { exact: true })).toBeVisible();

    // Round 2 is Pending / Upcoming
    await expect(page.locator('text=Technical Assessment')).toBeVisible();
    await expect(page.getByText('Pending / Upcoming', { exact: true })).toBeVisible();
  });
});
