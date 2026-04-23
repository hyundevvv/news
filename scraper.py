import feedparser
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from deep_translator import GoogleTranslator
import time
import re
from email.utils import parsedate_to_datetime

# ─────────────────────────────────────────────────────────────────
# 주식 및 금융 전문 RSS 피드 목록
# ─────────────────────────────────────────────────────────────────
FEEDS = {
    'MARKET': [
        "https://finance.yahoo.com/news/rssindex",
        "https://www.marketwatch.com/rss/topstories",
        "https://news.einfomax.co.kr/rss/S1N1.xml",
        "https://rss.hankyung.com/feed/stock.xml"
    ],
    'STOCKS': [
        "https://www.investing.com/rss/news_25.rss",
        "https://rss.mt.co.kr/mt_news_stock.xml",
        "https://www.mk.co.kr/rss/30100041/",
        "https://techcrunch.com/feed/"
    ],
    'ECONOMY': [
        "https://www.marketwatch.com/rss/economy",
        "https://finance.yahoo.com/news/rss",
        "https://www.hankyung.com/feed/economy",
        "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko"
    ]
}

BLACKLIST_DOMAINS = ['ndsoftnews.com', 'test', 'dev.', 'localhost', 'internal']
PAYWALL_KEYWORDS = ['[유료]', '[프리미엄]', '[구독]', '[Premium]', '[Exclusive]', '로그인 필요']

HEADERS = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36' }

def fetch_indices():
    """야후 파이낸스 API를 사용하여 주요 증시 지수를 정확하게 수집합니다."""
    indices = []
    symbols = "^KS11,^KQ11,^IXIC,^GSPC,KRW=X"
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbols}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        data = resp.json()
        
        mapping = {
            '^KS11': 'KOSPI', 
            '^KQ11': 'KOSDAQ', 
            '^IXIC': 'NASDAQ', 
            '^GSPC': 'S&P 500', 
            'KRW=X': 'USD/KRW'
        }
        
        results = data.get('quoteResponse', {}).get('result', [])
        for item in results:
            symbol = item.get('symbol')
            name = mapping.get(symbol, symbol)
            price = item.get('regularMarketPrice', 0.0)
            change = item.get('regularMarketChangePercent', 0.0)
            
            # 포맷팅: 1,234.56 형식 및 부호 추가
            formatted_price = "{:,.2f}".format(price)
            formatted_change = "{:+.2f}%".format(change)
            
            indices.append({
                'name': name,
                'price': formatted_price,
                'change': formatted_change
            })
            
        print(f"[Indices] Successfully fetched {len(indices)} items.")
    except Exception as e:
        print(f"Index API Error: {e}")
        # API 오류 시에만 최소한의 안전장치 (실제 데이터와 구분되도록 처리)
        indices = [{"name": "Check Connection", "price": "0.00", "change": "0.00%"}]
        
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
    all_entries.sort(key=lambda x: x['_date'], reverse=True)
    return all_entries[:40]

def build_articles(entries, category, translator):
    articles = []
    for e in entries:
        title = re.sub(r'\s*[-|]\s*[^[-|]*$', '', e['_title']).strip()
        summary = clean_text(getattr(e['_entry'], 'summary', '') or getattr(e['_entry'], 'description', ''))
        publisher = getattr(e['_entry'], 'source', {}).get('title', 'Finance News')
        
        if not re.search('[가-힣]', title):
            try: 
                title = translator.translate(title) or title
                if summary: summary = translator.translate(summary[:300]) or summary
            except: pass
        
        image = extract_image(e['_entry']) or "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=800&auto=format&fit=crop"
        articles.append({
            'title': title, 'summary': summary[:200], 'link': e['_link'],
            'date': e['_date'].strftime('%m.%d %H:%M'), 'image': image, 'publisher': publisher
        })
    return articles

def fetch_news():
    all_data = { 'categories': {}, 'indices': [], 'last_updated': '' }
    translator = GoogleTranslator(source='auto', target='ko')
    
    # 1. 지수 정보 수집 (API 방식)
    all_data['indices'] = fetch_indices()
    
    # 2. 뉴스 카테고리 수집
    for category, urls in FEEDS.items():
        print(f"[{category}] Processing...")
        entries = fetch_all_entries(category, urls)
        all_data['categories'][category] = build_articles(entries, category, translator)
    
    kst = timezone(timedelta(hours=9))
    all_data['last_updated'] = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S KST')
    return all_data

if __name__ == "__main__":
    news_data = fetch_news()
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(f"const newsData = {json.dumps(news_data, ensure_ascii=False, indent=4)};")
    print("Done.")
