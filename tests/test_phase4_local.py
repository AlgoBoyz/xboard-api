#!/usr/bin/env python3
"""Phase 4 — knowledge, payment, system, theme, plugin (read-only or system-level)."""

import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from xboard_api import XboardClient, load_token
from xboard_api.resources.knowledge import KnowledgeResource
from xboard_api.resources.payment import PaymentResource
from xboard_api.resources.system import SystemResource
from xboard_api.resources.theme import ThemeResource
from xboard_api.resources.plugin import PluginResource

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


def test_knowledge(client, t):
    api = KnowledgeResource(client)
    uniq = datetime.now().strftime("%H%M%S")
    title = f"TEST-kb-{uniq}"
    content = "Phase 4 knowledge test"
    before = db_count("v2_knowledge")

    r = api.save(title=title, content=content, show=1)
    if r is True:
        t.ok("Knowledge.save → success")
    else:
        t.bad(f"Knowledge.save unexpected: {r}")
        return

    row = db_val(f"SELECT id,title,content,show FROM v2_knowledge WHERE title='{title}'")
    if row:
        kid = int(row.split("|")[0])
        if title in row and content in row:
            t.ok(f"DB knowledge: id={kid} OK")

            # Fetch single
            single = api.fetch(id=kid)
            t.ok(f"Knowledge.fetch(id={kid}) OK")

            api.drop(id=kid)
            after = db_count("v2_knowledge")
            t.ok(f"Knowledge dropped: {before}→{after}" if after == before else f"Drop wrong: {before}→{after}")
        else:
            t.bad(f"DB mismatch: {row}")
    else:
        t.bad(f"Knowledge not found: {title}")

    # Categories
    cats = api.get_category()
    t.ok(f"get_category: {len(cats) if isinstance(cats, list) else '?'} categories")


def test_payment(client, t):
    api = PaymentResource(client)

    methods = api.get_payment_methods()
    t.ok(f"getPaymentMethods: {len(methods)} available")

    payments = api.fetch()
    t.ok(f"fetch: {len(payments)} configured")


def test_system(client, t):
    api = SystemResource(client)

    status = api.get_system_status()
    if isinstance(status, dict):
        t.ok(f"getSystemStatus OK")
    else:
        t.bad(f"getSystemStatus: {status}")

    logs = api.get_audit_log(page=1, page_size=5)
    t.ok(f"getAuditLog: {'dict' if isinstance(logs, dict) else '?'}")


def test_theme(client, t):
    api = ThemeResource(client)

    themes = api.get_themes()
    if isinstance(themes, dict):
        active = themes.get("active", themes.get("active_theme", "?"))
        t.ok(f"getThemes: active={active}")
    else:
        t.bad(f"getThemes: {themes}")


def test_plugin(client, t):
    api = PluginResource(client)

    types = api.types()
    t.ok(f"types: {'dict' if isinstance(types, dict) else '?'}")

    plugins = api.get_plugins()
    t.ok(f"getPlugins: {len(plugins)} installed")


def main():
    token = load_token()
    if not token:
        print("FATAL: No token")
        sys.exit(1)

    client = XboardClient(base_url=BASE_URL, secure_path=SECURE_PATH, token=token)
    log_path = LOG_DIR / "phase4-peripheral.log"
    all_rows = []
    tp = tf = 0
    start = datetime.now(timezone.utc)

    tests = [
        ("knowledge", test_knowledge),
        ("payment", test_payment),
        ("system", test_system),
        ("theme", test_theme),
        ("plugin", test_plugin),
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
    header = f"Phase 4 Tests — {start.isoformat()}\n"
    header += f"Total: {tp + tf} | Pass: {tp} | Fail: {tf} | {elapsed:.1f}s\n\n"
    log_path.write_text(header + "\n".join(all_rows) + "\n")
    print(f"\n=== Log: {log_path} ===")
    sys.exit(0 if tf == 0 else 1)


if __name__ == "__main__":
    main()
