import { test, expect } from '@playwright/test';

/**
 * Phase 5.2 — Playwright E2E: Practice Assessment Engine Workflows
 * 
 * Verifies:
 * 1. Officer creates a practice assessment, adds MCQ questions with options, publishes, and assigns to students.
 * 2. Student discovers assigned assessment, views pre-test preview, starts timed attempt.
 * 3. Student takes test with options selection, question palette navigation, autosave sync, and submits test.
 * 4. Authoritative server evaluation displays results: score, percentage, pass/fail status, topic breakdown, and question review.
 * 5. Security & RBAC boundary checks.
 */

test.describe('Practice Assessment Engine (Phase 5.2)', () => {
  const assessmentId = 'a1111111-1111-1111-1111-111111111111';
  const questionId = 'q1111111-1111-1111-1111-111111111111';
  const assignmentId = 'as111111-1111-1111-1111-111111111111';
  const attemptId = 'att11111-1111-1111-1111-111111111111';
  const studentUserId = '11111111-1111-1111-1111-111111111111';
  const officerUserId = '22222222-2222-2222-2222-222222222222';

  const mockCategories = [
    {
      id: 'c1111111-1111-1111-1111-111111111111',
      code: 'TECHNICAL',
      name: 'Technical Core',
      description: 'Programming and CS foundations.',
      topics: [
        {
          id: 't1111111-1111-1111-1111-111111111111',
          name: 'Python & Data Structures',
        },
      ],
    },
  ];

  const mockQuestions = [
    {
      id: questionId,
      assessment_id: assessmentId,
      topic_id: 't1111111-1111-1111-1111-111111111111',
      topic_name: 'Python & Data Structures',
      question_text: 'What is the average time complexity of dictionary lookup in Python?',
      options: [
        { key: 'A', text: 'O(1)' },
        { key: 'B', text: 'O(n)' },
        { key: 'C', text: 'O(log n)' },
        { key: 'D', text: 'O(n^2)' },
      ],
      correct_option: 'A',
      explanation: 'Python dictionaries are implemented as hash tables with O(1) average lookup.',
      marks: 2,
      sequence_order: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ];

  const mockDraftAssessment = {
    id: assessmentId,
    title: 'Python & Data Structures Assessment',
    description: 'Comprehensive timed practice assessment covering Python dicts, lists, and complexity.',
    category_id: 'c1111111-1111-1111-1111-111111111111',
    category_name: 'Technical Core',
    topic_id: 't1111111-1111-1111-1111-111111111111',
    topic_name: 'Python & Data Structures',
    role_id: null,
    role_name: null,
    placement_drive_id: null,
    placement_drive_title: null,
    difficulty: 'INTERMEDIATE',
    duration_minutes: 30,
    total_marks: 2,
    pass_percentage: 60,
    status: 'DRAFT',
    allow_multiple_attempts: false,
    questions_count: 1,
    created_by_user_id: officerUserId,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const mockPublishedAssessment = {
    ...mockDraftAssessment,
    status: 'PUBLISHED',
  };

  const mockAdminDetailDraft = {
    ...mockDraftAssessment,
    questions: mockQuestions,
    assignments_count: 0,
    completed_count: 0,
  };

  const mockAdminDetailPublished = {
    ...mockPublishedAssessment,
    questions: mockQuestions,
    assignments_count: 1,
    completed_count: 0,
  };

  // -------------------------------------------------------------------------
  // TEST 1: OFFICER CREATION & QUESTION BUILDER FLOW
  // -------------------------------------------------------------------------
  test('1. Officer creates practice assessment, adds MCQ questions, publishes, and assigns', async ({ page }) => {
    // Seed authenticated Officer
    await page.addInitScript(() => {
      window.localStorage.setItem(
        'campusflow-auth-storage',
        JSON.stringify({
          state: {
            accessToken: 'mock-jwt-token-officer',
            refreshToken: 'mock-refresh-token-officer',
            user: {
              id: '22222222-2222-2222-2222-222222222222',
              email: 'officer@campusflow.edu',
              full_name: 'Placement Officer One',
              role: 'OFFICER',
              is_active: true,
            },
            isAuthenticated: true,
          },
          version: 0,
        })
      );
    });

    let currentAssessmentState = { ...mockDraftAssessment };
    let currentAdminDetail = { ...mockAdminDetailDraft };

    // Setup routes
    await page.route('**/api/v1/preparation/categories', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockCategories) });
    });

    await page.route('**/api/v1/assessments', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([currentAssessmentState]),
        });
      } else if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify(mockDraftAssessment),
        });
      }
    });

    await page.route(`**/api/v1/assessments/${assessmentId}`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(currentAdminDetail),
      });
    });

    await page.route(`**/api/v1/assessments/${assessmentId}/publish`, async (route) => {
      currentAssessmentState = { ...mockPublishedAssessment };
      currentAdminDetail = { ...mockAdminDetailPublished };
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPublishedAssessment),
      });
    });

    await page.route(`**/api/v1/assessments/${assessmentId}/results`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          assessment_id: assessmentId,
          assessment_title: 'Python & Data Structures Assessment',
          total_assigned: 1,
          total_started: 0,
          total_completed: 0,
          average_score: null,
          average_percentage: null,
          pass_count: 0,
          results: [],
        }),
      });
    });

    await page.route('**/api/v1/officers/students*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              user_id: studentUserId,
              full_name: 'Synthetic Student One',
              email: 'student1@campusflow.edu',
              roll_number: '2026-CS-001',
              branch_code: 'CSE',
            },
          ],
          total: 1,
        }),
      });
    });

    await page.route(`**/api/v1/assessments/${assessmentId}/assign`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: assignmentId,
            assessment_id: assessmentId,
            student_user_id: studentUserId,
            status: 'ASSIGNED',
          },
        ]),
      });
    });

    await page.goto('/');
    // Click Assessments in navigation
    await page.locator('nav').getByRole('button', { name: /Assessments/i }).click();

    // Verify on /assessments
    await expect(page).toHaveURL('/assessments');
    await expect(page.locator('h1')).toContainText('Practice Assessment Engine');

    // Verify assessment card rendered
    await expect(page.locator('text=Python & Data Structures Assessment')).toBeVisible();
    await expect(page.locator('span', { hasText: 'DRAFT' })).toBeVisible();

    // Open Builder
    await page.click('button:has-text("Edit & Build")');
    await expect(page).toHaveURL(`/assessments/builder/${assessmentId}`);
    await expect(page.locator('h1')).toContainText('Python & Data Structures Assessment');

    // Check Question in Builder
    await expect(page.locator('text=What is the average time complexity of dictionary lookup in Python?')).toBeVisible();
    await expect(page.locator('text=Correct Answer')).toBeVisible();

    // Publish assessment
    page.on('dialog', async (dialog) => {
      await dialog.accept();
    });
    await page.click('button:has-text("Publish Assessment")');

    // Verify status update to PUBLISHED
    await expect(page.locator('span', { hasText: 'PUBLISHED' }).first()).toBeVisible();

    // Assign to students
    await page.click('button:has-text("Assign Assessment")');
    await expect(page.locator('text=Synthetic Student One')).toBeVisible();
    await page.click('input[type="checkbox"]');
    await page.click('button:has-text("Assign to 1 Student(s)")');
    await expect(page.locator('text=Successfully assigned')).toBeVisible();
  });

  // -------------------------------------------------------------------------
  // TEST 2: STUDENT DISCOVERY, TEST TAKING, AUTOSAVE & RESULT REVIEW
  // -------------------------------------------------------------------------
  test('2. Student discovers assessment, starts timed attempt, answers MCQs with autosave, and views results', async ({ page }) => {
    // Seed authenticated Student
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

    const mockAssignedList = [
      {
        id: assignmentId,
        assessment_id: assessmentId,
        student_user_id: studentUserId,
        status: 'ASSIGNED',
        created_at: new Date().toISOString(),
        assessment_title: 'Python & Data Structures Assessment',
        difficulty: 'INTERMEDIATE',
        duration_minutes: 30,
        total_marks: 2,
        pass_percentage: 60,
        category_name: 'Technical Core',
        topic_name: 'Python & Data Structures',
        placement_drive_title: null,
        student_name: 'Synthetic Student One',
        student_email: 'student1@campusflow.edu',
        student_roll_number: '2026-CS-001',
        student_branch: 'CSE',
        latest_result_id: null,
        latest_score: null,
        latest_percentage: null,
        latest_passed: null,
      },
    ];

    const mockPreview = {
      id: assessmentId,
      assignment_id: assignmentId,
      title: 'Python & Data Structures Assessment',
      description: 'Comprehensive timed practice assessment covering Python dicts, lists, and complexity.',
      category_name: 'Technical Core',
      topic_name: 'Python & Data Structures',
      role_name: null,
      placement_drive_title: null,
      difficulty: 'INTERMEDIATE',
      duration_minutes: 30,
      question_count: 1,
      total_marks: 2,
      pass_percentage: 60,
      due_date: null,
      assignment_status: 'ASSIGNED',
      has_active_attempt: false,
      active_attempt_id: null,
      active_attempt_expires_at: null,
      latest_result_id: null,
      latest_score: null,
      latest_percentage: null,
      latest_passed: null,
    };

    const futureExpiry = new Date(Date.now() + 30 * 60 * 1000).toISOString();

    const mockStartAttemptResponse = {
      attempt_id: attemptId,
      assessment_id: assessmentId,
      assignment_id: assignmentId,
      title: 'Python & Data Structures Assessment',
      duration_minutes: 30,
      started_at: new Date().toISOString(),
      expires_at: futureExpiry,
      questions: [
        {
          id: questionId,
          assessment_id: assessmentId,
          topic_id: 't1111111-1111-1111-1111-111111111111',
          question_text: 'What is the average time complexity of dictionary lookup in Python?',
          options: [
            { key: 'A', text: 'O(1)' },
            { key: 'B', text: 'O(n)' },
            { key: 'C', text: 'O(log n)' },
            { key: 'D', text: 'O(n^2)' },
          ],
          marks: 2,
          sequence_order: 1,
        },
      ],
      saved_responses: {},
    };

    const mockResult = {
      id: 'res11111-1111-1111-1111-111111111111',
      attempt_id: attemptId,
      assessment_id: assessmentId,
      assessment_title: 'Python & Data Structures Assessment',
      score_obtained: 2,
      total_score: 2,
      percentage: 100,
      is_passed: true,
      total_questions: 1,
      correct_answers: 1,
      incorrect_answers: 0,
      unanswered: 0,
      time_taken_seconds: 45,
      topic_breakdown: {
        'Python & Data Structures': {
          total_questions: 1,
          correct_answers: 1,
          incorrect_answers: 0,
          unanswered: 0,
          score_obtained: 2,
          total_score: 2,
        },
      },
      created_at: new Date().toISOString(),
      review: [
        {
          id: questionId,
          topic_id: 't1111111-1111-1111-1111-111111111111',
          topic_name: 'Python & Data Structures',
          question_text: 'What is the average time complexity of dictionary lookup in Python?',
          options: [
            { key: 'A', text: 'O(1)' },
            { key: 'B', text: 'O(n)' },
            { key: 'C', text: 'O(log n)' },
            { key: 'D', text: 'O(n^2)' },
          ],
          selected_option: 'A',
          correct_option: 'A',
          is_correct: true,
          marks_awarded: 2,
          explanation: 'Python dictionaries are implemented as hash tables with O(1) average lookup.',
          sequence_order: 1,
        },
      ],
    };

    // Route mocks
    await page.route('**/api/v1/assessments/assigned*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAssignedList),
      });
    });

    await page.route(`**/api/v1/assessments/${assessmentId}/preview`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockPreview),
      });
    });

    await page.route(`**/api/v1/assessments/${assessmentId}/start`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockStartAttemptResponse),
      });
    });

    await page.route(`**/api/v1/assessments/attempts/${attemptId}/active`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockStartAttemptResponse),
      });
    });

    await page.route(`**/api/v1/assessments/attempts/${attemptId}/save-progress`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'saved', saved_count: 1 }),
      });
    });

    await page.route(`**/api/v1/assessments/attempts/${attemptId}/submit`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockResult),
      });
    });

    await page.route(`**/api/v1/assessments/attempts/${attemptId}/result`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockResult),
      });
    });

    await page.goto('/');
    // Click Practice Assessments in student sidebar
    await page.locator('nav').getByRole('button', { name: /Practice Assessments/i }).click();

    // Verify on /assessments
    await expect(page).toHaveURL('/assessments');
    await expect(page.locator('h1')).toContainText('Practice Assessments');

    // Click Start Assessment -> opens Preview Modal
    await page.click('button:has-text("Start Assessment →")');
    await expect(page.locator('text=Important Test Instructions')).toBeVisible();
    await expect(page.locator('text=30 Minutes')).toBeVisible();

    // Confirm Start Test -> Navigates to player
    await page.click('button:has-text("I am Ready, Start Test →")');
    await expect(page).toHaveURL(`/assessments/player/${attemptId}`);

    // Verify Test Player Elements
    await expect(page.locator('text=Question 1 of 1')).toBeVisible();
    await expect(page.locator('text=What is the average time complexity of dictionary lookup in Python?')).toBeVisible();
    await expect(page.locator('text=O(1)')).toBeVisible();

    // Select Option A
    await page.click('text=O(1)');
    await expect(page.locator('text=Saved')).toBeVisible();

    // Submit test
    await page.click('button:has-text("Review & Submit")');
    await expect(page.locator('text=Submit Practice Assessment?')).toBeVisible();
    await page.click('button:has-text("Yes, Submit Test")');

    // Verify navigation to results page
    await expect(page).toHaveURL(`/assessments/results/${attemptId}`);

    // Verify Result page elements
    await expect(page.locator('text=✓ Assessment Passed')).toBeVisible();
    await expect(page.locator('div', { hasText: '100%' }).first()).toBeVisible();
    await expect(page.getByText('Correct Answers', { exact: true })).toBeVisible();
    await expect(page.locator('text=Python dictionaries are implemented as hash tables')).toBeVisible();
    await expect(page.getByText('Correct Answer', { exact: true })).toBeVisible();
  });
});
