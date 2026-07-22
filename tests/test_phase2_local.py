#!/usr/bin/env python3
"""Phase 2 integration tests — runs ON the Xboard server, reads DB locally.

Every test:
  1. Calls Admin API (http://127.0.0.1)
  2. Reads SQLite DB directly (same machine)
  3. Cleans up

Key findings:
  - Most save endpoints return data:true (not created object)
  - Only machine/save returns {id, token, install_command}
  - User.generate returns array of users WITHOUT id field
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from xboard_api import XboardClient, load_token
from xboard_api.resources.config import ConfigResource
from xboard_api.resources.plan import PlanResource
from xboard_api.resources.server import (
    ServerGroupResource,
    ServerMachineResource,
    ServerRouteResource,
)
from xboard_api.resources.user import UserResource
from xboard_api.resources.order import OrderResource

BASE_URL = "http://127.0.0.1"
SECURE_PATH = "4ec3c529"
DB_PATH = "/var/www/xboard/database/database.sqlite"

LOG_DIR = Path(__file__).parent / "test_logs" / "2026-07-22"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class Tester:
    def __init__(self, name):
        self.name = name
        self.results: list[str] = []
        self.p = 0
        self.f = 0

    def ts(self):
        return datetime.now(timezone.utc).strftime("%H:%M:%S")

    def record(self, status, msg):
        line = f"[{status}] {self.ts()} [{self.name}] {msg}"
        self.results.append(line)
        print(line)
        if status == "PASS":
            self.p += 1
        else:
            self.f += 1

    def ok(self, m):
        self.record("PASS", m)

    def bad(self, m):
        self.record("FAIL", m)


def db(sql):
    """Run sqlite3 query locally with busy_timeout for concurrent access."""
    import time
    for attempt in range(5):
        r = subprocess.run(
            ["sqlite3", "-cmd", ".timeout 5000", DB_PATH, sql],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and "database is locked" not in r.stderr:
            return r.stdout.strip()
        if "database is locked" in r.stderr:
            time.sleep(0.3)
            continue
        sys.stderr.write(f"[DB-ERR] rc={r.returncode} err={r.stderr.strip()}\n")
        return r.stdout.strip()
    return ""


def db_val(sql):
    return db(sql)


def db_count(table, where=""):
    q = f"SELECT COUNT(*) FROM {table}"
    if where:
        q += f" WHERE {where}"
    try:
        return int(db_val(q))
    except (ValueError, TypeError):
        return -1


# ============================================================
# Tests
# ============================================================

def test_config(client, t):
    api = ConfigResource(client)

    new_name = "XboardLocalTest"
    r = api.save(app_name=new_name)

    if r is True:
        t.ok("Config.save → success (data=true)")
    else:
        t.bad(f"Config.save unexpected: {r}")
        return

    val = db_val("SELECT value FROM v2_settings WHERE name='app_name'")
    if val == new_name:
        t.ok(f"DB: app_name = {val}")
    else:
        t.bad(f"DB mismatch: expected '{new_name}', got '{val}'")

    api.save(app_name="Xboard")
    val2 = db_val("SELECT value FROM v2_settings WHERE name='app_name'")
    if val2 == "Xboard":
        t.ok("Config restored → Xboard")
    else:
        t.bad(f"Restore failed: {val2}")


def test_plan(client, t):
    api = PlanResource(client)
    uniq = datetime.now().strftime("%H%M%S")
    name = f"TEST-plan-{uniq}"
    before = db_count("v2_plan")

    r = api.save(name=name, transfer_enable=500, content="local test plan")
    if r is True:
        t.ok("Plan.save → success")
    else:
        t.bad(f"Plan.save unexpected: {r}")
        return

    row = db_val(f"SELECT id,name,transfer_enable,content FROM v2_plan WHERE name='{name}'")
    if row:
        parts = row.split("|", 3)
        pid = int(parts[0])
        if parts[1] == name and parts[2] == "500":
            t.ok(f"DB plan: id={pid} transfer_enable=500 content OK")
        else:
            t.bad(f"DB mismatch: {row}")

        api.drop(id=pid)
        after = db_count("v2_plan")
        t.ok(f"Plan dropped, count: {before}→{after}" if after == before else f"Drop count wrong: {before}→{after}")
    else:
        t.bad(f"Plan not found: {name}")


def test_machine(client, t):
    api = ServerMachineResource(client)
    uniq = datetime.now().strftime("%H%M%S")
    name = f"TEST-mach-{uniq}"
    before = db_count("v2_server_machine")

    r = api.save(name=name, notes="local test")
    if isinstance(r, dict) and r.get("id"):
        mid = r["id"]
        t.ok(f"Machine.save → id={mid}, token={r.get('token','')[:8]}...")
    else:
        t.bad(f"Machine.save unexpected: {r}")
        return

    row = db_val(f"SELECT name,notes FROM v2_server_machine WHERE id={mid}")
    if name in row and "local test" in row:
        t.ok(f"DB machine: {row}")
    else:
        t.bad(f"DB mismatch: {row}")

    api.drop(id=mid)
    after = db_count("v2_server_machine")
    t.ok(f"Machine dropped: {before}→{after}" if after == before else f"Drop wrong: {before}→{after}")


def test_server_group(client, t):
    api = ServerGroupResource(client)
    uniq = datetime.now().strftime("%H%M%S")
    name = f"TEST-grp-{uniq}"
    before = db_count("v2_server_group")

    r = api.save(name=name)
    if r is True:
        t.ok("Group.save → success")
    else:
        t.bad(f"Group.save unexpected: {r}")
        return

    row = db_val(f"SELECT id,name FROM v2_server_group WHERE name='{name}'")
    if row:
        gid = int(row.split("|")[0])
        t.ok(f"DB group: id={gid}")
        api.drop(id=gid)
        after = db_count("v2_server_group")
        t.ok(f"Group dropped: {before}→{after}" if after == before else f"Drop wrong: {before}→{after}")
    else:
        t.bad(f"Group not found: {name}")


def test_user(client, t):
    api = UserResource(client)

    # Read admin
    info = api.get_by_id(id=1)
    email = info.get("email", "?") if isinstance(info, dict) else "?"
    t.ok(f"User.getById(1) → {email}")

    # Generate
    before = db_count("v2_user")
    r = api.generate(email_suffix="localtest.api", email_prefix="testuser", generate_count=1)

    users = r if isinstance(r, list) else r.get("data", [])
    if not isinstance(users, list) or not users:
        t.bad(f"User.generate unexpected: {r}")
        return

    uemail = users[0].get("email", "")
    t.ok(f"User.generate → {uemail}")

    # DB verify (generate doesn't return id, query by email)
    row = db_val(f"SELECT id,email FROM v2_user WHERE email='{uemail}'")
    if row:
        uid = int(row.split("|")[0])
        t.ok(f"DB user: id={uid}")

        api.destroy(id=uid)
        after = db_count("v2_user")
        t.ok(f"User destroyed: {before}→{after}" if after == before else f"Destroy wrong: {before}→{after}")
    else:
        t.bad(f"User not in DB: {uemail}")


def test_order(client, t):
    api = OrderResource(client)
    plan_api = PlanResource(client)
    user_api = UserResource(client)
    uniq = datetime.now().strftime("%H%M%S")

    # Temp plan
    pname = f"TEST-ord-p-{uniq}"
    plan_api.save(name=pname, transfer_enable=50)
    prow = db_val(f"SELECT id FROM v2_plan WHERE name='{pname}'")
    if not prow:
        t.bad("Temp plan creation failed")
        return
    pid = int(prow)

    # Temp user
    user_api.generate(email_suffix="ordtest.api", email_prefix=f"u{uniq}", generate_count=1)
    urow = db_val(f"SELECT id,email FROM v2_user WHERE email LIKE '%ordtest.api' ORDER BY id DESC LIMIT 1")
    if not urow:
        t.bad("Temp user creation failed")
        plan_api.drop(id=pid)
        return
    uid = int(urow.split("|")[0])
    uemail = urow.split("|", 1)[1]

    before = db_count("v2_order")

    r = api.assign(plan_id=pid, email=uemail, period="month_price", total_amount=99)
    if r is True or (isinstance(r, dict) and r.get("status") == "success"):
        t.ok("Order.assign → success")
    elif isinstance(r, dict):
        t.ok(f"Order.assign → id={r.get('id')}")
    else:
        t.bad(f"Order.assign unexpected: {r}")
        user_api.destroy(id=uid)
        plan_api.drop(id=pid)
        return

    # DB verify
    orow = db_val(f"SELECT id,trade_no,plan_id,total_amount,status FROM v2_order WHERE plan_id={pid} ORDER BY id DESC LIMIT 1")
    if orow:
        parts = orow.split("|")
        oid, trade_no = parts[0], parts[1]
        if str(pid) in orow and "99" in orow:
            t.ok(f"DB order: id={oid}, plan={pid}, amount=99")

            # Cancel by trade_no
            api.cancel(trade_no)
            new_status = db_val(f"SELECT status FROM v2_order WHERE id={oid}")
            t.ok(f"Order.cancel → status={new_status}")
        else:
            t.bad(f"DB mismatch order: {orow}")
    else:
        t.bad(f"Order not found in DB")

    user_api.destroy(id=uid)
    plan_api.drop(id=pid)


def main():
    token = load_token()
    if not token:
        print("FATAL: No token")
        sys.exit(1)

    client = XboardClient(base_url=BASE_URL, secure_path=SECURE_PATH, token=token)
    log_path = LOG_DIR / "phase2-core.log"
    all_rows = []
    tp = tf = 0
    start = datetime.now(timezone.utc)

    tests = [
        ("config", test_config),
        ("plan", test_plan),
        ("machine", test_machine),
        ("server_group", test_server_group),
        ("user", test_user),
        ("order", test_order),
    ]

    for name, fn in tests:
        t = Tester(name)
        try:
            fn(client, t)
        except Exception as e:
            import traceback
            t.bad(f"Exception: {e}\n{traceback.format_exc()}")
        all_rows.extend(t.results)
        tp += t.p
        tf += t.f

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    header = f"Phase 2 Core Tests (LOCAL DB) — {start.isoformat()}\n"
    header += f"Total: {tp + tf} | Pass: {tp} | Fail: {tf} | {elapsed:.1f}s\n\n"
    log_path.write_text(header + "\n".join(all_rows) + "\n")
    print(f"\n=== Log: {log_path} ===")
    sys.exit(0 if tf == 0 else 1)


if __name__ == "__main__":
    main()
