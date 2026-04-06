import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "pebbles.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # 已確認黑名單
    c.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            category TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 爬蟲抓到的待審核詞彙
    c.execute("""
        CREATE TABLE IF NOT EXISTS pending_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            source TEXT,
            frequency INTEGER DEFAULT 1,
            risk_score REAL DEFAULT 0,
            risk_reason TEXT,
            status TEXT DEFAULT 'pending',
            found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Discord 違規紀錄
    c.execute("""
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            channel_id TEXT,
            user_id TEXT,
            username TEXT,
            message_content TEXT,
            matched_words TEXT,
            action_taken TEXT DEFAULT 'flagged',
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] 資料庫初始化完成")


def add_to_blacklist(word: str, category: str = "general"):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO blacklist (word, category) VALUES (?, ?)",
            (word.lower(), category)
        )
        conn.commit()
    finally:
        conn.close()


def get_blacklist() -> list[str]:
    conn = get_conn()
    rows = conn.execute("SELECT word FROM blacklist").fetchall()
    conn.close()
    return [r["word"] for r in rows]


def add_pending_word(word: str, source: str, frequency: int = 1):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO pending_words (word, source, frequency)
            VALUES (?, ?, ?)
            ON CONFLICT(word) DO UPDATE SET frequency = frequency + ?
        """, (word.lower(), source, frequency, frequency))
        conn.commit()
    finally:
        conn.close()


def update_pending_risk(word: str, score: float, reason: str):
    conn = get_conn()
    conn.execute(
        "UPDATE pending_words SET risk_score = ?, risk_reason = ? WHERE word = ?",
        (score, reason, word)
    )
    conn.commit()
    conn.close()


def log_violation(guild_id, channel_id, user_id, username, content, matched_words):
    conn = get_conn()
    conn.execute("""
        INSERT INTO violations (guild_id, channel_id, user_id, username, message_content, matched_words)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (guild_id, channel_id, user_id, username, content, ",".join(matched_words)))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    # 預設黑名單種子資料
    seed_words = ["池沼", "homo", "兩女一腸", "(確信", "會員制料理", "Homo", "Homo 特有", "Homo特有"]
    for w in seed_words:
        add_to_blacklist(w, "known_slur")
    print("[DB] 種子黑名單已載入")
