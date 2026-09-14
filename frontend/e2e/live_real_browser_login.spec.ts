import { test, expect } from '@playwright/test';

test.describe('Real Live Browser Cross-Role Authentication (No Mocking)', () => {

  test('Case A: registration number SYN26CSE00001 + correct password logs in and loads live student dashboard', async ({ page }) => {
    // Navigate to live login page
    await page.goto('/login');
    await expect(page.locator('h2')).toContainText(/Sign in to your account/i);

    // Enter registration number as string and correct password
    await page.fill('input[name="email"]', 'SYN26CSE00001');
    await page.fill('input[type="password"]', 'TestStudent@123');
    await page.click('button:has-text("Sign in")');

    // Verify redirected to dashboard with authenticated session
    await expect(page).toHaveURL('/', { timeout: 10000 });
    await expect(page.locator('nav').getByText('Synthetic Student One (STUDENT)')).toBeVisible();
    await expect(page.locator('h1')).toContainText(/Welcome/i);
  });

  test('Case B: student1@campusflow.edu + correct password logs in and loads live student dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'student1@campusflow.edu');
    await page.fill('input[type="password"]', 'TestStudent@123');
    await page.click('button:has-text("Sign in")');

    await expect(page).toHaveURL('/', { timeout: 10000 });
    await expect(page.locator('nav').getByText('Synthetic Student One (STUDENT)')).toBeVisible();
  });

  test('Case C: 99230041249 + wrong password displays controlled error with zero React crashes', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', '99230041249');
    await page.fill('input[type="password"]', 'WrongPassword@999');
    await page.click('button:has-text("Sign in")');

    const errorAlert = page.locator('.bg-red-50');
    await expect(errorAlert).toBeVisible();
    await expect(errorAlert).toContainText(/Invalid/i);
    await expect(page.locator('text=Objects are not valid as a React child')).not.toBeVisible();
  });

  test('Case D: UNKNOWN999 + password displays controlled error with zero React crashes', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'UNKNOWN999');
    await page.fill('input[type="password"]', 'Password@123');
    await page.click('button:has-text("Sign in")');

    const errorAlert = page.locator('.bg-red-50');
    await expect(errorAlert).toBeVisible();
    await expect(errorAlert).toContainText(/Invalid/i);
    await expect(page.locator('text=Objects are not valid as a React child')).not.toBeVisible();
  });

  test('Case E: empty identifier displays controlled validation error with zero React crashes', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', '');
    await page.fill('input[type="password"]', 'Password@123');
    await page.click('button:has-text("Sign in")');

    // Frontend validation message or alert
    await expect(page.getByText('Email or registration number is required')).toBeVisible();
    await expect(page.locator('text=Objects are not valid as a React child')).not.toBeVisible();
  });

});
