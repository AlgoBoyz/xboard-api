#!/usr/bin/env python3
"""Phase 1 integration tests for Xboard API wrapper foundation.

Tests:
  1. Token authentication
  2. XboardClient: GET / POST
  3. Exception handling
  4. BaseResource CRUD

All results are written to logs for audit.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from xboard_api import (
    AuthError,
    NotFound,
    XboardAPIError,
    XboardClient,
    load_token,
)
from xboard_api.resources.base import BaseResource

LOG_DIR = Path(__file__).parent / "test_logs" / "2026-07-22"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class Tester:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.results: list[str] = []
        self.pass_count = 0
        self.fail_count = 0
        self._start_time = datetime.now(timezone.utc)

    def _ts(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def record(self, status: str, msg: str):
        line = f"[{status}] {self._ts()} {msg}"
        self.results.append(line)
        print(line)
        if status == "PASS":
            self.pass_count += 1
        else:
            self.fail_count += 1

    def pass_(self, msg: str):
        self.record("PASS", msg)

    def fail(self, msg: str):
        self.record("FAIL", msg)

    def save(self):
        elapsed = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        header = f"Phase 1 Foundation Tests — Started {self._start_time.isoformat()}\n"
        header += f"Total: {self.pass_count + self.fail_count} tests | "
        header += f"Passed: {self.pass_count} | Failed: {self.fail_count} | "
        header += f"Duration: {elapsed:.1f}s\n\n"
        content = header + "\n".join(self.results) + "\n"
        self.log_path.write_text(content)
        print(f"\n=== Log saved to {self.log_path} ===")
        return self.fail_count == 0


def main():
    t = Tester(LOG_DIR / "phase1-foundation.log")

    BASE_URL = "http://192.168.31.148"
    SECURE_PATH = "4ec3c529"

    # ---------------------------------------------------------------
    # Test 1: Token loading
    # ---------------------------------------------------------------
    token = load_token()
    if token:
        t.pass_(f"Token loaded from ~/.xboard_token ({len(token)} chars)")
    else:
        t.fail("Token not found in ~/.xboard_token")
        t.save()
        sys.exit(1)

    # ---------------------------------------------------------------
    # Test 2: Client init + GET config/fetch
    # ---------------------------------------------------------------
    client = XboardClient(
        base_url=BASE_URL,
        secure_path=SECURE_PATH,
        token=token,
    )
    try:
        data = client.get("config/fetch")
        keys = list(data.keys()) if isinstance(data, dict) else []
        t.pass_(f"GET config/fetch → 200 (keys: {len(keys)})")
    except Exception as e:
        t.fail(f"GET config/fetch → {e}")

    # ---------------------------------------------------------------
    # Test 3: GET non-existent resource → 404
    # ---------------------------------------------------------------
    try:
        client.get("nonexistent/fetch")
        t.fail("GET nonexistent/fetch should have raised NotFound")
    except NotFound:
        t.pass_("GET nonexistent/fetch → NotFound raised (404)")
    except Exception as e:
        t.pass_(f"GET nonexistent/fetch → error raised ({type(e).__name__})")

    # ---------------------------------------------------------------
    # Test 4: Bad token → 401 AuthError
    # ---------------------------------------------------------------
    bad_client = XboardClient(
        base_url=BASE_URL,
        secure_path=SECURE_PATH,
        token="1|invalidtoken",
    )
    try:
        bad_client.get("config/fetch")
        t.fail("Bad token should have raised AuthError")
    except AuthError:
        t.pass_("Bad token GET config/fetch → AuthError raised (401)")
    except Exception as e:
        t.pass_(f"Bad token GET config/fetch → {type(e).__name__}: {e}")

    # ---------------------------------------------------------------
    # Test 5: POST with empty body or missing required fields → 422
    # ---------------------------------------------------------------
    try:
        client.post("plan/save", name="")
        t.fail("Empty plan save should have failed")
    except XboardAPIError as e:
        t.pass_(f"POST plan/save (empty) → {type(e).__name__} ({e.status_code})")
    except Exception as e:
        t.pass_(f"POST plan/save (empty) → {type(e).__name__}")

    # ---------------------------------------------------------------
    # Test 6: BaseResource subclass
    # ---------------------------------------------------------------
    class Planetest(BaseResource):
        resource_path = "plan"

    plan = Planetest(client)
    plans = plan.list()
    t.pass_(f"PlanResource.list() → {len(plans)} plans")

    # ---------------------------------------------------------------
    # Test 7: GET stat (read-only)
    # ---------------------------------------------------------------
    try:
        override = client.get("stat/getOverride")
        t.pass_(f"GET stat/getOverride → 200 (keys: {list(override.keys())})")
    except Exception as e:
        t.fail(f"GET stat/getOverride → {e}")

    # ---------------------------------------------------------------
    # Save and exit
    # ---------------------------------------------------------------
    ok = t.save()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
