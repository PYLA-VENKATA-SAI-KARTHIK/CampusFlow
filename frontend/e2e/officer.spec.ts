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

  test('officer accesses /drives/:id and manages applicants via Applicant Management workspace', async ({ page }) => {
    const driveId = '88888888-8888-8888-8888-888888888888';
    const stageId = '77777777-7777-7777-7777-777777777777';

    // Mock drive details
    await page.route(`**/api/v1/drives/${driveId}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: driveId,
          company_id: '99999999-9999-9999-9999-999999999999',
          title: 'Stripe — Software Engineer',
          job_role: 'Software Engineer',
          description: 'Payment systems.',
          ctc_lpa: 24.0,
          status: 'PUBLISHED',
          created_by_user_id: '33333333-3333-3333-3333-333333333333',
          company: { name: 'Stripe', website: 'https://stripe.com' },
          eligibility_criteria: { min_cgpa: 8.0, eligible_branches: ['CSE', 'ECE'] },
        }),
      });
    });

    // Mock stages
    await page.route(`**/api/v1/drives/${driveId}/stages`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: stageId,
            drive_id: driveId,
            name: 'Technical Architecture Round',
            stage_type: 'TECHNICAL',
            sequence_order: 1,
            is_published: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ]),
      });
    });

    // Mock branches
    await page.route('**/api/v1/branches', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { code: 'CSE', name: 'Computer Science', is_active: true },
          { code: 'ECE', name: 'Electronics', is_active: true },
        ]),
      });
    });

    // Mock registrations
    const mockApplicants = [
      {
        id: 'reg-1',
        drive_id: driveId,
        student_user_id: 'stu-user-1',
        resume_gcs_path_at_registration: 'resumes/stu-1/resume.pdf',
        status: 'REGISTERED',
        registered_at: '2026-09-10T10:00:00Z',
        updated_at: '2026-09-10T10:00:00Z',
        student: {
          id: 'stu-profile-1',
          user_id: 'stu-user-1',
          full_name: 'Devin Thorne',
          email: 'devin@campusflow.edu',
          roll_number: 'CSE-2027-010',
          branch: 'CSE',
          batch_year: 2027,
          cgpa: 8.95,
          active_backlogs: 0,
        },
        current_stage: null,
      },
      {
        id: 'reg-2',
        drive_id: driveId,
        student_user_id: 'stu-user-2',
        resume_gcs_path_at_registration: 'resumes/stu-2/resume.pdf',
        status: 'REGISTERED',
        registered_at: '2026-09-10T11:00:00Z',
        updated_at: '2026-09-10T11:00:00Z',
        student: {
          id: 'stu-profile-2',
          user_id: 'stu-user-2',
          full_name: 'Elena Rostova',
          email: 'elena@campusflow.edu',
          roll_number: 'ECE-2027-025',
          branch: 'ECE',
          batch_year: 2027,
          cgpa: 9.1,
          active_backlogs: 0,
        },
        current_stage: {
          stage_id: stageId,
          stage_name: 'Technical Architecture Round',
          stage_type: 'TECHNICAL',
          sequence_order: 1,
          status: 'SHORTLISTED',
          result_notes: 'Strong DSA foundation',
          assigned_at: '2026-09-11T10:00:00Z',
        },
      },
    ];

    await page.route(`**/api/v1/drives/${driveId}/registrations*`, async (route) => {
      const url = new URL(route.request().url());
      const search = url.searchParams.get('search');
      let filtered = mockApplicants;
      if (search) {
        filtered = mockApplicants.filter((a) =>
          a.student.full_name.toLowerCase().includes(search.toLowerCase())
        );
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: filtered,
          total: filtered.length,
          page: 1,
          page_size: 20,
          has_next: false,
        }),
      });
    });

    // Mock bulk shortlist
    let shortlistedIds: string[] = [];
    await page.route(`**/api/v1/drives/${driveId}/stages/${stageId}/shortlist`, async (route) => {
      const postData = route.request().postDataJSON();
      shortlistedIds = postData.student_ids;
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ message: `${shortlistedIds.length} students shortlisted` }),
      });
    });

    // Mock bulk status
    let bulkStatusUpdated: any = null;
    await page.route(`**/api/v1/drives/${driveId}/stages/${stageId}/bulk-status`, async (route) => {
      bulkStatusUpdated = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Candidate assignments updated to SELECTED' }),
      });
    });

    // Mock resume download URL
    await page.route(`**/api/v1/officers/students/stu-profile-1/resume-download-url`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ url: 'https://storage.googleapis.com/test-bucket/signed-resume-1.pdf' }),
      });
    });

    // 1. Navigate to Drive Details
    await page.goto(`/drives/${driveId}`);

    // Verify Officer Applicant Workspace is displayed
    const workspace = page.locator('[data-testid="applicant-workspace"]');
    await expect(workspace).toBeVisible();
    await expect(workspace.getByText('Applicant Management')).toBeVisible();
    await expect(workspace.getByText('Devin Thorne')).toBeVisible();
    await expect(workspace.getByText('Elena Rostova')).toBeVisible();
    await expect(workspace.getByText('Not Assigned')).toBeVisible();

    // 2. Test Search debounce
    await page.fill('#applicant-search-input', 'Devin');
    await expect(workspace.getByText('Devin Thorne')).toBeVisible();
    await expect(workspace.getByText('Elena Rostova')).not.toBeVisible();

    // Clear search
    await page.fill('#applicant-search-input', '');
    await expect(workspace.getByText('Elena Rostova')).toBeVisible();

    // 3. Test Row Selection & Bulk Action Bar
    await page.click('[data-testid="applicant-select-stu-user-1"]');
    const bulkBar = page.locator('[data-testid="bulk-action-bar"]');
    await expect(bulkBar).toBeVisible();
    await expect(bulkBar.getByText('1 Candidate Selected')).toBeVisible();

    // 4. Test Bulk Shortlist Modal
    await page.click('#btn-bulk-shortlist');
    const shortlistModal = page.getByRole('dialog');
    await expect(shortlistModal).toBeVisible();
    await expect(shortlistModal.getByText('Shortlist Candidates to Stage')).toBeVisible();
    await shortlistModal.getByRole('button', { name: 'Confirm Shortlisting' }).click();
    await expect(shortlistModal).not.toBeVisible();
    expect(shortlistedIds).toEqual(['stu-user-1']);

    // 5. Test Bulk Status Modal
    await page.click('[data-testid="applicant-select-stu-user-2"]');
    await expect(bulkBar).toBeVisible();
    await page.click('#btn-bulk-status');
    const statusModal = page.getByRole('dialog');
    await expect(statusModal).toBeVisible();
    await expect(statusModal.getByText('Update Candidate Stage Status')).toBeVisible();
    await statusModal.locator('select').nth(1).selectOption('SELECTED');
    await statusModal.locator('textarea').fill('Cleared architecture round with distinction.');
    await statusModal.getByRole('button', { name: 'Confirm Status Update' }).click();
    await expect(statusModal).not.toBeVisible();
    expect(bulkStatusUpdated.status).toBe('SELECTED');
    expect(bulkStatusUpdated.result_notes).toContain('Cleared architecture round');

    // 6. Test Candidate Quick View Review Modal & Resume Access
    await page.click('[data-testid="view-candidate-stu-user-1"]');
    const reviewModal = page.getByRole('dialog');
    await expect(reviewModal).toBeVisible();
    await expect(reviewModal.getByText('Devin Thorne')).toBeVisible();
    await expect(reviewModal.getByText('devin@campusflow.edu')).toBeVisible();
    await expect(reviewModal.getByText('CSE-2027-010')).toBeVisible();
    await expect(reviewModal.getByText('8.95')).toBeVisible();
    await expect(reviewModal.getByText('REGISTERED', { exact: true }).first()).toBeVisible();
    await expect(page.locator('#btn-download-resume')).toBeVisible();
    await expect(page.locator('#btn-close-review')).toBeVisible();
    await page.locator('#btn-close-review').click();
    await expect(reviewModal).not.toBeVisible();
  });

  test('student does NOT see Applicant Management workspace on /drives/:id', async ({ page }) => {
    const driveId = '88888888-8888-8888-8888-888888888888';

    // Seed student user
    await page.addInitScript(() => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-jwt-token-student',
            refreshToken: 'mock-refresh-token-student',
            user: {
              id: '11111111-1111-1111-1111-111111111111',
              email: 'student@campusflow.edu',
              full_name: 'Alex Student',
              role: 'STUDENT',
              is_active: true,
            },
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    });

    await page.route(`**/api/v1/drives/${driveId}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: driveId,
          company_id: '99999999-9999-9999-9999-999999999999',
          title: 'Stripe — Software Engineer',
          job_role: 'Software Engineer',
          status: 'PUBLISHED',
          created_by_user_id: '33333333-3333-3333-3333-333333333333',
          company: { name: 'Stripe' },
        }),
      });
    });

    await page.route(`**/api/v1/drives/${driveId}/stages`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.goto(`/drives/${driveId}`);
    await expect(page.locator('h1:has-text("Stripe")')).toBeVisible();
    await expect(page.locator('[data-testid="applicant-workspace"]')).not.toBeVisible();
    await expect(page.locator('text=Applicant Management')).not.toBeVisible();
  });
});

