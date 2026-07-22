#!/usr/bin/env python3
"""Phase 2 integration tests — API write + DB verify via sshpass.

Every test:
  1. Calls API to create/modify
  2. Queries DB via sshpass to verify
  3. Cleans up

Key finding: Most save endpoints return data:true, not the created object.
We query DB by unique name to find the created ID.
"""

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
    ServerNodeResource,
    ServerRouteResource,
)
from xboard_api.resources.user import UserResource
from xboard_api.resources.order import OrderResource

BASE_URL = "http://192.168.31.148"
SECURE_PATH = "4ec3c529"
SSH_CMD = [
    "sshpass", "-p", "wfxc_qsc", "ssh",
    "-o", "StrictHostKeyChecking=no",
    "-o", "PubkeyAuthentication=no",
    "pomni@192.168.31.148",
]

LOG_DIR = Path(__file__).parent / "test_logs" / "2026-07-22"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class Tester:
    def __init__(self, name):
        self.name = name
        self.results: list[str] = []
        self.pass_count = 0
        self.fail_count = 0

    def ts(self):
        return datetime.now(timezone.utc).strftime("%H:%M:%S")

    def record(self, status, msg):
        line = f"[{status}] {self.ts()} [{self.name}] {msg}"
        self.results.append(line)
        print(line)
        if status == "PASS":
            self.pass_count += 1
        else:
            self.fail_count += 1

    def ok(self, msg):
        self.record("PASS", msg)

    def bad(self, msg):
        self.record("FAIL", msg)


def db(sql: str) -> str:
    """Run SQLite query on test machine, return stdout."""
    full = SSH_CMD + [f"cd /var/www/xboard && sqlite3 database/database.sqlite '{sql}'"]
    r = subprocess.run(full, capture_output=True, text=True, timeout=15)
    return r.stdout.strip()


def db_val(sql: str) -> str:
    """Convenience: single value query."""
    return db(sql)


def db_count(table: str, where: str = "") -> int:
    q = f"SELECT COUNT(*) FROM {table}"
    if where:
        q += f" WHERE {where}"
    v = db_val(q)
    try:
        return int(v)
    except ValueError:
        return -1


def db_row(table: str, where: str) -> str:
    return db_val(f"SELECT * FROM {table} WHERE {where} LIMIT 1")


# ============================================================
# Tests
# ============================================================

def test_config(client, t: Tester):
    api = ConfigResource(client)

    # Save
    new_name = "XboardDBVerify"
    r = api.save(app_name=new_name)
    if r is True or (isinstance(r, dict) and r.get("status") == "success"):
        t.ok(f"Config.save → success")
    else:
        t.bad(f"Config.save unexpected: {r}")
        return

    # DB verify
    val = db_val("SELECT value FROM v2_settings WHERE name='app_name'")
    if val == new_name:
        t.ok(f"DB app_name = {val}")
    else:
        t.bad(f"DB mismatch: expected '{new_name}', got '{val}'")

    # Restore
    api.save(app_name="Xboard")
    val2 = db_val("SELECT value FROM v2_settings WHERE name='app_name'")
    if val2 == "Xboard":
        t.ok("Config restored to Xboard")
    else:
        t.bad(f"Restore failed: {val2}")


def test_plan(client, t: Tester):
    api = PlanResource(client)
    uniq = datetime.now().strftime("%H%M%S")
    name = f"TEST-PLAN-{uniq}"
    before = db_count("v2_plan")

    r = api.save(name=name, transfer_enable=200, content="db verify test")
    if r is True or (isinstance(r, dict) and r.get("status") == "success"):
        t.ok(f"Plan.save → success")
    else:
        t.bad(f"Plan.save unexpected: {r}")
        return

    row = db_val(f"SELECT id, name, transfer_enable, content FROM v2_plan WHERE name='{name}'")
    if row:
        parts = row.split("|")
        pid = parts[0]
        if parts[1] == name and parts[2] == "200" and "db verify test" in row:
            t.ok(f"DB plan: id={pid}, transfer_enable=200, content OK")
        else:
            t.bad(f"DB mismatch: {row}")

        api.drop(id=int(pid))
        after = db_count("v2_plan")
        if after == before:
            t.ok(f"Plan dropped, count restored ({before})")
        else:
            t.bad(f"Drop count: before={before} after={after}")
    else:
        t.bad(f"Plan not found in DB: {name}")


def test_machine(client, t: Tester):
    api = ServerMachineResource(client)
    uniq = datetime.now().strftime("%H%M%S")
    name = f"TEST-MACH-{uniq}"
    before = db_count("v2_server_machine")

    r = api.save(name=name, notes="db verify")
    # Machine save returns {id, token, install_command}
    mid = None
    if isinstance(r, dict):
        mid = r.get("id")
        token = r.get("token", "")[:8]
        t.ok(f"Machine.save → id={mid}, token={token}...")
    else:
        t.bad(f"Machine.save unexpected: {r}")
        return

    row = db_val(f"SELECT name, notes FROM v2_server_machine WHERE id={mid}")
    if name in row and "db verify" in row:
        t.ok(f"DB machine: {row}")
    else:
        t.bad(f"DB mismatch machine: {row}")

    api.drop(id=mid)
    after = db_count("v2_server_machine")
    if after == before:
        t.ok(f"Machine dropped, count restored ({before})")
    else:
        t.bad(f"Drop count: before={before} after={after}")


def test_server_group(client, t: Tester):
    api = ServerGroupResource(client)
    uniq = datetime.now().strftime("%H%M%S")
    name = f"TEST-GRP-{uniq}"
    before = db_count("v2_server_group")

    r = api.save(name=name)
    if r is True or (isinstance(r, dict) and r.get("status") == "success"):
        t.ok("Group.save → success")
    else:
        t.bad(f"Group.save unexpected: {r}")
        return

    row = db_val(f"SELECT id, name FROM v2_server_group WHERE name='{name}'")
    if row:
        gid = row.split("|")[0]
        t.ok(f"DB group: id={gid}")
        api.drop(id=int(gid))
        after = db_count("v2_server_group")
        if after == before:
            t.ok(f"Group dropped, count restored ({before})")
        else:
            t.bad(f"Drop count: before={before} after={after}")
    else:
        t.bad(f"Group not found in DB: {name}")


def test_user(client, t: Tester):
    api = UserResource(client)

    # Read admin
    info = api.get_by_id(id=1)
    if isinstance(info, dict):
        email = info.get("email", "")
        t.ok(f"User.getById(1) → {email}")
    else:
        t.bad(f"User.getById unexpected: {info}")
        return

    # Generate test user
    before = db_count("v2_user")
    r = api.generate(email_suffix="dbverify.local", email_prefix="testuser", generate_count=1)
    users = []
    if isinstance(r, list):
        users = r
    elif isinstance(r, dict):
        users = r.get("data", [])
        if not isinstance(users, list):
            users = []

    if users:
        uemail = users[0].get("email")
        t.ok(f"User.generate → email={uemail}")

        # DB verify — get id from DB since generate() doesn't return it
        row = db_val(f"SELECT id, email FROM v2_user WHERE email='{uemail}'")
        if uemail in row:
            uid = int(row.split("|")[0])
            t.ok(f"DB user: id={uid}, email={uemail}")

            # Cleanup
            api.destroy(id=uid)
            after = db_count("v2_user")
            if after == before:
                t.ok(f"User destroyed, count restored ({before})")
            else:
                t.bad(f"Destroy count: before={before} after={after}")
        else:
            t.bad(f"DB mismatch user: expected {uemail}")
    else:
        t.bad(f"User.generate no users returned: {r}")


def test_order(client, t: Tester):
    api = OrderResource(client)
    plan_api = PlanResource(client)
    user_api = UserResource(client)
    uniq = datetime.now().strftime("%H%M%S")

    # Create temp plan
    pname = f"TEST-ORD-PLAN-{uniq}"
    plan_api.save(name=pname, transfer_enable=50)
    prow = db_val(f"SELECT id FROM v2_plan WHERE name='{pname}'")
    pid = int(prow) if prow else 0
    if not pid:
        t.bad("Temp plan creation failed")
        return

    # Create temp user
    user_api.generate(email_suffix="orddb.local", email_prefix=f"orduser{uniq}", generate_count=1)
    urow = db_val(f"SELECT id, email FROM v2_user WHERE email LIKE '%orddb.local' ORDER BY id DESC LIMIT 1")
    if not urow:
        t.bad("Temp user creation failed")
        plan_api.drop(id=pid)
        return
    uid, uemail = urow.split("|", 1)

    before = db_count("v2_order")

    r = api.assign(plan_id=pid, email=uemail, period="monthly", total_amount=88)
    # Order.assign might return order data or just success
    if isinstance(r, (bool,)) and r:
        t.ok("Order.assign → success")
    elif isinstance(r, dict):
        oid = r.get("id", r.get("data", {}).get("id"))
        t.ok(f"Order.assign → id={oid}")
    else:
        t.bad(f"Order.assign unexpected: {r}")
        user_api.destroy(id=int(uid))
        plan_api.drop(id=pid)
        return

    # DB verify
    orow = db_val(f"SELECT id, plan_id, total_amount, status FROM v2_order WHERE plan_id={pid} AND total_amount=88")
    if orow:
        oid = orow.split("|")[0]
        if str(pid) in orow and "88" in orow:
            t.ok(f"DB order: id={oid}, plan={pid}, amount=88")
        else:
            t.bad(f"DB mismatch order: {orow}")

        # Cancel
        api.cancel(oid)
        status = db_val(f"SELECT status FROM v2_order WHERE id={oid}")
        t.ok(f"Order.cancel → status={status}")
    else:
        t.bad(f"Order not found in DB: plan={pid}, amount=88")

    # Cleanup
    user_api.destroy(id=int(uid))
    plan_api.drop(id=pid)


def main():
    token = load_token()
    if not token:
        print("FATAL: No token")
        sys.exit(1)

    client = XboardClient(base_url=BASE_URL, secure_path=SECURE_PATH, token=token)
    log_path = LOG_DIR / "phase2-core.log"
    all_results: list[str] = []
    total_pass = 0
    total_fail = 0
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
        all_results.extend(t.results)
        total_pass += t.pass_count
        total_fail += t.fail_count

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    header = f"Phase 2 Core Tests — {start.isoformat()}\n"
    header += f"Total: {total_pass + total_fail} | Pass: {total_pass} | Fail: {total_fail} | {elapsed:.1f}s\n\n"
    log_path.write_text(header + "\n".join(all_results) + "\n")
    print(f"\n=== Log: {log_path} ===")
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
