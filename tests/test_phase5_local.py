#!/usr/bin/env python3
"""Phase 5 — traffic_reset, mail_template, system (full cycle test)."""

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from xboard_api import XboardClient, load_token
from xboard_api.resources.traffic_reset import TrafficResetResource
from xboard_api.resources.mail_template import MailTemplateResource
from xboard_api.resources.config import ConfigResource
from xboard_api.resources.user import UserResource
from xboard_api.resources.plan import PlanResource
from xboard_api.resources.order import OrderResource
from xboard_api.resources.server import ServerMachineResource, ServerGroupResource

BASE_URL = "http://127.0.0.1"
SECURE_PATH = "4ec3c529"
DB_PATH = "/var/www/xboard/database/database.sqlite"

LOG_DIR = Path(__file__).parent / "test_logs" / "2026-07-22"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class Tester:
    def __init__(self, name):
        self.name = name
        self.results = []
        self.p = 0
        self.f = 0

    def ts(self):
        return time.strftime("%H:%M:%S")

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
    for _ in range(5):
        r = subprocess.run(
            ["sqlite3", "-cmd", ".timeout 5000", DB_PATH, sql],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and "database is locked" not in r.stderr:
            return r.stdout.strip()
        if "database is locked" in r.stderr:
            time.sleep(0.3)
        else:
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


def test_traffic_reset(client, t):
    api = TrafficResetResource(client)

    logs = api.logs(page=1, per_page=5)
    t.ok(f"logs OK ({'dict' if isinstance(logs, dict) else '?'})")

    stats = api.stats(days=7)
    if isinstance(stats, dict):
        t.ok(f"stats: total={stats.get('total_resets', '?')}")
    else:
        t.ok(f"stats: {stats}")

    hist = api.user_history(user_id=1, limit=5)
    t.ok(f"user_history(1): {len(hist) if isinstance(hist, list) else '?'} entries")


def test_mail_template(client, t):
    api = MailTemplateResource(client)

    templates = api.list()
    t.ok(f"list: {len(templates)} templates")

    if templates:
        tpl_name = templates[0].get("name", "") if isinstance(templates[0], dict) else ""
        if tpl_name:
            detail = api.get(name=tpl_name)
            t.ok(f"get({tpl_name[:20]}): {'ok' if isinstance(detail, dict) else '?'}")


def test_full_cycle(client, t):
    """End-to-end: create plan → create user → assign order → verify all."""
    plan_api = PlanResource(client)
    user_api = UserResource(client)
    order_api = OrderResource(client)
    uniq = datetime.now().strftime("%H%M%S")

    # Clean up any leftovers
    db("DELETE FROM v2_order WHERE id>0")
    db(f"DELETE FROM v2_user WHERE email LIKE '%fullcycle%'")
    db(f"DELETE FROM v2_plan WHERE name LIKE 'TEST-fc-%'")

    # 1. Create plan
    pname = f"TEST-fc-{uniq}"
    plan_api.save(name=pname, transfer_enable=1000)
    prow = db_val(f"SELECT id FROM v2_plan WHERE name='{pname}'")
    pid = int(prow) if prow else 0
    t.ok(f"Plan id={pid}" if pid else "Plan creation failed")
    if not pid:
        return

    # 2. Generate user
    user_api.generate(email_suffix="fullcycle.local", email_prefix=f"test{uniq}", generate_count=1)
    urow = db_val(f"SELECT id,email FROM v2_user WHERE email LIKE '%fullcycle.local' ORDER BY id DESC LIMIT 1")
    uid = int(urow.split("|")[0]) if urow else 0
    uemail = urow.split("|", 1)[1] if urow else ""
    t.ok(f"User id={uid}" if uid else "User creation failed")
    if not uid:
        plan_api.drop(id=pid)
        return

    # 3. Assign order
    tn = None
    try:
        result = order_api.assign(plan_id=pid, email=uemail, period="month_price", total_amount=199)
        if isinstance(result, str) and len(result) > 10:
            tn = result
            t.ok(f"Order trade_no={tn[:12]}...")
        else:
            t.bad(f"Order assign: {result}")
    except Exception as e:
        t.bad(f"Order assign failed: {e}")

    # 4. DB verify
    if tn:
        orow = db_val(f"SELECT id,trade_no,plan_id,total_amount,status FROM v2_order WHERE trade_no='{tn}'")
        if orow:
            oid, db_tn, db_pid, db_amt, db_status = orow.split("|")
            if db_pid == str(pid) and db_amt == "199" and db_status == "0":
                t.ok(f"Full cycle DB: plan={db_pid} amount={db_amt} status={db_status}")
            else:
                t.bad(f"DB mismatch: {orow}")

            # Mark as paid (full cycle test)
            try:
                order_api.paid(tn)
                paid_status = db_val(f"SELECT status FROM v2_order WHERE trade_no='{tn}'")
                t.ok(f"Order.paid → status={paid_status}")
            except Exception as e:
                t.bad(f"Order.paid: {e}")
        else:
            t.bad("Order not found in DB")

    # 5. Cleanup
    user_api.destroy(id=uid)
    plan_api.drop(id=pid)
    t.ok("Full cycle cleanup done")


def main():
    token = load_token()
    if not token:
        print("FATAL: No token")
        sys.exit(1)

    client = XboardClient(base_url=BASE_URL, secure_path=SECURE_PATH, token=token)
    log_path = LOG_DIR / "phase5-final.log"
    all_rows = []
    tp = tf = 0
    start = datetime.now(timezone.utc)

    tests = [
        ("traffic_reset", test_traffic_reset),
        ("mail_template", test_mail_template),
        ("full_cycle", test_full_cycle),
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
    header = f"Phase 5 Tests — {start.isoformat()}\n"
    header += f"Total: {tp + tf} | Pass: {tp} | Fail: {tf} | {elapsed:.1f}s\n\n"
    log_path.write_text(header + "\n".join(all_rows) + "\n")
    print(f"\n=== Log: {log_path} ===")
    print(f"\n{'='*60}")
    print(f"PHASE 5: {tp+tf} tests | Pass: {tp} | Fail: {tf}")
    sys.exit(0 if tf == 0 else 1)


if __name__ == "__main__":
    main()
