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
# 주식 및 금융 전문 RSS 피드 목록 (Stock-Centric)
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

# 차단할 도메인 및 유료 키워드
BLACKLIST_DOMAINS = ['ndsoftnews.com', 'test', 'dev.', 'localhost', 'internal']
PAYWALL_KEYWORDS = ['[유료]', '[프리미엄]', '[구독]', '[Premium]', '[Exclusive]', '로그인 필요']

PUBLISHER_LOGOS = {
    '연합': "https://www.yonhapnewstv.co.kr/static/images/common/logo.png",
    '매일경제': "https://www.mk.co.kr/static/common/img/mk_logo.png",
    '한국경제': "https://www.hankyung.com/img/common/hankyung_logo.png",
    '인포맥스': "https://news.einfomax.co.kr/image/logo.png",
    '머니투데이': "https://www.mt.co.kr/favicon.ico",
    'yahoo': "https://s.yimg.com/cv/apiv2/myy/yahoo_logo_v3.png",
    'marketwatch': "https://www.marketwatch.com/favicon.ico",
    'investing': "https://www.investing.com/favicon.ico",
    'techcrunch': "https://techcrunch.com/wp-content/uploads/2015/02/cropped-tc-favicon-lg.png"
}

HEADERS = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36' }

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

def get_publisher_info(entry, url, original_title):
    text = (url + " " + original_title).lower()
    if hasattr(entry, 'source') and 'title' in entry.source:
        found_pub = entry.source.title
    else:
        mapping = {'einfomax': '연합인포맥스', 'mt.co.kr': '머니투데이', 'mk.co.kr': '매일경제', 'hankyung': '한국경제', 'marketwatch': 'MarketWatch', 'investing': 'Investing.com', 'yahoo': 'Yahoo Finance', 'techcrunch': 'TechCrunch'}
        found_pub = "Financial News"
        for key, name in mapping.items():
            if key in text:
                found_pub = name
                break
    logo = ""
    for key, l in PUBLISHER_LOGOS.items():
        if key in found_pub.lower() or key in text:
            logo = l
            break
    if not logo:
        logo = "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=800&auto=format&fit=crop"
    return found_pub, logo

def is_valid_article(title, url):
    """유료 기사 및 불량 도메인을 필터링합니다."""
    # 1. 도메인 블랙리스트 체크
    for domain in BLACKLIST_DOMAINS:
        if domain in url.lower():
            return False
    
    # 2. 유료 키워드 체크
    for kw in PAYWALL_KEYWORDS:
        if kw in title:
            return False
            
    return True

def fetch_all_entries(category, feed_urls):
    all_entries = []
    seen_titles = set()
    for url in feed_urls:
        try:
            print(f"  [Fetch] {url}")
            resp = requests.get(url, headers=HEADERS, timeout=10)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:20]:
                title = (entry.get('title') or '').strip()
                link = entry.get('link', '#')
                
                # 유효성 검사 (블랙리스트 및 유료 필터링)
                if not is_valid_article(title, link):
                    continue
                    
                if not title or title in seen_titles: continue
                seen_titles.add(title)
                all_entries.append({'_entry': entry, '_date': parse_date(entry), '_title': title, '_link': link})
        except Exception as e: print(f"  [Error] {e}")
    all_entries.sort(key=lambda x: x['_date'], reverse=True)
    return all_entries[:40]

def build_articles(entries, category, translator):
    articles = []
    for e in entries:
        original_title = e['_title']
        publisher, logo = get_publisher_info(e['_entry'], e['_link'], original_title)
        title = re.sub(r'\s*[-|]\s*[^[-|]*$', '', original_title).strip()
        summary = clean_text(getattr(e['_entry'], 'summary', '') or getattr(e['_entry'], 'description', ''))
        if not re.search('[가-힣]', title):
            try: 
                title = translator.translate(title) or title
                if summary: summary = translator.translate(summary[:300]) or summary
            except: pass
        image = extract_image(e['_entry'])
        if not image or 'googleusercontent' in image: image = logo
        articles.append({
            'title': title, 'summary': summary[:200], 'link': e['_link'],
            'date': e['_date'].strftime('%m.%d %H:%M'), 'image': image, 'publisher': publisher
        })
    return articles

def fetch_news():
    all_data = { 'categories': {}, 'last_updated': '' }
    translator = GoogleTranslator(source='auto', target='ko')
    for category, urls in FEEDS.items():
        print(f"\n[{category}] Processing...")
        entries = fetch_all_entries(category, urls)
        all_data['categories'][category] = build_articles(entries, category, translator)
        print(f"[{category}] Saved {len(all_data['categories'][category])} items.")
    kst = timezone(timedelta(hours=9))
    all_data['last_updated'] = datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S KST')
    return all_data

if __name__ == "__main__":
    start = datetime.now()
    print("=== H_NEWS Stock Scraper Starting ===")
    news_data = fetch_news()
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(f"const newsData = {json.dumps(news_data, ensure_ascii=False, indent=4)};")
    print(f"\n=== Done! ({datetime.now() - start}) ===\n")
