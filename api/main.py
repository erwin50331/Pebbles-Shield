from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from db.database import get_conn, add_to_blacklist, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Pebbles Shield API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 黑名單 ──────────────────────────────────────────────

@app.get("/blacklist")
def get_blacklist():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM blacklist ORDER BY added_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


class WordIn(BaseModel):
    word: str
    category: Optional[str] = "general"


@app.post("/blacklist")
def add_blacklist(body: WordIn):
    add_to_blacklist(body.word, body.category)
    return {"ok": True, "word": body.word.lower()}


@app.delete("/blacklist/{word}")
def delete_blacklist(word: str):
    conn = get_conn()
    conn.execute("DELETE FROM blacklist WHERE word = ?", (word.lower(),))
    conn.commit()
    conn.close()
    return {"ok": True}


# ── 待審核詞彙 ───────────────────────────────────────────

@app.get("/pending")
def get_pending(status: str = "pending", limit: int = 100):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM pending_words
        WHERE status = ?
        ORDER BY risk_score DESC, frequency DESC
        LIMIT ?
    """, (status, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/pending/{word}/approve")
def approve_word(word: str, category: Optional[str] = "general"):
    """審核通過：加入黑名單"""
    conn = get_conn()
    conn.execute("UPDATE pending_words SET status = 'approved' WHERE word = ?", (word,))
    conn.commit()
    conn.close()
    add_to_blacklist(word, category)
    return {"ok": True, "action": "approved", "word": word}


@app.post("/pending/{word}/reject")
def reject_word(word: str):
    """標記為誤報"""
    conn = get_conn()
    conn.execute("UPDATE pending_words SET status = 'rejected' WHERE word = ?", (word,))
    conn.commit()
    conn.close()
    return {"ok": True, "action": "rejected", "word": word}


# ── 違規紀錄 ─────────────────────────────────────────────

@app.get("/violations")
def get_violations(limit: int = 50):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM violations
        ORDER BY detected_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/violations/stats")
def get_stats():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM violations").fetchone()[0]
    today = conn.execute("""
        SELECT COUNT(*) FROM violations
        WHERE date(detected_at) = date('now')
    """).fetchone()[0]
    blacklist_count = conn.execute("SELECT COUNT(*) FROM blacklist").fetchone()[0]
    pending_count = conn.execute(
        "SELECT COUNT(*) FROM pending_words WHERE status = 'pending'"
    ).fetchone()[0]
    conn.close()
    return {
        "total_violations": total,
        "today_violations": today,
        "blacklist_count": blacklist_count,
        "pending_count": pending_count,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
