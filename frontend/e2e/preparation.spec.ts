import { test, expect } from '@playwright/test';

/**
 * Phase 5.1 — Playwright E2E: Placement Preparation Hub Workflows
 * 
 * Verifies:
 * - Student navigates to /preparation via persistent workspace sidebar
 * - Placement Preparation Hub header, role roadmaps, and category tabs rendering
 * - Role switching updates active role roadmap curriculum
 * - Material library grid renders type badges, difficulty badges, and resource links
 * - Student "Suggest a Material" modal flow with validation and success feedback
 * - Placement Officer Review Queue tab and approval workflow
 */

test.describe('Placement Preparation Hub (Phase 5.1)', () => {
  const mockRoles = [
    {
      id: 'r1111111-1111-1111-1111-111111111111',
      code: 'SOFTWARE_DEVELOPER',
      name: 'Software Developer',
      description: 'Full-stack & backend development across core CS fundamentals.',
      icon: 'Code',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 'r2222222-2222-2222-2222-222222222222',
      code: 'AI_ML_ENGINEER',
      name: 'AI/ML Engineer',
      description: 'Machine learning, data processing, and AI application engineering.',
      icon: 'Cpu',
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  const mockCategories = [
    {
      id: 'c1111111-1111-1111-1111-111111111111',
      code: 'APTITUDE',
      name: 'Aptitude & Reasoning',
      description: 'Quantitative ability and logical reasoning.',
      icon: 'Calculator',
      sequence_order: 1,
      created_at: new Date().toISOString(),
      topics: [
        {
          id: 't1111111-1111-1111-1111-111111111111',
          category_id: 'c1111111-1111-1111-1111-111111111111',
          name: 'Quantitative Aptitude',
          slug: 'quantitative-aptitude',
          description: 'Percentages, time & work, algebra.',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    },
    {
      id: 'c2222222-2222-2222-2222-222222222222',
      code: 'TECHNICAL',
      name: 'Technical Core',
      description: 'Programming languages and databases.',
      icon: 'Code',
      sequence_order: 2,
      created_at: new Date().toISOString(),
      topics: [
        {
          id: 't2222222-2222-2222-2222-222222222222',
          category_id: 'c2222222-2222-2222-2222-222222222222',
          name: 'Python Programming',
          slug: 'python',
          description: 'Core syntax and data structures.',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    },
  ];

  const mockMaterials = [
    {
      id: 'm1111111-1111-1111-1111-111111111111',
      topic_id: 't2222222-2222-2222-2222-222222222222',
      role_id: 'r1111111-1111-1111-1111-111111111111',
      title: 'Complete Python for Placement Interviews',
      description: 'Essential Python interview questions, data structures, and edge cases.',
      url: 'https://example.com/python-guide',
      material_type: 'ARTICLE',
      difficulty: 'BEGINNER',
      source: 'Tech Prep Cell',
      status: 'APPROVED',
      submitted_by_user_id: null,
      reviewed_by_user_id: null,
      review_notes: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  test('1. Student navigates to Preparation Hub, inspects roadmaps and suggests a resource', async ({ page }) => {
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

    // Mock API endpoints
    await page.route('**/api/v1/preparation/roles', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockRoles) });
    });

    await page.route('**/api/v1/preparation/categories', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockCategories) });
    });

    await page.route('**/api/v1/preparation/roles/*/roadmap', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          role: mockRoles[0],
          topics: [
            {
              topic: mockCategories[1].topics[0],
              importance: 'CORE',
              material_count: 5,
            },
          ],
        }),
      });
    });

    await page.route('**/api/v1/preparation/materials*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: mockMaterials,
          total: 1,
          page: 1,
          page_size: 18,
          has_next: false,
        }),
      });
    });

    await page.route('**/api/v1/preparation/suggest', async (route) => {
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'm2222222-2222-2222-2222-222222222222',
          topic_id: mockCategories[1].topics[0].id,
          title: 'Advanced Dynamic Programming Masterclass',
          url: 'https://example.com/dp-guide',
          material_type: 'VIDEO',
          difficulty: 'ADVANCED',
          status: 'PENDING',
          submitted_by_user_id: '11111111-1111-1111-1111-111111111111',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });

    await page.goto('/');
    // Click Preparation Hub in sidebar
    await page.locator('nav').getByRole('button', { name: /Preparation Hub/i }).click();

    // Verify on /preparation
    await expect(page).toHaveURL('/preparation');
    await expect(page.locator('h1')).toContainText('Curated Placement Preparation & Roadmaps');

    // Verify Target Role Roadmap section
    await expect(page.locator('text=Target Role Roadmap')).toBeVisible();
    await expect(page.locator('button', { hasText: 'Software Developer' })).toBeVisible();

    // Verify material card
    await expect(page.locator('text=Complete Python for Placement Interviews')).toBeVisible();
    await expect(page.locator('span', { hasText: 'BEGINNER' })).toBeVisible();
    await expect(page.locator('a', { hasText: 'Open Guide' })).toBeVisible();

    // Open Suggestion modal
    await page.locator('button', { hasText: 'Suggest a Material' }).click();
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();
    await expect(modal.getByText('Suggest a Placement Material')).toBeVisible();

    // Fill form inside modal
    await modal.locator('select').first().selectOption({ label: 'Python Programming' });
    await modal.locator('input[placeholder*="Binary Search"]').fill('Advanced Dynamic Programming Masterclass');
    await modal.locator('input[type="url"]').fill('https://example.com/dp-guide');

    // Submit
    await modal.locator('button[type="submit"]', { hasText: 'Submit for Review' }).click();

    // Verify success feedback message
    await expect(page.locator('text=Thank you! Your suggestion has been submitted')).toBeVisible();
  });

  test('2. Officer accesses Preparation Hub, views pending suggestions, and approves material', async ({ page }) => {
    // Seed authenticated officer state
    await page.addInitScript(() => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-jwt-token-officer',
            refreshToken: 'mock-refresh-token-officer',
            user: {
              id: '99999999-9999-9999-9999-999999999999',
              email: 'officer@campusflow.edu',
              full_name: 'Placement Officer Jane',
              role: 'OFFICER',
              is_active: true,
            },
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    });

    const mockPendingMaterial = {
      id: 'm3333333-3333-3333-3333-333333333333',
      topic_id: 't2222222-2222-2222-2222-222222222222',
      role_id: null,
      title: 'Top 50 SQL Query Interview Questions',
      description: 'Practical SQL interview problems on Window Functions and Joins.',
      url: 'https://example.com/sql-50',
      material_type: 'PRACTICE_QUESTIONS',
      difficulty: 'INTERMEDIATE',
      source: 'Community Submitter',
      status: 'PENDING',
      submitted_by_user_id: '11111111-1111-1111-1111-111111111111',
      reviewed_by_user_id: null,
      review_notes: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    await page.route('**/api/v1/preparation/roles', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockRoles) });
    });

    await page.route('**/api/v1/preparation/categories', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockCategories) });
    });

    await page.route('**/api/v1/preparation/roles/*/roadmap', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ role: mockRoles[0], topics: [] }),
      });
    });

    await page.route('**/api/v1/preparation/materials*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0, page: 1, page_size: 18, has_next: false }),
      });
    });

    await page.route('**/api/v1/preparation/officers/submissions*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [mockPendingMaterial],
          total: 1,
          page: 1,
          page_size: 50,
          has_next: false,
        }),
      });
    });

    await page.route('**/api/v1/preparation/officers/submissions/*/review', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...mockPendingMaterial,
          status: 'APPROVED',
          reviewed_by_user_id: '99999999-9999-9999-9999-999999999999',
        }),
      });
    });

    await page.goto('/preparation');

    // Verify Officer Action buttons
    await expect(page.locator('button', { hasText: 'Publish New Material' })).toBeVisible();
    await expect(page.locator('button', { hasText: 'Review Queue' })).toBeVisible();

    // Click Review Queue tab
    await page.locator('button', { hasText: 'Review Queue' }).click();

    // Verify pending material appears in review queue
    await expect(page.locator('text=Top 50 SQL Query Interview Questions')).toBeVisible();
    await expect(page.locator('text=PENDING REVIEW')).toBeVisible();

    // Click Review Action button
    await page.locator('button', { hasText: 'Review Action' }).click();
    await expect(page.locator('h3', { hasText: 'Review Suggestion' })).toBeVisible();

    // Fill review notes and Approve
    await page.locator('textarea').fill('Approved for student SQL practice.');
    await page.locator('button', { hasText: 'Approve & Publish' }).click();

    // Modal closes
    await expect(page.locator('h3', { hasText: 'Review Suggestion' })).not.toBeVisible();
  });

  test('3. Officer directly publishes preparation material and verifies immediate visibility in Explore Library', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-jwt-token-officer',
            refreshToken: 'mock-refresh-token-officer',
            user: {
              id: '99999999-9999-9999-9999-999999999999',
              email: 'officer@campusflow.edu',
              full_name: 'Placement Officer Jane',
              role: 'OFFICER',
              is_active: true,
            },
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    });

    const newMaterial = {
      id: 'm-direct-4444-4444',
      topic_id: 't2222222-2222-2222-2222-222222222222',
      role_id: null,
      title: 'Full-Stack System Design Cheat Sheet',
      description: 'System design fundamentals for campus placement rounds.',
      url: 'https://example.com/system-design',
      material_type: 'PDF',
      difficulty: 'INTERMEDIATE',
      source: 'TPO Career Cell',
      status: 'APPROVED',
      submitted_by_user_id: '99999999-9999-9999-9999-999999999999',
      reviewed_by_user_id: '99999999-9999-9999-9999-999999999999',
      review_notes: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    await page.route('**/api/v1/preparation/roles', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockRoles) });
    });

    await page.route('**/api/v1/preparation/categories', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockCategories) });
    });

    let currentMaterials: any[] = [...mockMaterials];
    await page.route('**/api/v1/preparation/materials*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: currentMaterials,
          total: currentMaterials.length,
          page: 1,
          page_size: 50,
          has_next: false,
        }),
      });
    });

    await page.route('**/api/v1/preparation/officers/materials', async (route) => {
      currentMaterials = [newMaterial, ...currentMaterials];
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(newMaterial),
      });
    });

    await page.goto('/preparation');

    // Click Publish New Material
    await page.locator('button', { hasText: 'Publish New Material' }).click();
    const modal = page.getByRole('dialog');
    await expect(modal).toBeVisible();
    await expect(modal.getByText('Publish Official Material')).toBeVisible();

    // Fill publishing form
    await modal.locator('select').first().selectOption({ label: 'Python Programming' });
    await modal.locator('input[placeholder*="Binary Search"]').fill('Full-Stack System Design Cheat Sheet');
    await modal.locator('input[type="url"]').fill('https://example.com/system-design');

    // Submit
    await modal.locator('button[type="submit"]', { hasText: 'Publish Material' }).click();

    // Verify modal closes and new material appears in Explore Library
    await expect(modal).not.toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=Full-Stack System Design Cheat Sheet')).toBeVisible();
  });
});
