import sqlite3
import json
from config import DB
from convert_address import to_friendly


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    db = conn()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS wallets (
            address TEXT PRIMARY KEY,
            balance REAL,
            first_seen INTEGER,
            nfts INTEGER,
            tokens INTEGER,
            tokens_raw TEXT,
            sources TEXT
        );
        CREATE TABLE IF NOT EXISTS queue (
            address TEXT PRIMARY KEY
        );
    """)
    db.commit()
    db.close()


def add_to_queue(addrs):
    normalized = []
    for a in addrs:
        try:
            normalized.append(to_friendly(a))
        except Exception:
            normalized.append(a)
    db = conn()
    db.executemany("INSERT OR IGNORE INTO queue (address) VALUES (?)", [(a,) for a in normalized])
    db.commit()
    db.close()


def get_queue(limit=200):
    db = conn()
    rows = db.execute("""
        SELECT q.address FROM queue q
        LEFT JOIN wallets w ON q.address = w.address
        WHERE w.address IS NULL
        LIMIT ?
    """, (limit,)).fetchall()
    db.close()
    return [r["address"] for r in rows]


def save(data):
    db = conn()
    db.execute("""
        INSERT OR REPLACE INTO wallets
        (address, balance, first_seen, nfts, tokens, tokens_raw, sources)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["address"],
        data["balance"],
        data["first_seen"],
        data["nfts"],
        data["tokens"],
        json.dumps(data["tokens_list"]),
        json.dumps(data["sources"]),
    ))
    db.commit()
    db.close()


def all_wallets():
    db = conn()
    rows = db.execute("SELECT * FROM wallets").fetchall()
    db.close()
    out = []
    for r in rows:
        d = dict(r)
        d["tokens_list"] = json.loads(d["tokens_raw"] or "[]")
        d["sources"] = json.loads(d["sources"] or "[]")
        out.append(d)
    return out
