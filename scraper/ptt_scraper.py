import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup
import re
from collections import Counter
from db.database import add_pending_word, get_blacklist

PTT_BASE = "https://www.ptt.cc"
BOARDS = ["Gossiping", "C_Chat"]

# PTT 八卦板需要確認年齡
SESSION = requests.Session()
SESSION.cookies.set("over18", "1")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.ptt.cc/bbs/index.html",
}

# 過濾用：太短或太常見的詞不計入
STOP_WORDS = {
    "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都",
    "一", "一個", "上", "也", "很", "到", "說", "要", "去", "你",
    "會", "著", "沒有", "看", "好", "自己", "這", "那", "啊", "嗎",
    "re", "推", "噓", "→", "樓", "版", "問題", "討論", "分享", "請問",
    "影片", "新聞", "心得", "閒聊", "公告", "轉錄",
    "re:", "re:re", "re:re:", ":re", "e:re", "e:", ":r", "vy", ":vy",
    "請益", "徵求", "發問", "詢問", "求助", "感謝", "謝謝", "爬文",
}

MIN_WORD_LENGTH = 2   # 至少幾個字
MIN_FREQUENCY = 3     # 出現幾次才進待審核


def fetch_board_titles(board: str, pages: int = 5) -> list[str]:
    """抓取看板最新 N 頁的文章標題"""
    titles = []

    # 先取得最新頁的頁碼
    url = f"{PTT_BASE}/bbs/{board}/index.html"
    try:
        resp = SESSION.get(url, headers=HEADERS, timeout=15, verify=False)
    except Exception as e:
        print(f"[Scraper] 連線失敗 {board}：{e}")
        return []
    if resp.status_code != 200:
        print(f"[Scraper] 無法連線至 {board}，狀態碼：{resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # 找「上頁」按鈕取得目前最大頁碼
    prev_link = soup.select_one("a.btn.wide:nth-of-type(2)")
    if prev_link and prev_link.get("href"):
        match = re.search(r"index(\d+)\.html", prev_link["href"])
        max_page = int(match.group(1)) + 1 if match else 1
    else:
        max_page = 1

    # 爬最新幾頁
    for page in range(max_page, max(max_page - pages, 0), -1):
        page_url = f"{PTT_BASE}/bbs/{board}/index{page}.html"
        try:
            r = SESSION.get(page_url, headers=HEADERS, timeout=15, verify=False)
            s = BeautifulSoup(r.text, "html.parser")
            for entry in s.select("div.title a"):
                titles.append(entry.get_text(strip=True))
        except Exception as e:
            print(f"[Scraper] 抓取 {page_url} 失敗：{e}")

    print(f"[Scraper] {board} 共抓到 {len(titles)} 篇標題")
    return titles


def extract_ngrams(titles: list[str]) -> Counter:
    """從標題中提取 2~4 字的 n-gram 詞組並計頻"""
    counter = Counter()
    blacklist_set = set(get_blacklist())

    for title in titles:
        # 移除標點與空白
        clean = re.sub(r"[【】\[\]《》「」『』\(\)（）\s\.,!?！？。，、~～＊*#\-_/\\]", " ", title)
        tokens = [t for t in clean.split() if t and t not in STOP_WORDS]

        # 單詞計頻
        for token in tokens:
            if len(token) >= MIN_WORD_LENGTH and token not in STOP_WORDS:
                counter[token] += 1

        # 2~4 字 n-gram
        words = list(clean.replace(" ", ""))
        for n in range(2, 5):
            for i in range(len(words) - n + 1):
                gram = "".join(words[i:i+n])
                if gram not in STOP_WORDS:
                    counter[gram] += 1

    # 移除已在黑名單的詞（不需要重複記錄）
    for word in blacklist_set:
        counter.pop(word, None)

    return counter


def run_scraper():
    """執行爬蟲並將高頻新詞存入待審核資料庫"""
    all_titles = []

    for board in BOARDS:
        titles = fetch_board_titles(board, pages=5)
        all_titles.extend(titles)

    if not all_titles:
        print("[Scraper] 沒有抓到任何標題，結束")
        return

    counter = extract_ngrams(all_titles)

    # 篩選出頻率超過門檻的詞
    trending = [(word, freq) for word, freq in counter.items() if freq >= MIN_FREQUENCY]
    trending.sort(key=lambda x: x[1], reverse=True)

    print(f"[Scraper] 發現 {len(trending)} 個高頻詞，存入待審核資料庫")

    for word, freq in trending[:100]:  # 最多存前 100 個
        add_pending_word(word, source="PTT", frequency=freq)

    print("[Scraper] 完成")
    return trending[:20]  # 回傳前 20 個供預覽


if __name__ == "__main__":
    from db.database import init_db
    init_db()
    results = run_scraper()
    if results:
        print("\n--- 本次高頻詞 Top 20 ---")
        for word, freq in results:
            print(f"  {word}：{freq} 次")
