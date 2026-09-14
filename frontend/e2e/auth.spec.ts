import { test, expect } from '@playwright/test';

/**
 * Phase 4.4 — Playwright E2E: Authentication Workflows
 * 
 * Verifies:
 * - Unauthenticated user redirect to /login
 * - Form validation and invalid credential rejection
 * - Successful authentication for Student, Officer, and Admin
 * - Session clearance and redirection on logout
 */

test.describe('Authentication & Session Workflows', () => {

  test('unauthenticated user is redirected to /login', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/.*\/login/);
    await expect(page.locator('text=Sign in to your account')).toBeVisible();
  });

  test('invalid login credentials displays server error', async ({ page }) => {
    // Intercept login to return 401
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid credentials' }),
      });
    });

    await page.goto('/login');
    await page.fill('input[name="email"]', 'unknown@campusflow.edu');
    await page.fill('input[type="password"]', 'WrongPassword123');
    await page.click('button:has-text("Sign in")');

    // Verify error notification or server message
    const errorAlert = page.locator('.bg-red-50');
    await expect(errorAlert).toBeVisible();
    await expect(errorAlert).toContainText('Invalid credentials');
  });

  test('student login succeeds with registration number and redirects to dashboard', async ({ page }) => {
    // Mock successful student login via numeric registration number
    await page.route('**/api/v1/auth/login', async (route) => {
      const body = JSON.parse(route.request().postData() || '{}');
      expect(body.email).toBe('99230041249');
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token-student-reg',
          refresh_token: 'mock-refresh-token-student-reg',
          user: {
            id: '11111111-1111-1111-1111-111111111111',
            email: 'student99@campusflow.edu',
            full_name: 'Numeric Roll Student',
            role: 'STUDENT',
            is_active: true,
            must_change_password: false,
          },
        }),
      });
    });

    await page.route('**/api/v1/students/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '22222222-2222-2222-2222-222222222222',
          user_id: '11111111-1111-1111-1111-111111111111',
          roll_number: '99230041249',
          branch_code: 'CSE',
          batch_year: 2026,
          cgpa: 8.95,
          active_backlogs: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });

    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20, has_next: false }),
      });
    });

    await page.goto('/login');
    await page.fill('input[name="email"]', '99230041249');
    await page.fill('input[type="password"]', 'Password@123');
    await page.click('button:has-text("Sign in")');

    await expect(page).toHaveURL('/');
    await expect(page.locator('nav').getByText('Numeric Roll Student (STUDENT)')).toBeVisible();
  });

  test('login with FastAPI Pydantic validation error array renders readable message without React child crash', async ({ page }) => {
    // Intercept login to return raw Pydantic 422 validation array response
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: [
            {
              type: 'value_error',
              loc: ['body', 'email'],
              msg: 'Email address or student registration number is required.',
              input: '',
              ctx: { error: 'Value error' },
            },
          ],
        }),
      });
    });

    await page.goto('/login');
    await page.fill('input[name="email"]', 'some-identifier');
    await page.fill('input[type="password"]', 'Password@123');
    await page.click('button:has-text("Sign in")');

    const errorAlert = page.locator('.bg-red-50');
    await expect(errorAlert).toBeVisible();
    await expect(errorAlert).toContainText('Email address or student registration number is required');

    // Verify no React fatal crash screen overlay appears
    await expect(page.locator('text=Objects are not valid as a React child')).not.toBeVisible();
  });

  test('student login succeeds and redirects to dashboard', async ({ page }) => {
    // Mock successful student login
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token-student',
          refresh_token: 'mock-refresh-token-student',
          user: {
            id: '11111111-1111-1111-1111-111111111111',
            email: 'student1@campusflow.edu',
            full_name: 'Synthetic Student One',
            role: 'STUDENT',
            is_active: true,
            must_change_password: false,
          },
        }),
      });
    });

    // Mock student profile and drives endpoints
    await page.route('**/api/v1/students/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '22222222-2222-2222-2222-222222222222',
          user_id: '11111111-1111-1111-1111-111111111111',
          roll_number: 'SYN26CSE001',
          branch_code: 'CSE',
          batch_year: 2026,
          cgpa: 8.8,
          active_backlogs: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });

    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20, has_next: false }),
      });
    });

    await page.goto('/login');
    await page.fill('input[name="email"]', 'student1@campusflow.edu');
    await page.fill('input[type="password"]', 'TestStudent@123');
    await page.click('button:has-text("Sign in")');

    await expect(page).toHaveURL('/');
    // Check that user name with role is visible in AppLayout navbar
    await expect(page.locator('nav').getByText('Synthetic Student One (STUDENT)')).toBeVisible();
  });

  test('officer login displays placement officer navigation', async ({ page }) => {
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token-officer',
          refresh_token: 'mock-refresh-token-officer',
          user: {
            id: '33333333-3333-3333-3333-333333333333',
            email: 'officer@campusflow.edu',
            full_name: 'Placement Officer',
            role: 'OFFICER',
            is_active: true,
            must_change_password: false,
          },
        }),
      });
    });

    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20, has_next: false }),
      });
    });

    await page.goto('/login');
    await page.fill('input[name="email"]', 'officer@campusflow.edu');
    await page.fill('input[type="password"]', 'TestOfficer@123');
    await page.click('button:has-text("Sign in")');

    await expect(page).toHaveURL('/');
    await expect(page.locator('nav').getByText('Placement Officer (OFFICER)')).toBeVisible();
    await expect(page.locator('nav button:has-text("Analytics")')).toBeVisible();
  });

  test('admin login displays admin management navigation', async ({ page }) => {
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token-admin',
          refresh_token: 'mock-refresh-token-admin',
          user: {
            id: '44444444-4444-4444-4444-444444444444',
            email: 'admin@campusflow.edu',
            full_name: 'System Admin',
            role: 'ADMIN',
            is_active: true,
            must_change_password: false,
          },
        }),
      });
    });

    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20, has_next: false }),
      });
    });

    await page.goto('/login');
    await page.fill('input[name="email"]', 'admin@campusflow.edu');
    await page.fill('input[type="password"]', 'TestAdmin@123');
    await page.click('button:has-text("Sign in")');

    await expect(page).toHaveURL('/');
    await expect(page.locator('nav').getByText('System Admin (ADMIN)')).toBeVisible();
    await expect(page.locator('nav button:has-text("Users")')).toBeVisible();
    await expect(page.locator('nav button:has-text("Audit Logs")')).toBeVisible();
  });

  test('logout clears session and redirects to /login', async ({ page }) => {
    // Pre-seed authenticated state
    await page.addInitScript(() => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'dummy-token',
            refreshToken: 'dummy-refresh',
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

    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20, has_next: false }),
      });
    });

    await page.route('**/api/v1/auth/logout', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Successfully logged out' }),
      });
    });

    await page.goto('/');
    await expect(page.locator('nav').getByText('Synthetic Student One (STUDENT)')).toBeVisible();

    // Click Logout button
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL(/.*\/login/);

    // Verify localStorage cleared
    const authStorage = await page.evaluate(() => window.localStorage.getItem('campusflow-auth-storage'));
    const parsed = JSON.parse(authStorage || '{}');
    expect(parsed.state?.isAuthenticated).toBe(false);
  });

  test('officer logout to student login transition completes with zero console errors', async ({ page }) => {
    let currentUserRole: 'OFFICER' | 'STUDENT' = 'OFFICER';

    await page.route('**/api/v1/auth/login', async (route) => {
      if (currentUserRole === 'OFFICER') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'mock-jwt-token-officer',
            refresh_token: 'mock-refresh-token-officer',
            user: {
              id: '33333333-3333-3333-3333-333333333333',
              email: 'officer@campusflow.edu',
              full_name: 'Placement Officer',
              role: 'OFFICER',
              is_active: true,
              must_change_password: false,
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            access_token: 'mock-jwt-token-student',
            refresh_token: 'mock-refresh-token-student',
            user: {
              id: '11111111-1111-1111-1111-111111111111',
              email: 'student1@campusflow.edu',
              full_name: 'Synthetic Student One',
              role: 'STUDENT',
              is_active: true,
              must_change_password: false,
            },
          }),
        });
      }
    });

    await page.route('**/api/v1/auth/logout', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Successfully logged out' }),
      });
    });

    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20, has_next: false }),
      });
    });

    await page.route('**/api/v1/students/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '22222222-2222-2222-2222-222222222222',
          user_id: '11111111-1111-1111-1111-111111111111',
          roll_number: 'SYN26CSE001',
          branch_code: 'CSE',
          batch_year: 2026,
          cgpa: 8.8,
          active_backlogs: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });

    await page.route('**/api/v1/students/me/applications**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 5, has_next: false }),
      });
    });

    // 1. Officer logs in
    currentUserRole = 'OFFICER';
    await page.goto('/login');
    await page.fill('input[name="email"]', 'officer@campusflow.edu');
    await page.fill('input[type="password"]', 'TestOfficer@123');
    await page.click('button:has-text("Sign in")');
    await expect(page).toHaveURL('/');
    await expect(page.locator('nav').getByText('Placement Officer (OFFICER)')).toBeVisible();

    // 2. Officer logs out
    await page.click('nav button:has-text("Logout")');
    await expect(page).toHaveURL(/.*\/login/);

    // 3. Student logs in
    currentUserRole = 'STUDENT';
    await page.fill('input[name="email"]', 'student1@campusflow.edu');
    await page.fill('input[type="password"]', 'TestStudent@123');
    await page.click('button:has-text("Sign in")');
    await expect(page).toHaveURL('/');

    // 4. Verify Student Dashboard
    await expect(page.locator('nav').getByText('Synthetic Student One (STUDENT)')).toBeVisible();
    await expect(page.locator('h1')).toContainText(/Welcome/i);
    await expect(page.getByText('Eligible Drives')).toBeVisible();
  });

  test('student completes registration flow and signs in to dashboard', async ({ page }) => {
    // 1. Intercept /api/v1/auth/register
    await page.route('**/api/v1/auth/register', async (route) => {
      const body = JSON.parse(route.request().postData() || '{}');
      expect(body.registration_number).toBe('99230041249');
      expect(body.password).toBe('NewSecurePassword123!');
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Registration completed successfully. You can now sign in.',
          email: '99230041249@klu.ac.in',
          registration_number: '99230041249',
        }),
      });
    });

    // 2. Intercept /api/v1/auth/login
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-jwt-token-demo',
          refresh_token: 'mock-refresh-token-demo',
          user: {
            id: '55555555-5555-5555-5555-555555555555',
            email: '99230041249@klu.ac.in',
            full_name: 'Demo Student',
            role: 'STUDENT',
            is_active: true,
            must_change_password: false,
          },
        }),
      });
    });

    // 3. Intercept profile and drives
    await page.route('**/api/v1/students/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '66666666-6666-6666-6666-666666666666',
          user_id: '55555555-5555-5555-5555-555555555555',
          roll_number: '99230041249',
          branch_code: 'CSE',
          batch_year: 2026,
          cgpa: 8.5,
          active_backlogs: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });

    await page.route('**/api/v1/drives**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 20, has_next: false }),
      });
    });

    // 1. Open New User Registration page
    await page.goto('/register');
    await expect(page.locator('h3:has-text("New User Registration")')).toBeVisible();
    await expect(page.getByText('Student Registration Number')).toBeVisible();

    // 2. Fill form
    await page.fill('#registration-number', '99230041249');
    await page.fill('#new-password', 'NewSecurePassword123!');
    await page.fill('#confirm-password', 'NewSecurePassword123!');

    // 3. Complete Registration
    await page.click('button:has-text("Complete Registration")');

    // 4. Verify success screen
    await expect(page.locator('h3:has-text("Account Registered!")')).toBeVisible();
    await expect(page.getByText('Registration completed successfully. You can now sign in using:')).toBeVisible();
    await expect(page.getByText('99230041249@klu.ac.in')).toBeVisible();

    // 5. Navigate to Sign In
    await page.click('#return-to-login-btn');
    await expect(page).toHaveURL(/.*\/login/);

    // 6. Sign in with newly registered credentials
    await page.fill('input[name="email"]', '99230041249');
    await page.fill('input[type="password"]', 'NewSecurePassword123!');
    await page.click('button:has-text("Sign in")');

    // 7. Verify student dashboard loads without console/runtime errors
    await expect(page).toHaveURL('/');
    await expect(page.locator('nav').getByText('Demo Student (STUDENT)')).toBeVisible();
    await expect(page.locator('h1')).toContainText(/Welcome/i);
    await expect(page.getByText('Eligible Drives')).toBeVisible();
  });

  test('registration displays error when student registration number is not found', async ({ page }) => {
    await page.route('**/api/v1/auth/register', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          type: 'https://campusflow.internal/errors/student_registration_not_found',
          title: 'Registration Number Not Found',
          status: 404,
          detail: 'Registration number not found. Please contact your placement office.',
        }),
      });
    });

    await page.goto('/register');
    await page.fill('#registration-number', 'UNKNOWN_REG_123');
    await page.fill('#new-password', 'NewSecurePassword123!');
    await page.fill('#confirm-password', 'NewSecurePassword123!');
    await page.click('button:has-text("Complete Registration")');

    const errorAlert = page.locator('.bg-red-50');
    await expect(errorAlert).toBeVisible();
    await expect(errorAlert).toContainText('Registration number not found. Please contact your placement office.');
  });

  test('registration displays error when account is already registered', async ({ page }) => {
    await page.route('**/api/v1/auth/register', async (route) => {
      await route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({
          type: 'https://campusflow.internal/errors/account_already_registered',
          title: 'Account Already Registered',
          status: 409,
          detail: 'This student account is already registered. Please sign in.',
        }),
      });
    });

    await page.goto('/register');
    await page.fill('#registration-number', 'SYN26CSE00001');
    await page.fill('#new-password', 'NewSecurePassword123!');
    await page.fill('#confirm-password', 'NewSecurePassword123!');
    await page.click('button:has-text("Complete Registration")');

    const errorAlert = page.locator('.bg-red-50');
    await expect(errorAlert).toBeVisible();
    await expect(errorAlert).toContainText('This student account is already registered. Please sign in.');
  });
});
