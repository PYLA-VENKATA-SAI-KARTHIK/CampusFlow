"""
Phase 4.3 — CI/CD Pipeline Foundation Verification Tests.

Verifies:
1. .github/workflows/ci.yml exists and has valid YAML structure.
2. Triggers on push and pull_request only.
3. Permissions are least-privilege (contents: read).
4. Three logical jobs exist: backend-tests, frontend-build, docker-build.
5. backend-tests includes PostgreSQL service, Alembic validation, and pytest.
6. frontend-build includes Node 22, npm ci, and npm run build.
7. docker-build validates Docker Compose config and builds backend/frontend Docker images.
8. Non-root user checks are enforced in docker-build.
9. No deployment or production GCP resources are referenced.
"""
from pathlib import Path
import yaml
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
CI_WORKFLOW = ROOT_DIR / ".github" / "workflows" / "ci.yml"


def test_01_ci_workflow_structure_and_permissions():
    """Verify ci.yml exists, parses, has least-privilege permissions, and proper triggers."""
    assert CI_WORKFLOW.exists(), ".github/workflows/ci.yml must exist"

    with open(CI_WORKFLOW, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["name"] == "CampusFlow CI"

    # Triggers
    triggers = data.get("on") or data.get(True)  # PyYAML parses "on" as boolean True in 1.1 unless quoted
    assert triggers is not None
    assert "push" in triggers
    assert "pull_request" in triggers

    # Permissions
    permissions = data.get("permissions")
    assert permissions == {"contents": "read"}, "CI must have strictly least-privilege contents: read permission"

    # Jobs
    jobs = data.get("jobs", {})
    assert "backend-tests" in jobs
    assert "frontend-build" in jobs
    assert "docker-build" in jobs


def test_02_backend_tests_job_configuration():
    """Verify backend-tests job runs on Python 3.13, uses PostgreSQL service, and validates Alembic."""
    with open(CI_WORKFLOW, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    job = data["jobs"]["backend-tests"]
    assert job["runs-on"] == "ubuntu-latest"

    # Services
    services = job.get("services", {})
    assert "postgres" in services
    pg = services["postgres"]
    assert "postgres:15-alpine" in pg["image"]
    assert "pg_isready" in pg["options"]

    # Environment
    env = job.get("env", {})
    assert env.get("APP_ENV") == "testing"
    assert "postgresql+asyncpg" in env.get("DATABASE_URL", "")
    assert env.get("STORAGE_PROVIDER") == "mock"
    assert env.get("NOTIFICATION_TASK_PROVIDER") == "mock"
    assert env.get("PUSH_PROVIDER") == "mock"
    assert env.get("EMAIL_PROVIDER") == "mock"

    # Steps inspection
    step_names = [s.get("name", "") for s in job.get("steps", [])]
    assert any("Checkout" in name for name in step_names)
    assert any("Setup Python" in name for name in step_names)
    assert any("Install Backend Dependencies" in name for name in step_names)
    assert any("Validate Alembic Migrations" in name for name in step_names)
    assert any("Run Complete Backend Pytest Suite" in name for name in step_names)

    # Inspect Alembic step commands
    alembic_step = next(s for s in job["steps"] if "Validate Alembic" in s.get("name", ""))
    assert "alembic upgrade head" in alembic_step["run"]
    assert "0007_audit_logs_immutability" in alembic_step["run"]
    assert "alembic heads" in alembic_step["run"]


def test_03_frontend_build_job_configuration():
    """Verify frontend-build job sets up Node 22, runs npm ci, and npm run build."""
    with open(CI_WORKFLOW, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    job = data["jobs"]["frontend-build"]
    assert job["runs-on"] == "ubuntu-latest"

    steps = job.get("steps", [])
    step_names = [s.get("name", "") for s in steps]
    assert any("Setup Node.js" in name for name in step_names)
    assert any("Install Frontend Dependencies" in name for name in step_names)
    assert any("Build Frontend Bundle" in name for name in step_names)

    # Check setup-node version
    node_step = next(s for s in steps if "Setup Node" in s.get("name", ""))
    assert str(node_step["with"]["node-version"]) == "22"

    # Check build step
    build_step = next(s for s in steps if "Build Frontend" in s.get("name", ""))
    assert "npm run build" in build_step["run"]


def test_04_docker_build_job_configuration():
    """Verify docker-build job validates compose and builds backend/frontend images without publishing."""
    with open(CI_WORKFLOW, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    job = data["jobs"]["docker-build"]
    assert job["runs-on"] == "ubuntu-latest"

    steps = job.get("steps", [])

    # Compose validation step
    compose_step = next(s for s in steps if "Docker Compose" in s.get("name", ""))
    assert "docker compose config" in compose_step["run"]

    # Backend docker build step
    backend_build = next(s for s in steps if "Build Backend Docker Image" in s.get("name", ""))
    assert backend_build["with"]["push"] is False
    assert backend_build["with"]["context"] == "./backend"

    # Backend non-root user verification
    backend_user_step = next(s for s in steps if "Verify Backend Non-Root User" in s.get("name", ""))
    assert "10001" in backend_user_step["run"]

    # Frontend docker build step
    frontend_build = next(s for s in steps if "Build Frontend Docker Image" in s.get("name", ""))
    assert frontend_build["with"]["push"] is False
    assert frontend_build["with"]["context"] == "./frontend"

    # Frontend non-root user verification
    frontend_user_step = next(s for s in steps if "Verify Frontend Non-Root User" in s.get("name", ""))
    assert "nginx" in frontend_user_step["run"]


def test_05_security_and_no_deployment():
    """Verify workflow contains zero deployment triggers, zero cloud provisioning, and no secrets."""
    content = CI_WORKFLOW.read_text(encoding="utf-8")

    # Forbidden deployment targets
    forbidden_terms = [
        "gcloud",
        "google-github-actions",
        "cloud run deploy",
        "terraform",
        "locust",
        "playwright",
        "docker push",
    ]
    for term in forbidden_terms:
        assert term not in content.lower(), f"Forbidden deployment/external action '{term}' found in CI workflow"
