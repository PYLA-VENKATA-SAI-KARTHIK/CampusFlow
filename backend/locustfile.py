"""
CampusFlow — Locust Load & Performance Validation Suite.

Adheres strictly to Phase 4.4 constraints:
- Synthetic users and credentials only.
- Realistic weighted distributions:
  * StudentUser: 80% weight (browsing, eligibility, notifications, registration)
  * OfficerUser: 15% weight (drive monitoring, applicant review, analytics)
  * AdminUser: 5% weight (user management, audit logs, platform overview)
- Paced with realistic think-times (between 1s and 5s).
- Suitable for lightweight local validation tiers (10, 25, 50 concurrent users)
  on standard hardware (16 GB RAM).
"""
import random
import requests
from locust import HttpUser, between, events, task


STUDENT_CREDENTIALS = [
    ("student1@campusflow.edu", "TestStudent@123"),
    ("student2@campusflow.edu", "TestStudent@123"),
    ("student3@campusflow.edu", "TestStudent@123"),
    ("student4@campusflow.edu", "TestStudent@123"),
    ("student5@campusflow.edu", "TestStudent@123"),
]

OFFICER_CREDENTIALS = ("officer@campusflow.edu", "TestOfficer@123")
ADMIN_CREDENTIALS = ("admin@campusflow.edu", "TestAdmin@123")

TOKEN_CACHE: dict[str, str] = {}


def _load_pregenerated_tokens() -> dict[str, str]:
    """
    Reads pre-generated RS256 JWT tokens from .locust_tokens.json if present.
    This avoids Gevent/asyncpg event-loop conflicts and completely bypasses
    the 10/min login rate limiter for high-concurrency local load tests.
    """
    import json
    from pathlib import Path
    token_file = Path(__file__).resolve().parent / ".locust_tokens.json"
    if token_file.exists():
        try:
            return json.loads(token_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Pre-authenticates the unique synthetic accounts once before user swarm begins.
    First checks for pregenerated tokens, falling back to HTTP login.
    """
    pre_tokens = _load_pregenerated_tokens()
    if pre_tokens:
        TOKEN_CACHE.update(pre_tokens)
        return

    host = (environment.host or "http://127.0.0.1:8000").rstrip("/")
    for email, pwd in STUDENT_CREDENTIALS:
        try:
            r = requests.post(f"{host}/api/v1/auth/login", json={"email": email, "password": pwd}, timeout=10)
            if r.status_code == 200:
                TOKEN_CACHE[email] = r.json().get("access_token")
        except Exception:
            pass

    for role_key, creds in [("officer", OFFICER_CREDENTIALS), ("admin", ADMIN_CREDENTIALS)]:
        try:
            r = requests.post(f"{host}/api/v1/auth/login", json={"email": creds[0], "password": creds[1]}, timeout=10)
            if r.status_code == 200:
                TOKEN_CACHE[role_key] = r.json().get("access_token")
        except Exception:
            pass


class StudentUser(HttpUser):
    """
    Simulates student candidate traffic:
    Browsing placement drives, checking eligibility, reading notifications,
    registering for drives.
    """
    weight = 80
    wait_time = between(1.0, 3.0)

    def on_start(self):
        self.email, self.password = random.choice(STUDENT_CREDENTIALS)
        self.token = TOKEN_CACHE.get(self.email)
        self.headers = {}
        self.known_drive_ids = []
        self.known_notification_ids = []

        if not self.token:
            resp = self.client.post(
                "/api/v1/auth/login",
                json={"email": self.email, "password": self.password},
                name="/api/v1/auth/login [Student]",
            )
            if resp.status_code == 200:
                self.token = resp.json().get("access_token")
                TOKEN_CACHE[self.email] = self.token

        if self.token:
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

    @task(4)
    def view_profile(self):
        """Fetch student's own academic profile."""
        if not self.headers:
            return
        self.client.get(
            "/api/v1/students/me",
            headers=self.headers,
            name="/api/v1/students/me",
        )

    @task(5)
    def list_drives(self):
        """Browse published placement drives."""
        if not self.headers:
            return
        resp = self.client.get(
            "/api/v1/drives",
            headers=self.headers,
            name="/api/v1/drives [List]",
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            self.known_drive_ids = [d["id"] for d in items if "id" in d]

    @task(4)
    def view_drive_details(self):
        """View specific drive details."""
        if not self.headers or not self.known_drive_ids:
            return
        drive_id = random.choice(self.known_drive_ids)
        self.client.get(
            f"/api/v1/drives/{drive_id}",
            headers=self.headers,
            name="/api/v1/drives/[id]",
        )

    @task(3)
    def check_eligibility(self):
        """Check student eligibility for a drive."""
        if not self.headers or not self.known_drive_ids:
            return
        drive_id = random.choice(self.known_drive_ids)
        self.client.get(
            f"/api/v1/drives/{drive_id}/eligibility-check",
            headers=self.headers,
            name="/api/v1/drives/[id]/eligibility-check",
        )

    @task(3)
    def view_notifications(self):
        """Fetch in-app notifications."""
        if not self.headers:
            return
        resp = self.client.get(
            "/api/v1/notifications",
            headers=self.headers,
            name="/api/v1/notifications [List]",
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            self.known_notification_ids = [n["id"] for n in items if "id" in n]

    @task(1)
    def check_push_status(self):
        """Check web push subscription status."""
        if not self.headers:
            return
        self.client.get(
            "/api/v1/notifications/push-subscription/status",
            headers=self.headers,
            name="/api/v1/notifications/push-subscription/status",
        )

    @task(1)
    def mark_notifications_read(self):
        """Mark all notifications as read."""
        if not self.headers:
            return
        self.client.post(
            "/api/v1/notifications/read-all",
            headers=self.headers,
            name="/api/v1/notifications/read-all",
        )


class OfficerUser(HttpUser):
    """
    Simulates placement officer operations:
    Monitoring drives, inspecting applicant lists, viewing analytics.
    """
    weight = 15
    wait_time = between(2.0, 4.0)

    def on_start(self):
        self.token = TOKEN_CACHE.get("officer")
        self.headers = {}
        self.known_drive_ids = []

        if not self.token:
            resp = self.client.post(
                "/api/v1/auth/login",
                json={"email": OFFICER_CREDENTIALS[0], "password": OFFICER_CREDENTIALS[1]},
                name="/api/v1/auth/login [Officer]",
            )
            if resp.status_code == 200:
                self.token = resp.json().get("access_token")
                TOKEN_CACHE["officer"] = self.token

        if self.token:
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

    @task(4)
    def list_drives(self):
        """List drives including draft/active/completed."""
        if not self.headers:
            return
        resp = self.client.get(
            "/api/v1/drives",
            headers=self.headers,
            name="/api/v1/drives [Officer List]",
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            self.known_drive_ids = [d["id"] for d in items if "id" in d]

    @task(3)
    def view_applicants(self):
        """View student registrations for a drive."""
        if not self.headers or not self.known_drive_ids:
            return
        drive_id = random.choice(self.known_drive_ids)
        self.client.get(
            f"/api/v1/drives/{drive_id}/registrations",
            headers=self.headers,
            name="/api/v1/drives/[id]/registrations",
        )

    @task(2)
    def view_drive_analytics(self):
        """Query drive-specific placement statistics."""
        if not self.headers or not self.known_drive_ids:
            return
        drive_id = random.choice(self.known_drive_ids)
        self.client.get(
            f"/api/v1/drives/{drive_id}/analytics",
            headers=self.headers,
            name="/api/v1/drives/[id]/analytics",
        )

    @task(2)
    def view_overview_analytics(self):
        """View platform-wide placement metrics."""
        if not self.headers:
            return
        self.client.get(
            "/api/v1/analytics/overview",
            headers=self.headers,
            name="/api/v1/analytics/overview",
        )


class AdminUser(HttpUser):
    """
    Simulates administrator operations:
    Managing users, reviewing immutable audit logs, platform overview.
    """
    weight = 5
    wait_time = between(2.0, 5.0)

    def on_start(self):
        self.token = TOKEN_CACHE.get("admin")
        self.headers = {}

        if not self.token:
            resp = self.client.post(
                "/api/v1/auth/login",
                json={"email": ADMIN_CREDENTIALS[0], "password": ADMIN_CREDENTIALS[1]},
                name="/api/v1/auth/login [Admin]",
            )
            if resp.status_code == 200:
                self.token = resp.json().get("access_token")
                TOKEN_CACHE["admin"] = self.token

        if self.token:
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }

    @task(3)
    def list_users(self):
        """Admin list users."""
        if not self.headers:
            return
        self.client.get(
            "/api/v1/admin/users",
            headers=self.headers,
            name="/api/v1/admin/users",
        )

    @task(3)
    def list_audit_logs(self):
        """Admin query immutable audit logs."""
        if not self.headers:
            return
        self.client.get(
            "/api/v1/admin/audit-logs",
            headers=self.headers,
            name="/api/v1/admin/audit-logs",
        )

    @task(1)
    def view_overview_analytics(self):
        """Admin check platform analytics."""
        if not self.headers:
            return
        self.client.get(
            "/api/v1/analytics/overview",
            headers=self.headers,
            name="/api/v1/analytics/overview [Admin]",
        )
