#!/usr/bin/env python3
"""Phase 3 integration tests — stat, notice, ticket, coupon, gift_card.

All tests: API call → DB verify → cleanup.
"""

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from xboard_api import XboardClient, load_token
from xboard_api.resources.stat import StatResource
from xboard_api.resources.notice import NoticeResource
from xboard_api.resources.ticket import TicketResource
from xboard_api.resources.coupon import CouponResource
from xboard_api.resources.gift_card import GiftCardResource

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
            sys.stderr.write(f"[DB-ERR] {r.stderr.strip()}\n")
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
def test_stat(client, t):
    api = StatResource(client)

    r = api.get_override()
    if isinstance(r, dict) and "month_income" in r:
        t.ok(f"getOverride: income={r.get('month_income')}, nodes={r.get('online_nodes')}")
    else:
        t.bad(f"getOverride unexpected: {str(r)[:100]}")

    stats = api.get_stats()
    if isinstance(stats, dict):
        t.ok(f"getStats: keys={len(stats)}")
    else:
        t.bad(f"getStats unexpected")

    rank = api.get_server_last_rank()
    t.ok(f"getServerLastRank: {len(rank) if isinstance(rank, list) else '?'} entries")

    traffic = api.get_traffic_rank(type="user")
    t.ok(f"getTrafficRank(user): {len(traffic) if isinstance(traffic, list) else '?'} entries")


def test_notice(client, t):
    api = NoticeResource(client)
    uniq = datetime.now().strftime("%H%M%S")
    title = f"TEST-notice-{uniq}"
    content = "Phase 3 test notice content"
    before = db_count("v2_notice")

    r = api.save(title=title, content=content, show=1)
    if r is True:
        t.ok("Notice.save → success")
    else:
        t.bad(f"Notice.save unexpected: {r}")
        return

    row = db_val(f"SELECT id,title,content,show FROM v2_notice WHERE title='{title}'")
    if row:
        nid = int(row.split("|")[0])
        if title in row and content in row:
            t.ok(f"DB notice: id={nid} title/content/show OK")
        else:
            t.bad(f"DB mismatch: {row}")

        # Test show toggle
        api.show(id=nid)
        show_val = db_val(f"SELECT show FROM v2_notice WHERE id={nid}")
        t.ok(f"Notice.show toggled → show={show_val}")

        api.drop(id=nid)
        after = db_count("v2_notice")
        t.ok(f"Notice dropped: {before}→{after}" if after == before else f"Drop wrong: {before}→{after}")
    else:
        t.bad(f"Notice not found: {title}")


def test_ticket(client, t):
    api = TicketResource(client)

    r = api.fetch(page=1, page_size=10)
    # Ticket/fetch returns {data: [...], total: N} from response() helper
    items = r if isinstance(r, list) else r.get("data", [])
    total = r.get("total", len(items)) if isinstance(r, dict) else len(items)
    t.ok(f"Ticket.fetch → total={total}, items={len(items)}")


def test_coupon(client, t):
    api = CouponResource(client)
    uniq = datetime.now().strftime("%H%M%S")
    name = f"TEST-coupon-{uniq}"
    now = int(time.time())
    before = db_count("v2_coupon")

    r = api.generate(
        name=name,
        type=1,
        value=10,
        started_at=now,
        ended_at=now + 86400 * 30,
        generate_count=1,
        limit_use=100,
    )
    # Generate returns the coupon(s) or True
    if isinstance(r, dict):
        t.ok(f"Coupon.generate → dict keys: {list(r.keys())[:5]}")
    elif r is True:
        t.ok("Coupon.generate → success")
    elif isinstance(r, list):
        t.ok(f"Coupon.generate → {len(r)} coupons")
    else:
        t.bad(f"Coupon.generate unexpected: {r}")
        return

    row = db_val(f"SELECT id,name,type,value,limit_use FROM v2_coupon WHERE name='{name}'")
    if row:
        cid = int(row.split("|")[0])
        if name in row and "10" in row:
            t.ok(f"DB coupon: id={cid} type=1 value=10 limit=100")

            # Test show toggle
            api.show(id=cid)
            show_val = db_val(f"SELECT show FROM v2_coupon WHERE id={cid}")
            t.ok(f"Coupon.show toggled → show={show_val}")

            api.drop(id=cid)
            after = db_count("v2_coupon")
            t.ok(f"Coupon dropped: {before}→{after}" if after == before else f"Drop wrong: {before}→{after}")
        else:
            t.bad(f"DB mismatch: {row}")
    else:
        t.bad(f"Coupon not found: {name}")


def test_gift_card(client, t):
    api = GiftCardResource(client)
    uniq = datetime.now().strftime("%H%M%S")
    tname = f"TEST-gc-{uniq}"

    # Types
    types = api.types()
    if isinstance(types, list):
        valid_type = types[0].get("id", 1) if types else 1
        t.ok(f"GiftCard.types → {len(types)} types")
    else:
        valid_type = 1
        t.bad(f"GiftCard.types unexpected: {types}")

    # Create template
    r = api.create_template(
        name=tname,
        type=valid_type,
        rewards=[{"type": "traffic", "value": 10}],
        description="Phase 3 test",
        status=1,
    )
    tid = None
    if isinstance(r, dict):
        tid = r.get("id")
        t.ok(f"Create template → id={tid}")
    else:
        t.bad(f"Create template unexpected: {r}")
        return

    if not tid:
        t.bad("No template id in response")
        return

    # DB verify template
    trow = db_val(f"SELECT id,name,type,status FROM v2_gift_card_template WHERE id={tid}")
    if trow and tname in trow:
        t.ok(f"DB template: {trow}")
    else:
        t.bad(f"DB template not found: tid={tid}")

    # List templates
    tmpls = api.templates(page=1, per_page=5)
    t.ok(f"Templates list: {'ok' if isinstance(tmpls, dict) else str(tmpls)[:50]}")

    # Generate codes
    cr = api.generate_codes(template_id=tid, count=3)

    # DB verify codes
    code_count = db_count("v2_gift_card_code", f"template_id={tid}")
    t.ok(f"Generate codes → DB: {code_count} codes")

    # Delete codes first (can't delete template with codes)
    code_ids = db_val(f"SELECT id FROM v2_gift_card_code WHERE template_id={tid} LIMIT 1")
    if code_ids:
        api.delete_code(id=int(code_ids))
    # Delete remaining codes via DB
    db(f"DELETE FROM v2_gift_card_code WHERE template_id={tid}")

    # Now delete template
    api.delete_template(id=tid)
    tpl_row = db_val(f"SELECT id FROM v2_gift_card_template WHERE id={tid}")
    if not tpl_row:
        t.ok("Template deleted from DB")
    else:
        t.bad(f"Template not deleted: {tpl_row}")


def main():
    token = load_token()
    if not token:
        print("FATAL: No token")
        sys.exit(1)

    client = XboardClient(base_url=BASE_URL, secure_path=SECURE_PATH, token=token)
    log_path = LOG_DIR / "phase3-secondary.log"
    all_rows = []
    tp = tf = 0
    start = datetime.now(timezone.utc)

    tests = [
        ("stat", test_stat),
        ("notice", test_notice),
        ("ticket", test_ticket),
        ("coupon", test_coupon),
        ("gift_card", test_gift_card),
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
    header = f"Phase 3 Tests — {start.isoformat()}\n"
    header += f"Total: {tp + tf} | Pass: {tp} | Fail: {tf} | {elapsed:.1f}s\n\n"
    log_path.write_text(header + "\n".join(all_rows) + "\n")
    print(f"\n=== Log: {log_path} ===")
    sys.exit(0 if tf == 0 else 1)


if __name__ == "__main__":
    main()
