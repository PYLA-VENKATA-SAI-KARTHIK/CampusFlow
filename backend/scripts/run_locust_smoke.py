#!/usr/bin/env python3
"""
CampusFlow — Headless Locust Runner for Lightweight Smoke Validation.

Executes Tier 1 (10 users, spawn rate 2) or Tier 2 (25 users, spawn rate 5)
in headless mode against a running local test instance.

Usage:
    python scripts/run_locust_smoke.py --tier 1 --host http://127.0.0.1:8000 --duration 15s
    python scripts/run_locust_smoke.py --tier 2 --host http://127.0.0.1:8000 --duration 30s
"""
import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

TIERS = {
    1: {"users": 10, "spawn_rate": 2, "duration": "15s"},
    2: {"users": 25, "spawn_rate": 5, "duration": "25s"},
    3: {"users": 50, "spawn_rate": 10, "duration": "30s"},
}


def _pregenerate_tokens() -> Path | None:
    """
    Directly creates valid JWT tokens for test accounts prior to launching Locust.
    This runs in pure Python (no gevent) and writes to backend/.locust_tokens.json.
    """
    import asyncio
    import json
    try:
        from app.core.config import get_settings
        from app.core.security import JWTManager
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy import select
        from app.models.user import User

        settings = get_settings()
        jwt_mgr = JWTManager(settings)

        async def _fetch():
            tokens = {}
            engine = create_async_engine(settings.database_url)
            async with AsyncSession(engine) as session:
                res = await session.execute(select(User))
                for u in res.scalars().all():
                    role_str = u.role.value if hasattr(u.role, "value") else str(u.role)
                    tok = jwt_mgr.create_access_token(user_id=str(u.id), role=role_str, email=u.email)
                    tokens[u.email] = tok
                    if role_str == "OFFICER":
                        tokens["officer"] = tok
                    elif role_str == "ADMIN":
                        tokens["admin"] = tok
            await engine.dispose()
            return tokens

        tokens = asyncio.run(_fetch())
        token_file = BASE_DIR / ".locust_tokens.json"
        token_file.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
        return token_file
    except Exception as exc:
        print(f"[WARN] Could not pre-generate tokens: {exc}")
        return None


def run_smoke(tier: int, host: str, duration: str | None = None) -> int:
    token_file = _pregenerate_tokens()
    config = TIERS.get(tier, TIERS[1])
    dur = duration or config["duration"]
    users = config["users"]
    spawn_rate = config["spawn_rate"]

    print(f"\n=======================================================")
    print(f" CampusFlow Locust Smoke Test — Tier {tier}")
    print(f" Users: {users} | Spawn Rate: {spawn_rate}/s | Duration: {dur}")
    print(f" Target Host: {host}")
    print(f"=======================================================\n")

    cmd = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(BASE_DIR / "locustfile.py"),
        "--headless",
        "-u",
        str(users),
        "-r",
        str(spawn_rate),
        "--run-time",
        dur,
        "--host",
        host,
        "--only-summary",
    ]

    try:
        result = subprocess.run(cmd, cwd=str(BASE_DIR))
        if result.returncode == 0:
            print(f"\n[OK] Tier {tier} Locust validation PASSED successfully.")
        else:
            print(f"\n[FAIL] Tier {tier} Locust validation completed with return code {result.returncode}.")
        return result.returncode
    finally:
        if token_file and token_file.exists():
            token_file.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Run lightweight local Locust load validation")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], default=1, help="Validation tier (1=10 users, 2=25 users, 3=50 users)")
    parser.add_argument("--host", type=str, default="http://127.0.0.1:8000", help="Base URL of target CampusFlow API")
    parser.add_argument("--duration", type=str, default=None, help="Custom duration string (e.g. 20s, 1m)")

    args = parser.parse_args()
    code = run_smoke(args.tier, args.host, args.duration)
    sys.exit(code)


if __name__ == "__main__":
    main()
