import os
import time
import json
import anthropic
from dotenv import load_dotenv
from db.database import get_conn, update_pending_risk

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PROMPT_TEMPLATE = """分析台灣網路詞彙「{word}」是否為惡意隱語或歧視用語（含淫夢梗、性少數歧視等）。只回JSON：
{{"risk_score":0.0到1.0,"category":"淫夢梗/歧視用語/一般詞彙/不確定","reason":"20字內說明"}}"""


def analyze_word(word: str, retries: int = 3) -> dict:
    """用 Claude Haiku 分析單一詞彙的風險"""
    prompt = PROMPT_TEMPLATE.format(word=word)

    for attempt in range(retries):
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()

            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]

            result = json.loads(text)
            return {
                "risk_score": float(result.get("risk_score", 0)),
                "category": result.get("category", "不確定"),
                "reason": result.get("reason", ""),
            }
        except Exception as e:
            err = str(e)
            if "429" in err or "overloaded" in err.lower():
                wait = 30
                print(f"[Analyzer] 達到速率限制，等待 {wait} 秒後重試... (第 {attempt+1}/{retries} 次)")
                time.sleep(wait)
            else:
                print(f"[Analyzer] 分析「{word}」失敗：{err[:80]}")
                return {"risk_score": 0.0, "category": "分析失敗", "reason": err[:50]}

    return {"risk_score": 0.0, "category": "重試失敗", "reason": "多次失敗"}


def run_analyzer(limit: int = 50, min_frequency: int = 3):
    """批次分析待審核資料庫中尚未評分的詞彙"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT word FROM pending_words
        WHERE risk_score = 0 AND status = 'pending' AND frequency >= ?
        ORDER BY frequency DESC
        LIMIT ?
    """, (min_frequency, limit)).fetchall()
    conn.close()

    words = [r["word"] for r in rows]
    print(f"[Analyzer] 開始分析 {len(words)} 個詞彙...")

    results = []
    for i, word in enumerate(words):
        result = analyze_word(word)
        update_pending_risk(word, result["risk_score"], result["reason"])
        results.append((word, result))

        status = "[HIGH]" if result["risk_score"] >= 0.7 else "[MED]" if result["risk_score"] >= 0.4 else "[LOW]"
        print(f"  [{i+1}/{len(words)}] {status} [{word}] {result['risk_score']:.2f} - {result['reason']}")

        # 免費方案限制 15次/分鐘，每次間隔 5 秒
        time.sleep(5)

    print(f"\n[Analyzer] 完成，共分析 {len(results)} 個詞")

    # 顯示高風險詞彙
    high_risk = [(w, r) for w, r in results if r["risk_score"] >= 0.7]
    if high_risk:
        print(f"\n--- 高風險詞彙（score >= 0.7）共 {len(high_risk)} 個 ---")
        for word, r in high_risk:
            print(f"  [HIGH] [{word}] {r['risk_score']:.2f} | {r['category']} | {r['reason']}")

    return results


if __name__ == "__main__":
    from db.database import init_db
    init_db()
    run_analyzer(limit=5)  # 測試用
