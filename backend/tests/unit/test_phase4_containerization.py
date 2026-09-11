"""
Phase 4.2 — Containerization & Docker Infrastructure Verification Tests.

Verifies:
1. Backend Dockerfile multi-stage structure, non-root user, healthcheck, and no secrets.
2. Frontend Dockerfile multi-stage structure, non-root nginx user, healthcheck.
3. Frontend nginx.conf SPA routing, asset caching, security headers, and reverse proxy.
4. Root docker-compose.yml service topology, healthchecks, dependencies, and networks.
5. Mock providers local functionality (MockStorage, MockCloudTasks, MockPush).
"""
from pathlib import Path
from uuid import uuid4
import yaml
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


def test_01_backend_dockerfile_structure():
    """Verify backend/Dockerfile follows best practices, non-root user, and healthcheck."""
    dockerfile_path = BACKEND_DIR / "Dockerfile"
    assert dockerfile_path.exists(), "backend/Dockerfile must exist"

    content = dockerfile_path.read_text(encoding="utf-8")

    # Multi-stage build
    assert "AS builder" in content
    assert "AS runner" in content

    # Non-root user
    assert "useradd -u 10001 -g campusflow" in content
    assert "USER campusflow:campusflow" in content

    # Health check
    assert "HEALTHCHECK" in content
    assert "http://localhost:8000/api/v1/health" in content

    # Port and Entrypoint
    assert "EXPOSE 8000" in content
    assert 'ENTRYPOINT ["/app/entrypoint.sh"]' in content
    assert 'CMD ["uvicorn", "app.main:app"' in content

    # No hardcoded secrets or .env copy
    assert "COPY .env" not in content
    assert "ADD .env" not in content


def test_02_frontend_dockerfile_structure():
    """Verify frontend/Dockerfile follows multi-stage build, unprivileged user, and healthcheck."""
    dockerfile_path = FRONTEND_DIR / "Dockerfile"
    assert dockerfile_path.exists(), "frontend/Dockerfile must exist"

    content = dockerfile_path.read_text(encoding="utf-8")

    # Multi-stage build
    assert "AS build" in content
    assert "AS runner" in content
    assert "FROM node:" in content
    assert "FROM nginx:" in content

    # Non-root user
    assert "USER nginx" in content

    # Unprivileged port
    assert "EXPOSE 8080" in content

    # Health check
    assert "HEALTHCHECK" in content
    assert "http://localhost:8080/nginx-health" in content

    # No .env copy
    assert "COPY .env" not in content


def test_03_frontend_nginx_conf():
    """Verify frontend/nginx.conf includes SPA fallback, asset caching, reverse proxy, and headers."""
    nginx_conf_path = FRONTEND_DIR / "nginx.conf"
    assert nginx_conf_path.exists(), "frontend/nginx.conf must exist"

    content = nginx_conf_path.read_text(encoding="utf-8")

    # Unprivileged port
    assert "listen 8080;" in content

    # SPA routing fallback
    assert "try_files $uri $uri/ /index.html;" in content

    # Reverse proxy for /api/
    assert "location /api/ {" in content
    assert "proxy_pass http://backend:8000/api/;" in content

    # Cache immutable static assets
    assert "location /assets/ {" in content
    assert "immutable" in content

    # Security headers
    assert 'add_header X-Content-Type-Options "nosniff"' in content
    assert 'add_header X-Frame-Options "DENY"' in content
    assert 'add_header Referrer-Policy "strict-origin-when-cross-origin"' in content


def test_04_docker_compose_configuration():
    """Verify root docker-compose.yml configuration, services, healthchecks, and dependency graph."""
    compose_path = ROOT_DIR / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist"

    with open(compose_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    services = config.get("services", {})
    assert "postgres" in services
    assert "backend" in services
    assert "frontend" in services

    # PostgreSQL healthcheck
    pg = services["postgres"]
    assert "healthcheck" in pg
    assert "pg_isready" in " ".join(pg["healthcheck"]["test"])

    # Backend depends on healthy postgres
    backend = services["backend"]
    assert "depends_on" in backend
    assert backend["depends_on"]["postgres"]["condition"] == "service_healthy"
    assert "healthcheck" in backend
    assert "curl" in " ".join(backend["healthcheck"]["test"])

    # Frontend depends on healthy backend
    frontend = services["frontend"]
    assert "depends_on" in frontend
    assert frontend["depends_on"]["backend"]["condition"] == "service_healthy"
    assert "healthcheck" in frontend
    assert "wget" in " ".join(frontend["healthcheck"]["test"])

    # Ports exposed
    assert "8000:8000" in backend["ports"]
    assert "3000:8080" in frontend["ports"]

    # Volumes and networks
    assert "postgres_data" in config.get("volumes", {})
    assert "campusflow-network" in config.get("networks", {})


def test_05_dockerignore_files():
    """Verify backend and frontend .dockerignore files prevent leaking .env, venvs, and node_modules."""
    backend_ignore = BACKEND_DIR / ".dockerignore"
    frontend_ignore = FRONTEND_DIR / ".dockerignore"

    assert backend_ignore.exists()
    assert frontend_ignore.exists()

    b_content = backend_ignore.read_text(encoding="utf-8")
    assert ".env*" in b_content
    assert "venv" in b_content

    f_content = frontend_ignore.read_text(encoding="utf-8")
    assert "node_modules" in f_content
    assert "dist" in f_content
    assert ".env*" in f_content


@pytest.mark.asyncio
async def test_06_local_mock_providers_connectivity():
    """Verify local mock providers (Storage, CloudTasks, Push, Email) function without GCP."""
    from app.core.config import Settings
    from app.services.storage_service import create_storage_service, MockStorageService
    from app.services.cloud_tasks_service import create_cloud_tasks_service, MockCloudTasksService

    # 1. Mock Storage
    storage = create_storage_service(provider="mock", bucket_name="test-bkt")
    assert isinstance(storage, MockStorageService)
    up_url = await storage.generate_upload_url("resumes/test.pdf", "application/pdf", 1024, 900)
    assert "sig=mockPUT" in up_url

    # 2. Mock Cloud Tasks
    tasks = create_cloud_tasks_service(provider="mock")
    assert isinstance(tasks, MockCloudTasksService)
    task_id = await tasks.enqueue_notification_task({"type": "DRIVE_PUBLISHED", "payload": {}})
    assert "mock-task" in task_id or "projects/" in task_id

    # 3. Mock Push Sender
    from app.services.push_sender_service import get_push_sender_service, MockPushSenderService
    from app.models.push_subscription import PushSubscription

    push = get_push_sender_service()
    assert isinstance(push, MockPushSenderService)
    sub = PushSubscription(
        user_id=uuid4(),
        endpoint="https://fcm.googleapis.com/fcm/send/test",
        p256dh_key="test-key",
        auth_key="test-auth",
        is_active=True,
    )
    res = await push.send_notification(
        subscription=sub,
        payload={"title": "Test", "body": "Hello"},
    )
    assert res.status == "success"
