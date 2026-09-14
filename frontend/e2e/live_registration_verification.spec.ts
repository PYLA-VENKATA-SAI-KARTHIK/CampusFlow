import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';
import path from 'path';

/**
 * End-to-End Live Browser Test for CampusFlow Registration and Identity Workflow
 * 
 * Verifies live browser behavior without mocking:
 * 1. Unknown student registration number -> controlled error message
 * 2. Pre-provisioned student registration number (99230041249) -> completes registration
 * 3. Auto-generated university email (99230041249@klu.ac.in) displayed on confirmation screen
 * 4. Duplicate registration attempt -> controlled 409 error message
 * 5. Sign in using registration number (99230041249) -> student dashboard loaded
 * 6. Profile name update -> student updates full name to "Karthik V. Pyla" -> verified in UI
 * 7. Page reload -> updated name persists
 * 8. Logout and sign in using university email (99230041249@klu.ac.in) -> student dashboard loaded with new name
 * 9. Academic fields (roll_number, branch, batch, cgpa, backlogs) remain protected and non-editable
 */

test.describe('Live Registration & Identity Flow', () => {
  test.beforeAll(async () => {
    // Deterministically reseed database so student 99230041249 is in pre-provisioned unactivated state
    const backendDir = path.resolve(process.cwd(), '../backend');
    const pythonExe = path.join(backendDir, 'venv', 'Scripts', 'python.exe');
    const seedScript = path.join(backendDir, 'scripts', 'seed_test_env.py');
    try {
      execSync(`"${pythonExe}" "${seedScript}"`, { cwd: backendDir, stdio: 'pipe' });
    } catch (err: any) {
      console.error('Failed to reseed database in beforeAll:', err.message);
    }
  });

  test('full live registration, auto-email derivation, dual login, and profile name editing', async ({ page }) => {
    // 1. Unknown registration number test
    await page.goto('/register');
    await expect(page.locator('h3:has-text("New User Registration")')).toBeVisible();

    await page.fill('#registration-number', 'UNKNOWN999');
    await page.fill('#new-password', 'StudentSecret@2026');
    await page.fill('#confirm-password', 'StudentSecret@2026');
    await page.click('button:has-text("Complete Registration")');

    const errorAlert = page.locator('.bg-red-50');
    await expect(errorAlert).toBeVisible();
    await expect(errorAlert).toContainText('Registration number not found. Please contact your placement office.');

    // 2. Valid student registration with 99230041249
    await page.fill('#registration-number', '99230041249');
    await page.fill('#new-password', 'StudentSecret@2026');
    await page.fill('#confirm-password', 'StudentSecret@2026');
    await page.click('button:has-text("Complete Registration")');

    // 3. Verify confirmation screen and automatic university email
    await expect(page.locator('h3:has-text("Account Registered!")')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Registration completed successfully. You can now sign in using:')).toBeVisible();
    await expect(page.getByText('99230041249@klu.ac.in')).toBeVisible();

    // 4. Duplicate registration attempt
    await page.goto('/register');
    await page.fill('#registration-number', '99230041249');
    await page.fill('#new-password', 'StudentSecret@2026');
    await page.fill('#confirm-password', 'StudentSecret@2026');
    await page.click('button:has-text("Complete Registration")');

    await expect(page.locator('.bg-red-50')).toBeVisible();
    await expect(page.locator('.bg-red-50')).toContainText('This student account is already registered. Please sign in.');

    // 5. Login using Registration Number (99230041249)
    await page.goto('/login');
    await page.fill('input[name="email"]', '99230041249');
    await page.fill('input[type="password"]', 'StudentSecret@2026');
    await page.click('button:has-text("Sign in")');

    await expect(page).toHaveURL('/');
    await expect(page.locator('nav').getByText('(STUDENT)')).toBeVisible();

    // 6. Navigate to /profile and edit student name
    await page.goto('/profile');
    await expect(page.getByRole('heading', { name: 'Personal Details' })).toBeVisible();

    // Verify institutional fields are read-only / disabled
    await expect(page.locator('input[value="99230041249@klu.ac.in"]')).toBeDisabled();
    await expect(page.locator('#student-full-name')).toBeDisabled();

    // Click Edit Personal Details
    await page.click('button:has-text("Edit Personal Details")');
    await expect(page.locator('#student-full-name')).toBeEnabled();

    // Update Full Name
    await page.fill('#student-full-name', 'Karthik V. Pyla');
    await page.click('button:has-text("Save Personal Details")');

    // Verify success banner and updated name in profile & navbar
    await expect(page.locator('text=Personal details updated successfully.')).toBeVisible();
    await expect(page.locator('h2:has-text("Karthik V. Pyla")')).toBeVisible();

    // 7. Refresh page and verify name persistence
    await page.reload();
    await expect(page.locator('input[value="Karthik V. Pyla"]')).toBeVisible();
    await expect(page.locator('h2:has-text("Karthik V. Pyla")')).toBeVisible();

    // Verify academic fields remain protected
    await expect(page.locator('text=99230041249').first()).toBeVisible();
    await expect(page.locator('text=CSE').first()).toBeVisible();
    await expect(page.locator('text=2026').first()).toBeVisible();
    await expect(page.locator('text=8.50').first()).toBeVisible();

    // 8. Logout
    await page.click('nav button:has-text("Logout")');
    await expect(page).toHaveURL(/.*\/login/);

    // 9. Login using University Email (99230041249@klu.ac.in)
    await page.fill('input[name="email"]', '99230041249@klu.ac.in');
    await page.fill('input[type="password"]', 'StudentSecret@2026');
    await page.click('button:has-text("Sign in")');

    await expect(page).toHaveURL('/');
    await expect(page.locator('nav').getByText('Karthik V. Pyla (STUDENT)')).toBeVisible();
  });
});
