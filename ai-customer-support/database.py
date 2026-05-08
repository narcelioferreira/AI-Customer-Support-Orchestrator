import sqlite3
import os
import uuid
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "orchestrator.db")

SLA_HOURS = {"urgente": 2, "alta": 8, "media": 24, "baixa": 48}

SECTOR_COLORS = {
    "financeiro": "#F59E0B",
    "logistica": "#3B82F6",
    "comercial": "#10B981",
    "juridico": "#EF4444",
    "geral": "#8B5CF6",
}

PRIORITY_COLORS = {
    "urgente": "#EF4444",
    "alta": "#F59E0B",
    "media": "#3B82F6",
    "baixa": "#10B981",
}


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        cnpj TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        segment TEXT,
        status TEXT DEFAULT 'ativo',
        contact_name TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cnpj TEXT NOT NULL,
        contract_number TEXT UNIQUE,
        product TEXT,
        value REAL,
        status TEXT DEFAULT 'ativo',
        start_date TEXT,
        end_date TEXT,
        payment_day INTEGER,
        payment_terms TEXT,
        FOREIGN KEY(cnpj) REFERENCES clients(cnpj)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS protocols (
        protocol_id TEXT PRIMARY KEY,
        cnpj TEXT,
        client_name TEXT,
        sector TEXT,
        intent TEXT,
        priority TEXT,
        status TEXT DEFAULT 'aberto',
        action TEXT,
        resolved_by TEXT DEFAULT 'ia',
        sla_hours INTEGER,
        sla_deadline TEXT,
        created_at TEXT,
        updated_at TEXT,
        summary TEXT,
        ai_response TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        protocol_id TEXT,
        role TEXT,
        content TEXT,
        timestamp TEXT,
        FOREIGN KEY(protocol_id) REFERENCES protocols(protocol_id)
    )""")

    conn.commit()
    conn.close()


def get_client(cnpj: str):
    clean = cnpj.replace(".", "").replace("/", "").replace("-", "").strip()
    conn = get_conn()
    c = conn.cursor()
    row = c.execute("SELECT * FROM clients WHERE replace(replace(replace(cnpj,'.',''),'/',''),'-','') = ?", (clean,)).fetchone()
    if row:
        client = dict(row)
        contracts = c.execute("SELECT * FROM contracts WHERE cnpj = ?", (client["cnpj"],)).fetchall()
        client["contracts"] = [dict(ct) for ct in contracts]
        conn.close()
        return client
    conn.close()
    return None


def create_protocol(cnpj, client_name, sector, intent, priority, action, summary, ai_response):
    conn = get_conn()
    c = conn.cursor()
    protocol_id = f"PROT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    sla_hours = SLA_HOURS.get(priority, 24)
    sla_deadline = (datetime.now() + timedelta(hours=sla_hours)).isoformat()
    now = datetime.now().isoformat()
    resolved_by = "humano" if action == "escalar" else "ia"

    c.execute("""
    INSERT INTO protocols
      (protocol_id, cnpj, client_name, sector, intent, priority, action,
       sla_hours, sla_deadline, created_at, updated_at, summary, ai_response, resolved_by)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
    (protocol_id, cnpj, client_name, sector, intent, priority, action,
     sla_hours, sla_deadline, now, now, summary, ai_response, resolved_by))

    conn.commit()
    conn.close()
    return protocol_id


def add_message(protocol_id, role, content):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO messages (protocol_id, role, content, timestamp) VALUES (?,?,?,?)",
              (protocol_id, role, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_messages(protocol_id):
    conn = get_conn()
    c = conn.cursor()
    rows = c.execute("SELECT * FROM messages WHERE protocol_id=? ORDER BY id", (protocol_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_protocols(sector=None, status=None, limit=200):
    conn = get_conn()
    c = conn.cursor()
    query = "SELECT * FROM protocols WHERE 1=1"
    params = []
    if sector and sector != "Todos":
        query += " AND sector=?"
        params.append(sector)
    if status and status != "Todos":
        query += " AND status=?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = c.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_protocol_status(protocol_id, status):
    conn = get_conn()
    conn.execute("UPDATE protocols SET status=?, updated_at=? WHERE protocol_id=?",
                 (status, datetime.now().isoformat(), protocol_id))
    conn.commit()
    conn.close()


def get_stats():
    conn = get_conn()
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM protocols").fetchone()[0]
    aberto = c.execute("SELECT COUNT(*) FROM protocols WHERE status='aberto'").fetchone()[0]
    fechado = c.execute("SELECT COUNT(*) FROM protocols WHERE status='fechado'").fetchone()[0]
    ia = c.execute("SELECT COUNT(*) FROM protocols WHERE resolved_by='ia'").fetchone()[0]
    humano = c.execute("SELECT COUNT(*) FROM protocols WHERE resolved_by='humano'").fetchone()[0]

    by_sector = dict(c.execute("SELECT sector, COUNT(*) FROM protocols GROUP BY sector").fetchall())
    by_priority = dict(c.execute("SELECT priority, COUNT(*) FROM protocols GROUP BY priority").fetchall())

    sla_ok = c.execute("""
        SELECT COUNT(*) FROM protocols
        WHERE status='fechado' AND updated_at <= sla_deadline""").fetchone()[0]
    sla_breach = c.execute("""
        SELECT COUNT(*) FROM protocols
        WHERE status='fechado' AND updated_at > sla_deadline""").fetchone()[0]

    recent = [dict(r) for r in c.execute(
        "SELECT created_at, sector FROM protocols ORDER BY created_at DESC LIMIT 100").fetchall()]

    conn.close()
    return {
        "total": total, "aberto": aberto, "fechado": fechado,
        "ia": ia, "humano": humano,
        "by_sector": by_sector, "by_priority": by_priority,
        "sla_ok": sla_ok, "sla_breach": sla_breach,
        "recent": recent
    }


def is_seeded():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    conn.close()
    return count > 0
