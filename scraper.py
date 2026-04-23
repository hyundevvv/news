import feedparser
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from deep_translator import GoogleTranslator
import time
import re
from email.utils import parsedate_to_datetime
import os

# ─────────────────────────────────────────────────────────────────
# 주식 및 금융 전문 RSS 피드 목록 (4분할 개편)
# ─────────────────────────────────────────────────────────────────
FEEDS = {
    'K-MARKET': [ # 국내 증시
        "https://news.einfomax.co.kr/rss/S1N1.xml", # 연합인포맥스 시황
        "https://rss.hankyung.com/feed/stock.xml", # 한경 증권
        "https://rss.mt.co.kr/mt_news_stock.xml", # 머투 증권
        "https://www.mk.co.kr/rss/30100041/" # 매경 기업/종목
    ],
    'GLOBAL': [ # 해외 증시
        "https://finance.yahoo.com/news/rssindex",
        "https://www.marketwatch.com/rss/topstories",
        "https://www.investing.com/rss/news_25.rss",
        "https://techcrunch.com/feed/" # 나스닥 테크주
    ],
    'MACRO': [ # 거시경제 / 지표
        "https://www.marketwatch.com/rss/economy",
        "https://finance.yahoo.com/news/rss",
        "https://www.hankyung.com/feed/economy",
        "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko"
    ],
    'INDUSTRY': [ # 산업 / 테마 (AI, 반도체 등)
        "https://www.zdnet.co.kr/newsrss/all.xml", # 테크 산업
        "https://rss.hankyung.com/feed/it.xml", # 한경 IT
        "https://www.mk.co.kr/rss/50300011/", # 매경 IT/과학
        "https://www.theverge.com/rss/index.xml" # 글로벌 테크/산업
    ]
}

BLACKLIST_DOMAINS = ['ndsoftnews.com', 'test', 'dev.', 'localhost', 'internal']
PAYWALL_KEYWORDS = ['[유료]', '[프리미엄]', '[구독]', '[Premium]', '[Exclusive]', '로그인 필요']

HEADERS = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36' }

def load_existing_data():
    if not os.path.exists('data.js'): return {}
    try:
        with open('data.js', 'r', encoding='utf-8') as f:
            content = f.read()
            json_match = re.search(r'const newsData = (\{.*\});', content, re.DOTALL)
            if json_match: return json.loads(json_match.group(1))
    except: pass
    return {}

def fetch_indices():
    indices = []
    symbols = "^KS11,^KQ11,^IXIC,KRW=X,JPYKRW=X"
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        data = resp.json()
        mapping = {'^KS11': 'KOSPI', '^KQ11': 'KOSDAQ', '^IXIC': 'NASDAQ', 'KRW=X': 'USD/KRW', 'JPYKRW=X': 'JPY/KRW'}
        results = data.get('quoteResponse', {}).get('result', [])
        temp_dict = {item['symbol']: item for item in results}
        for sym in symbols.split(','):
            item = temp_dict.get(sym)
            if item:
                indices.append({
                    'name': mapping.get(sym, sym),
                    'price': "{:,.2f}".format(item.get('regularMarketPrice', 0.0)),
                    'change': "{:+.2f}%".format(item.get('regularMarketChangePercent', 0.0))
                })
    except: pass
    return indices

def parse_date(entry):
    dt = None
    for attr in ['published', 'updated', 'created']:
        raw = getattr(entry, attr, None)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                break
            except: pass
    if dt is None: dt = datetime.now(timezone.utc)
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def clean_text(html_text):
    if not html_text: return ""
    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text()
    return re.sub(r'\s+', ' ', text).strip()

def extract_image(entry):
    if hasattr(entry, 'media_content') and entry.media_content:
        return entry.media_content[0].get('url', '')
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        return entry.media_thumbnail[0].get('url', '')
    for field in ['summary', 'description']:
        val = getattr(entry, field, '') or ''
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', val)
        if match: return match.group(1)
    return None

def fetch_all_entries(category, feed_urls):
    all_entries = []
    seen_titles = set()
    for url in feed_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:20]:
                title = (entry.get('title') or '').strip()
                link = entry.get('link', '#')
                if any(d in link.lower() for d in BLACKLIST_DOMAINS): continue
                if any(kw in title for kw in PAYWALL_KEYWORDS): continue
                if not title or title in seen_titles: continue
                seen_titles.add(title)
                all_entries.append({'_entry': entry, '_date': parse_date(entry), '_title': title, '_link': link})
        except: pass
    return all_entries

def build_articles(entries, translator):
    articles = []
    for e in entries:
        title = re.sub(r'\s*[-|]\s*[^[-|]*$', '', e['_title']).strip()
        summary = clean_text(getattr(e['_entry'], 'summary', '') or getattr(e['_entry'], 'description', ''))
        publisher = getattr(e['_entry'], 'source', {}).get('title', 'Finance')
        if not re.search('[가-힣]', title):
            try: 
                title = translator.translate(title) or title
                if summary: summary = translator.translate(summary[:300]) or summary
            except: pass
        image = extract_image(e['_entry']) or "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=800&auto=format&fit=crop"
        articles.append({
            'title': title, 'summary': summary[:200], 'link': e['_link'],
            'date': e['_date'].strftime('%m.%d %H:%M'), 'image': image, 'publisher': publisher,
            '_timestamp': int(e['_date'].timestamp())
        })
    return articles

def merge_and_trim(existing_list, new_list, limit=40):
    combined = new_list + (existing_list or [])
    unique_list = []
    seen_links = set()
    for item in combined:
        if item['link'] not in seen_links:
            unique_list.append(item)
            seen_links.add(item['link'])
    unique_list.sort(key=lambda x: x.get('_timestamp', 0), reverse=True)
    return unique_list[:limit]

def fetch_news():
    existing_data = load_existing_data()
    all_data = { 'categories': {}, 'indices': [], 'last_updated': '' }
    translator = GoogleTranslator(source='auto', target='ko')
    all_data['indices'] = fetch_indices()
    for category, urls in FEEDS.items():
        print(f"[{category}] Processing...")
        new_entries = fetch_all_entries(category, urls)
        new_articles = build_articles(new_entries, translator)
        existing_list = existing_data.get('categories', {}).get(category, [])
        all_data['categories'][category] = merge_and_trim(existing_list, new_articles, 40)
    kst = timezone(timedelta(hours=9))
    all_data['last_updated'] = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S KST')
    return all_data

if __name__ == "__main__":
    news_data = fetch_news()
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(f"const newsData = {json.dumps(news_data, ensure_ascii=False, indent=4)};")
    print("Done.")
