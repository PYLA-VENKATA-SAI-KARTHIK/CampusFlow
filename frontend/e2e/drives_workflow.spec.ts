import { test, expect } from '@playwright/test';

/**
 * Phase 5A — Playwright E2E: Placement Drive Management & Student Discovery
 * 
 * Verifies:
 * 1. Officer creates, configures eligibility/stages, previews, and publishes a placement drive.
 * 2. Student discovers the published drive on Dashboard and /drives, inspects details & stages, and registers.
 * 3. Officer selects the drive by human-readable dropdown for Manual Broadcast with internal UUID binding.
 */

test.describe('Placement Drive Lifecycle & Student Discovery (Phase 5A)', () => {
  const officerUser = {
    id: '33333333-3333-3333-3333-333333333333',
    email: 'officer@campusflow.edu',
    full_name: 'Placement Officer',
    role: 'OFFICER',
    is_active: true,
  };

  const studentUser = {
    id: '11111111-1111-1111-1111-111111111111',
    email: 'student@campusflow.edu',
    full_name: 'Alex Johnson',
    role: 'STUDENT',
    is_active: true,
  };

  test('1. Officer creates, configures stages, previews, and publishes a placement drive', async ({ page }) => {
    // Seed authenticated officer session
    await page.addInitScript((user) => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-jwt-token-officer',
            refreshToken: 'mock-refresh-token-officer',
            user: user,
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    }, officerUser);

    const mockCompanyId = '99999999-9999-9999-9999-999999999999';
    const mockDriveId = '88888888-8888-8888-8888-888888888888';

    // Mock company creation and list
    await page.route('**/api/v1/companies', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: mockCompanyId,
            name: 'Palantir Technologies',
            website: 'https://palantir.com',
            industry: 'Enterprise Software',
            description: 'Mission-critical analytics and operations software.',
            created_by_user_id: officerUser.id,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: mockCompanyId,
                name: 'Palantir Technologies',
                website: 'https://palantir.com',
                industry: 'Enterprise Software',
              },
            ],
            total: 1,
            page: 1,
            page_size: 100,
            has_next: false,
          }),
        });
      }
    });

    // Mock branches
    await page.route('**/api/v1/branches', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { code: 'CSE', name: 'Computer Science', is_active: true },
          { code: 'IT', name: 'Information Technology', is_active: true },
          { code: 'ECE', name: 'Electronics', is_active: true },
        ]),
      });
    });

    // Mock drive endpoints
    let publishedStatus = 'DRAFT';
    await page.route(`**/api/v1/drives/${mockDriveId}/status`, async (route) => {
      publishedStatus = 'PUBLISHED';
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: mockDriveId,
          company_id: mockCompanyId,
          title: 'Palantir Technologies — Forward Deployed Engineer',
          job_role: 'Forward Deployed Engineer',
          status: 'PUBLISHED',
          created_by_user_id: officerUser.id,
          published_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });

    await page.route(`**/api/v1/drives/${mockDriveId}/stages`, async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '77777777-7777-7777-7777-777777777777',
          drive_id: mockDriveId,
          name: 'Technical Systems Round',
          stage_type: 'TECHNICAL',
          sequence_order: 1,
          is_published: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });

    await page.route('**/api/v1/drives', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: mockDriveId,
            company_id: mockCompanyId,
            title: 'Palantir Technologies — Forward Deployed Engineer',
            job_role: 'Forward Deployed Engineer',
            description: 'Solve complex data challenges.',
            ctc_lpa: 14.5,
            stipend_monthly: 60000,
            location: 'Bengaluru / Hyderabad',
            status: 'DRAFT',
            created_by_user_id: officerUser.id,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: mockDriveId,
                company_id: mockCompanyId,
                title: 'Palantir Technologies — Forward Deployed Engineer',
                job_role: 'Forward Deployed Engineer',
                location: 'Bengaluru / Hyderabad',
                ctc_lpa: 14.5,
                stipend_monthly: 60000,
                status: publishedStatus,
                created_by_user_id: officerUser.id,
                company: {
                  id: mockCompanyId,
                  name: 'Palantir Technologies',
                  website: 'https://palantir.com',
                },
                eligibility_criteria: {
                  min_cgpa: 7.5,
                  max_active_backlogs: 0,
                  eligible_branches: ['CSE', 'IT'],
                },
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              },
            ],
            total: 1,
            page: 1,
            page_size: 100,
            has_next: false,
          }),
        });
      }
    });

    // 1. Navigate to Placement Drives page
    await page.goto('/drives');
    await expect(page.locator('text=+ Create New Drive')).toBeVisible();

    // 2. Open Create Drive Wizard Modal
    await page.click('text=+ Create New Drive');
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();
    await expect(modal.getByText('Create New Placement Drive')).toBeVisible();
    await expect(modal.getByText('Step 1 of 5')).toBeVisible();

    // Step 1: Company & Job Profile
    await modal.getByRole('button', { name: '+ Add New Company' }).click();
    await modal.locator('input[placeholder="e.g. Accenture, Google, TCS"]').fill('Palantir Technologies');
    await modal.locator('input[placeholder="https://company.com"]').fill('https://palantir.com');
    await modal.getByRole('button', { name: '+ Custom / Other Role' }).click();
    await modal.locator('input[placeholder="Enter custom job role (e.g. Embedded Firmware Engineer)"]').fill('Forward Deployed Engineer');
    await modal.getByRole('button', { name: 'Continue →' }).click();

    // Step 2: Compensation
    await expect(modal.getByText('Step 2 of 5')).toBeVisible();
    await modal.locator('input[placeholder="e.g. 4.5"]').fill('14.5');
    await modal.locator('input[placeholder="e.g. 25000"]').fill('60000');
    await modal.getByRole('button', { name: 'Continue →' }).click();

    // Step 3: Eligibility
    await expect(modal.getByText('Step 3 of 5')).toBeVisible();
    await modal.locator('input[type="number"][max="10"]').fill('7.5');
    await modal.getByRole('button', { name: 'Continue →' }).click();

    // Step 4: Selection Process
    await expect(modal.getByText('Step 4 of 5')).toBeVisible();
    await expect(modal.getByText('Selection Process Stages')).toBeVisible();
    await modal.getByRole('button', { name: 'Continue →' }).click();

    // Step 5: Preview & Action
    await expect(modal.getByText('Step 5 of 5')).toBeVisible();
    await expect(modal.getByText('Student View Preview')).toBeVisible();
    await expect(modal.getByText('Palantir Technologies').first()).toBeVisible();
    await expect(modal.getByText('Forward Deployed Engineer').first()).toBeVisible();
    await expect(modal.getByRole('button', { name: 'Publish Drive Now' })).toBeVisible();

    // Publish Drive
    await modal.getByRole('button', { name: 'Publish Drive Now' }).click();

    // Verify modal closes and success banner appears
    await expect(page.locator('text=Drive "Palantir Technologies — Forward Deployed Engineer" has been successfully published!')).toBeVisible();
  });

  test('2. Student discovers drive, views detail with stages timeline, and registers', async ({ page }) => {
    // Seed authenticated student session
    await page.addInitScript((user) => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-jwt-token-student',
            refreshToken: 'mock-refresh-token-student',
            user: user,
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    }, studentUser);

    const mockDriveId = '88888888-8888-8888-8888-888888888888';
    const mockCompanyId = '99999999-9999-9999-9999-999999999999';

    // Mock student profile
    await page.route('**/api/v1/students/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user_id: studentUser.id,
          roll_number: 'CSE-2027-042',
          branch_code: 'CSE',
          batch_year: 2027,
          cgpa: 8.9,
          active_backlogs: 0,
          gender: 'MALE',
        }),
      });
    });

    // Mock applications
    let isRegistered = false;
    await page.route('**/api/v1/students/me/applications**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: isRegistered
            ? [
                {
                  id: '66666666-6666-6666-6666-666666666666',
                  drive_id: mockDriveId,
                  company_name: 'Palantir Technologies',
                  role_title: 'Forward Deployed Engineer',
                  status: 'REGISTERED',
                  created_at: new Date().toISOString(),
                },
              ]
            : [],
          total: isRegistered ? 1 : 0,
          page: 1,
          page_size: 5,
          has_next: false,
        }),
      });
    });

    // Specific route for stages
    await page.route(`**/api/v1/drives/${mockDriveId}/stages`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '1',
            drive_id: mockDriveId,
            name: 'Online Coding Challenge',
            stage_type: 'CODING',
            sequence_order: 1,
            location_or_link: 'HackerRank Assessment Link',
            instructions: '90 minutes algorithmic problem solving.',
            is_published: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: '2',
            drive_id: mockDriveId,
            name: 'Systems Design & Cultural Fit',
            stage_type: 'TECHNICAL',
            sequence_order: 2,
            location_or_link: 'Google Meet',
            instructions: 'Live architecture interview.',
            is_published: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ]),
      });
    });

    // Specific route for registration
    await page.route(`**/api/v1/drives/${mockDriveId}/register`, async (route) => {
      isRegistered = true;
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '66666666-6666-6666-6666-666666666666',
          drive_id: mockDriveId,
          student_user_id: studentUser.id,
          status: 'REGISTERED',
          registered_at: new Date().toISOString(),
        }),
      });
    });

    // Specific route for single drive details
    await page.route(`**/api/v1/drives/${mockDriveId}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: mockDriveId,
          company_id: mockCompanyId,
          title: 'Palantir Technologies — Forward Deployed Engineer 2027',
          job_role: 'Forward Deployed Engineer',
          description: 'Deploy advanced platforms and build mission-critical systems.',
          ctc_lpa: 14.5,
          stipend_monthly: 60000,
          location: 'Bengaluru / Hyderabad',
          status: 'PUBLISHED',
          created_by_user_id: officerUser.id,
          company: {
            id: mockCompanyId,
            name: 'Palantir Technologies',
            website: 'https://palantir.com',
          },
          eligibility_criteria: {
            min_cgpa: 7.5,
            max_active_backlogs: 0,
            eligible_branches: ['CSE', 'IT'],
            eligible_batch_years: [2027],
          },
          my_eligibility: {
            is_eligible: true,
            reasons: [],
          },
          is_registered: isRegistered,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });

    // General route for listing drives
    await page.route('**/api/v1/drives?*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: mockDriveId,
              company_id: mockCompanyId,
              title: 'Palantir Technologies — Forward Deployed Engineer 2027',
              job_role: 'Forward Deployed Engineer',
              location: 'Bengaluru / Hyderabad',
              ctc_lpa: 14.5,
              stipend_monthly: 60000,
              status: 'PUBLISHED',
              created_by_user_id: officerUser.id,
              company: {
                id: mockCompanyId,
                name: 'Palantir Technologies',
                website: 'https://palantir.com',
              },
              eligibility_criteria: {
                min_cgpa: 7.5,
                max_active_backlogs: 0,
                eligible_branches: ['CSE', 'IT'],
              },
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
          total: 1,
          page: 1,
          page_size: 6,
          has_next: false,
        }),
      });
    });

    // 1. Student opens Dashboard
    await page.goto('/');
    await expect(page.locator('text=Upcoming Placement Drives')).toBeVisible();
    await expect(page.locator('text=Palantir Technologies')).toBeVisible();

    // 2. Click "View Drive" to navigate to /drives/:id
    await page.click('button:has-text("View Drive")');
    await expect(page).toHaveURL(new RegExp(`/drives/${mockDriveId}`));

    // 3. Inspect Drive Details page
    await expect(page.locator('h1:has-text("Palantir Technologies")')).toBeVisible();
    await expect(page.getByText('Forward Deployed Engineer', { exact: true })).toBeVisible();
    await expect(page.getByText('₹14.5 LPA')).toBeVisible();
    await expect(page.getByText('You meet all eligibility criteria for this drive.')).toBeVisible();

    // Verify Selection Stages timeline
    await expect(page.getByText('Online Coding Challenge')).toBeVisible();
    await expect(page.getByText('Systems Design & Cultural Fit')).toBeVisible();

    // 4. Register for Drive
    await page.getByRole('button', { name: 'Register for Drive Now' }).click();
    await expect(page.getByText('Your application has been successfully submitted for this drive!')).toBeVisible();
    await expect(page.getByText('Application Submitted')).toBeVisible();
  });

  test('3. Officer selects drive by human-readable dropdown for Manual Broadcast with real UUID internally', async ({ page }) => {
    // Seed authenticated officer session
    await page.addInitScript((user) => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-jwt-token-officer',
            refreshToken: 'mock-refresh-token-officer',
            user: user,
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    }, officerUser);

    const targetUuid = '550e8400-e29b-41d4-a716-446655440000';

    // Mock drives for officer dashboard
    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: targetUuid,
              company_name: 'Accenture',
              role_title: 'Associate Software Engineer',
              status: 'PUBLISHED',
              created_at: new Date().toISOString(),
            },
          ],
          total: 1,
          page: 1,
          page_size: 6,
          has_next: false,
        }),
      });
    });

    let receivedDriveId = '';
    await page.route(`**/api/v1/drives/${targetUuid}/notify`, async (route) => {
      receivedDriveId = targetUuid;
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Notification enqueued for 45 students',
          recipient_count: 45,
        }),
      });
    });

    await page.goto('/');
    await expect(page.locator('text=Drive Manual Broadcast Management')).toBeVisible();

    // Select drive from dropdown
    await page.selectOption('#drive-select-dropdown', targetUuid);

    // Verify #drive-id-input received the real UUID
    await expect(page.locator('#drive-id-input')).toHaveValue(targetUuid);

    // Click Compose Broadcast
    await page.click('button:has-text("Compose Broadcast")');

    // Modal displays human-readable drive name, NOT raw UUID
    await expect(page.locator('text=Manual Notification Broadcast')).toBeVisible();
    await expect(page.getByRole('dialog').getByText('Accenture — Associate Software Engineer')).toBeVisible();

    // Fill message and dispatch
    await page.fill('#broadcast-title', 'Pre-Placement Talk Scheduled');
    await page.fill('#broadcast-body', 'Join the orientation on Friday at 10 AM.');
    await page.click('button:has-text("Review Broadcast")');

    await expect(page.locator('text=Confirm Notification Broadcast')).toBeVisible();
    await page.click('button:has-text("Send Broadcast Now")');

    // Verify success
    await expect(page.locator('text=Broadcast Dispatched Successfully')).toBeVisible();
    expect(receivedDriveId).toBe(targetUuid);
  });
});
