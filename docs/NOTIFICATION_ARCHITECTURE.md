# CampusFlow — Notification Architecture

> **Version:** 2.0 | **Date:** 2026-08-27  
> Notifications are a core product feature, not an afterthought. The primary product problem is students missing placement opportunities. The notification system is how CampusFlow solves that.

---

## 1. Core Constraint

> **A single HTTP request must NEVER synchronously send notifications to thousands of students.**

Violating this constraint means:
- API responses time out under load
- A single push failure crashes the entire request
- Retries are impossible without re-running the whole operation
- The placement officer sees a slow or failed response

**All notification fan-out is asynchronous** via Cloud Tasks. The API enqueues tasks and returns immediately.

---

## 2. Notification Channels (Phase 1)

| Channel | Mechanism | Delivery Time | User Opt-in Required | Phase |
|---|---|---|---|---|
| **In-App** | DB record + client polling | ~30 seconds | No (always on) | 1 |
| **Browser Push** | Web Push Protocol (VAPID) | Near real-time | Yes | 1 |
| **Email** | SendGrid or similar | Minutes | Yes | 2 |
| **WhatsApp** | WhatsApp Business API | Near real-time | Yes | 3 |

**Design principle:** The notification system is **channel-agnostic** at the data model level. A notification record in the database is channel-neutral. The worker decides how to deliver it based on the user's active subscriptions. Adding a new channel (email, WhatsApp) means adding a new delivery strategy in the worker — no schema changes.

---

## 3. Notification Event Catalog

| Event Type | DB Constant | Trigger | Audience | Priority |
|---|---|---|---|---|
| New drive published | `DRIVE_PUBLISHED` | Officer: `DRAFT → PUBLISHED` | Eligible students | High |
| Deadline approaching 24h | `DEADLINE_REMINDER_24H` | Scheduler | Eligible + not registered | Medium |
| Deadline approaching 6h | `DEADLINE_REMINDER_6H` | Scheduler | Eligible + not registered | High |
| Deadline approaching 1h | `DEADLINE_REMINDER_1H` | Scheduler | Eligible + not registered | Critical |
| Registration confirmed | `REGISTRATION_CONFIRMED` | Student registers | That student only | Low |
| Shortlisted for stage | `SHORTLISTED` | Officer shortlists | Shortlisted students | High |
| Stage schedule updated | `STAGE_UPDATED` | Officer updates published stage | Shortlisted students | High |
| Results published | `RESULT_PUBLISHED` | Officer: publish-results | Assigned students | High |
| Manual broadcast | `MANUAL_BROADCAST` | Officer: /drives/:id/notify | Configurable audience | Medium |

---

## 4. Full Notification Pipeline Architecture

```mermaid
flowchart TD
    subgraph Triggers["Notification Triggers"]
        T1["Drive Published\nAPI call by Officer"]
        T2["Student Shortlisted\nAPI call by Officer"]
        T3["Stage Updated\nAPI call by Officer"]
        T4["Results Published\nAPI call by Officer"]
        T5["Manual Broadcast\nAPI call by Officer"]
        T6["Cloud Scheduler\nevery 30 minutes"]
        T7["Student Registers\nAPI call by Student"]
    end

    subgraph API["Backend API Service"]
        ND["NotificationDispatcher\n\nDetermines recipients\nEnqueues Cloud Tasks\nNever delivers directly"]
        DC["DeadlineChecker\n\nRuns on /internal/scheduler/check-deadlines\nFinds drives needing reminders\nEnqueues per-student tasks"]
    end

    subgraph Queue["Google Cloud Tasks\nQueue: campusflow-notifications"]
        Q1["Task: {user_id, type, reference_id}\nRetry: up to 5 attempts\nBackoff: 1s→2s→4s→8s→300s"]
    end

    subgraph Worker["Notification Worker\nCloud Run — internal only"]
        W1["OIDC Token Verification\n(reject if not Cloud Tasks SA)"]
        W2["Idempotency Check\n(was this notification already sent?)"]
        W3["Re-check business rules\n(still eligible? still not registered?)"]
        W4["Write to notifications table\n(in-app record)"]
        W5["Send Browser Push\n(VAPID, per active subscription)"]
        W6["Future: Send Email"]
        W7["Future: Send WhatsApp"]
    end

    subgraph DB["PostgreSQL"]
        NR[("notifications\ntable")]
        PS[("push_subscriptions\ntable")]
    end

    T1 --> ND
    T2 --> ND
    T3 --> ND
    T4 --> ND
    T5 --> ND
    T7 --> ND
    T6 --> DC
    DC --> Queue
    ND --> Queue

    Queue --> W1
    W1 --> W2
    W2 -->|"Already sent"| SKIP["Return 200\n(idempotent skip)"]
    W2 -->|"Not sent yet"| W3
    W3 -->|"Rule no longer applies"| SKIP
    W3 -->|"Still applies"| W4
    W4 --> NR
    W4 --> W5
    W5 --> PS
    W5 --> PUSH["Browser Push API\nFCM / Mozilla Push"]
```

---

## 5. Asynchronous Fan-out Design

### 5.1 Why One Task Per Student

**Alternative considered:** One task per drive → worker fetches all eligible students → sends all pushes

**Problem with batch approach:**
- If worker crashes midway, there is no way to know which students were notified
- Retry would re-notify already-notified students
- No per-student retry granularity

**Chosen approach:** One Cloud Task per student notification
- Each task is independently retryable
- Failure of one student's notification doesn't affect others
- Idempotency check in the worker prevents double-sends on retry

### 5.2 Fan-out at Scale

For a drive with 2,000 eligible students, the API enqueues 2,000 Cloud Tasks.

Cloud Tasks dispatches at `500 tasks/sec max`. All 2,000 tasks will be dispatched within ~4 seconds to the worker pool. With 20 worker instances running in parallel, all notifications will be delivered within 1-2 minutes of the drive being published.

```
Drive published → 2,000 tasks enqueued in ~400ms (Cloud Tasks write is fast)
API returns to officer: 200 OK in < 500ms total

Cloud Tasks dispatches:
500 tasks/sec → 2,000 students notified in ~4 seconds of task processing
```

---

## 6. Cloud Tasks Configuration

### 6.1 Queue Settings

```yaml
Queue: campusflow-notifications
Location: asia-south1

Rate limits:
  maxDispatchesPerSecond: 500
  maxConcurrentDispatches: 100

Retry config:
  maxAttempts: 5
  minBackoff: 1s
  maxBackoff: 300s
  maxDoublings: 4          # 1s → 2s → 4s → 8s → 300s
  maxRetryDuration: 3600s  # Give up after 1 hour

Routing:
  target: campusflow-worker Cloud Run
  httpMethod: POST
  path: /internal/tasks/send-notification
  oidcToken:
    serviceAccountEmail: campusflow-tasks-sa@project.iam.gserviceaccount.com
```

### 6.2 Task Payload Schema

```json
{
  "notification_id": null,
  "user_id": "uuid",
  "notification_type": "DRIVE_PUBLISHED",
  "title": "New Placement Drive: Acme Corp",
  "body": "Acme Corp is hiring for SDE Intern 2025. Check your eligibility.",
  "reference_id": "drive-uuid",
  "reference_type": "DRIVE",
  "send_push": true,
  "idempotency_key": "DRIVE_PUBLISHED:drive-uuid:user-uuid"
}
```

**`idempotency_key`:** A stable string combining notification type + reference ID + user ID. Used by the worker to detect and skip duplicate tasks.

---

## 7. Deadline Reminder System

### 7.1 Architecture

```mermaid
sequenceDiagram
    participant CS as Cloud Scheduler
    participant API as Backend API
    participant DB as PostgreSQL
    participant CT as Cloud Tasks
    participant WKR as Worker

    note over CS: Runs every 30 minutes

    CS->>API: POST /internal/scheduler/check-deadlines\n[OIDC token: scheduler SA]
    API->>API: Verify OIDC token

    API->>DB: SELECT drives WHERE status = REGISTRATION_OPEN\nAND registration_deadline IS NOT NULL

    loop For each open drive
        API->>API: delta = registration_deadline - NOW()

        alt 23h50m ≤ delta ≤ 24h10m
            note over API: 24-hour window (20-min grace for scheduler imprecision)
            API->>DB: SELECT eligible students NOT registered\nAND no DEADLINE_REMINDER_24H notification exists
            API->>CT: Enqueue {type: DEADLINE_REMINDER_24H} per student
        else 5h50m ≤ delta ≤ 6h10m
            API->>CT: Enqueue {type: DEADLINE_REMINDER_6H} per student
        else 50m ≤ delta ≤ 1h10m
            API->>CT: Enqueue {type: DEADLINE_REMINDER_1H} per student
        end
    end

    API-->>CS: 200 OK {drives_checked, tasks_enqueued}

    note over CT,WKR: Worker re-checks before sending

    CT->>WKR: POST /internal/tasks/send-notification\n{type: DEADLINE_REMINDER_1H, user_id, drive_id}
    WKR->>DB: SELECT registration WHERE drive_id=? AND user_id=?
    alt Student registered since task was enqueued
        WKR-->>CT: 200 OK {status: skipped, reason: already_registered}
    else Still not registered
        WKR->>DB: INSERT notification record
        WKR->>WKR: Send push notification
        WKR-->>CT: 200 OK {status: sent}
    end
```

### 7.2 Reminder Deduplication Strategy

**Problem:** Cloud Scheduler fires every 30 minutes. A drive with deadline at T+5h will be in the 6H window for 20 minutes (two scheduler runs). Without deduplication, the student gets two 6H reminders.

**Solution — Two-layer deduplication:**

**Layer 1: Pre-enqueue check (SQL)**
```sql
-- Only enqueue if no notification of this type exists for this user+drive:
SELECT id FROM notifications
WHERE user_id = :user_id
  AND notification_type = :reminder_type     -- e.g., 'DEADLINE_REMINDER_6H'
  AND reference_id = :drive_id
  AND reference_type = 'DRIVE'
LIMIT 1;
-- If row found: skip enqueue
```

**Layer 2: Worker-side idempotency (defense in depth)**
```python
# Worker checks idempotency_key before writing notification:
existing = await repo.get_notification_by_idempotency_key(task.idempotency_key)
if existing:
    return {"status": "skipped", "reason": "idempotent_duplicate"}
```

**Layer 3: Registration re-check (cancellation)**
```python
# Worker re-checks registration even if task was enqueued when student was unregistered:
registration = await repo.get_registration(user_id=task.user_id, drive_id=task.reference_id)
if registration and registration.status == "REGISTERED":
    return {"status": "skipped", "reason": "already_registered"}
```

### 7.3 Registration → Reminder Stop Mechanism

```mermaid
flowchart TD
    A["Student successfully registers"] --> B["Service layer:\nINSERT drive_registrations"]
    B --> C["Enqueue Cloud Task:\ntype=CANCEL_REMINDERS\n{drive_id, user_id}"]
    C --> D["Worker receives CANCEL_REMINDERS task"]
    D --> E["No active task cancellation in Cloud Tasks\n(no task ID tracking needed)"]
    E --> F["Instead: Worker checks registration status\nbefore EVERY reminder send"]
    F --> G{"Is student\nregistered?"}
    G -->|Yes| H["Return 200 OK\nstatus=skipped\nreason=already_registered\n\nTask consumed — no retry\nNo notification sent"]
    G -->|No| I["Send reminder"]
```

**Why not cancel Cloud Tasks tasks?** Cloud Tasks doesn't provide an efficient way to cancel tasks by business criteria. The simpler, more reliable approach is: always re-check at delivery time. If the student is registered, the worker silently skips. This is more robust than task cancellation and handles race conditions naturally.

---

## 8. In-App Notification System

### 8.1 Storage & Persistence

Every notification is written to the `notifications` table **before** any push attempt. This guarantees:
- The student always has an in-app notification history
- If push delivery fails, the student can still see the notification in-app
- Push delivery status (`push_sent`, `push_sent_at`) is tracked separately from notification existence

### 8.2 Client Retrieval (Phase 1: Polling)

```
React component mounts (or user opens notification bell)
        │
        ▼
TanStack Query: GET /api/v1/notifications?is_read=false&page_size=20
        │ (refetch interval: 30 seconds while tab is active)
        ▼
Backend returns: {items, unread_count}
        │
        ▼
Zustand: update unread_count (drives badge on bell icon)
        │
        ▼
Render notification dropdown
```

**Phase 2 upgrade path:** Replace polling with Server-Sent Events (SSE) or WebSocket for real-time delivery. FastAPI supports both natively. The switch requires no schema changes.

### 8.3 Unread Count Management

```
unread_count = SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = FALSE

Updates on:
├── POST /notifications/{id}/read → decrement by 1
├── POST /notifications/mark-all-read → set to 0
└── Background push received → increment by 1 (via Service Worker → broadcast to React)
```

---

## 9. Browser Push Notification Architecture

### 9.1 VAPID Key Management

```
VAPID Private Key → stored in Google Secret Manager (campusflow/vapid-private-key)
VAPID Public Key  → stored in Google Secret Manager + served via GET /notifications/vapid-public-key

Key generation: openssl ecparam -genkey -name prime256v1 -noout | openssl pkcs8 -topk8 -nocrypt
```

### 9.2 Push Subscription Flow

```mermaid
sequenceDiagram
    actor S as Student
    participant FE as React SPA
    participant SW as Service Worker
    participant Browser as Browser Push Manager
    participant BE as Backend API
    participant DB as PostgreSQL

    S->>FE: First login or prompt trigger
    FE->>Browser: Notification.requestPermission()
    Browser->>S: Show permission dialog
    alt Permission granted
        FE->>BE: GET /notifications/vapid-public-key
        BE-->>FE: {vapid_public_key}
        FE->>SW: Register Service Worker (sw.js)
        SW->>Browser: pushManager.subscribe({userVisibleOnly: true, applicationServerKey: vapid_public_key})
        Browser-->>SW: PushSubscription {endpoint, keys: {p256dh, auth}}
        SW-->>FE: subscription object
        FE->>BE: POST /notifications/push-subscription {endpoint, p256dh_key, auth_key}
        BE->>DB: INSERT push_subscriptions (upsert by endpoint)
        BE-->>FE: 201 Created
    else Permission denied
        FE->>FE: Graceful degradation: in-app only mode
    end
```

### 9.3 Push Delivery & Error Handling

```python
# Worker: push delivery with full error handling
async def send_push_notification(subscription: PushSubscription, payload: dict):
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh_key,
                    "auth": subscription.auth_key
                }
            },
            data=json.dumps({
                "title": payload["title"],
                "body": payload["body"],
                "icon": "/icon-192.png",
                "badge": "/badge-72.png",
                "data": {
                    "url": f"/drives/{payload['reference_id']}",
                    "notification_id": payload["notification_id"]
                }
            }),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": "mailto:admin@campusflow.college"}
        )
        await repo.mark_push_sent(subscription.id, notification_id)

    except WebPushException as e:
        if e.response.status_code == 410:
            # Subscription expired — browser unsubscribed or cleared
            await repo.deactivate_subscription(subscription.id)
            # Do NOT retry — 410 is permanent
        elif e.response.status_code == 429:
            # Rate limited by push service — Cloud Tasks will retry
            raise  # Let Cloud Tasks retry with backoff
        else:
            logger.error(f"Push failed: {e}")
            raise  # Let Cloud Tasks retry
```

### 9.4 Service Worker Behavior

```javascript
// sw.js — Service Worker
self.addEventListener('push', event => {
  const data = event.data.json();
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/icon-192.png',
      badge: '/badge-72.png',
      data: data.data,
      requireInteraction: data.data.priority === 'CRITICAL'
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
    // Deep links to the relevant drive/stage page
  );
});
```

---

## 10. Manual Broadcast Flow

When a placement officer sends a manual notification:

```mermaid
sequenceDiagram
    actor O as Placement Officer
    participant API as Backend API
    participant DB as PostgreSQL
    participant CT as Cloud Tasks

    O->>API: POST /drives/{id}/notify\n{audience: "REGISTERED", title, body}
    API->>API: Verify role = OFFICER | ADMIN
    API->>DB: SELECT student_user_ids based on audience:\n- ELIGIBLE: run eligibility engine for all students\n- REGISTERED: SELECT from drive_registrations\n- SHORTLISTED: SELECT from stage_assignments

    loop For each recipient (up to thousands)
        API->>CT: Enqueue {type: MANUAL_BROADCAST, user_id, title, body}
    end

    API->>DB: INSERT audit_log\naction=MANUAL_NOTIFICATION_SENT\nrecipient_count=N

    API-->>O: 202 Accepted\n{message: "Notification enqueued for 243 students"}
```

**Audience options:**
- `ELIGIBLE` — all students who pass the eligibility engine for this drive
- `REGISTERED` — all students who have registered for this drive
- `SHORTLISTED` — all students shortlisted in the most recent active stage

---

## 11. Future Channel Extension

The worker architecture is designed to add channels with no schema changes:

```
Worker receives task
        │
        ▼
Write in-app notification record (always)
        │
        ├── if user has push_subscriptions → send Web Push
        ├── if user.email_notifications_enabled → (Phase 2) send Email via SendGrid
        └── if user.whatsapp_number AND whatsapp_enabled → (Phase 3) send via WA Business API
```

Adding email in Phase 2 requires:
1. Add `email_notifications_enabled` column to `users` (or a separate `notification_preferences` table)
2. Add email-sending code to the worker
3. No notification schema changes
4. No task queue changes
5. No API changes
