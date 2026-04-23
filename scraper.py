import feedparser
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from deep_translator import GoogleTranslator
import time
import re
from email.utils import parsedate_to_datetime

# ─────────────────────────────────────────────────────────────────
# 최종 검증된 안정적 RSS 피드 목록 (봇 차단 없음 확인)
# ─────────────────────────────────────────────────────────────────
FEEDS = {
    'TOP': [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "https://www.yonhapnewstv.co.kr/browse/feed/",
        "https://www.theguardian.com/world/rss"
    ],
    'FINANCE': [
        "https://finance.yahoo.com/news/rssindex",
        "https://www.mk.co.kr/rss/30100041/", # 매일경제 경제
        "https://www.hankyung.com/feed/economy", # 한국경제 경제 (최신 주소)
        "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko"
    ],
    'TECH': [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "http://rss.etnews.com/03.xml", # 전자신문 IT (최강 안정성)
        "https://www.hankyung.com/feed/it" # 한국경제 IT
    ]
}

DEFAULT_IMAGES = {
    'TOP':     "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop",
    'FINANCE': "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=800&auto=format&fit=crop",
    'TECH':    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=800&auto=format&fit=crop",
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def parse_date(entry):
    dt = None
    for attr in ['published', 'updated', 'created']:
        raw = getattr(entry, attr, None)
        if raw:
            try:
                dt = parsedate_to_datetime(raw)
                break
            except:
                pass
    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def extract_image(entry):
    # 1. media:content / media:thumbnail
    if hasattr(entry, 'media_content') and entry.media_content:
        url = entry.media_content[0].get('url', '')
        if url: return url
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        url = entry.media_thumbnail[0].get('url', '')
        if url: return url

    # 2. summary/description HTML 파싱
    for field in ['summary', 'description']:
        val = getattr(entry, field, '') or ''
        if val:
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', val)
            if match:
                src = match.group(1)
                if src.startswith('//'): src = 'https:' + src
                return src
    return None

def fetch_all_entries(category, feed_urls):
    all_entries = []
    seen_titles = set()

    for url in feed_urls:
        try:
            print(f"  [Fetch] {url}")
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)

            if not feed.entries:
                print(f"  [Skip] No entries")
                continue

            for entry in feed.entries[:7]:
                title = (entry.get('title') or '').strip()
                if not title or title in seen_titles: continue
                seen_titles.add(title)

                all_entries.append({
                    '_entry': entry,
                    '_date': parse_date(entry),
                    '_title': title,
                    '_link': entry.get('link', '#'),
                })
        except Exception as e:
            print(f"  [Error] {e}")
    
    all_entries.sort(key=lambda x: x['_date'], reverse=True)
    return all_entries[:12]

def build_articles(entries, category, translator):
    articles = []
    for e in entries:
        title = e['_title']
        # 언론사 태그 제거 (뒤쪽의 하이픈이나 파이프 뒤 텍스트 제거)
        title = re.sub(r'\s*[-|]\s*[^[-|]*$', '', title).strip()

        # 한국어 번역 (한글 미포함 시)
        if not re.search('[가-힣]', title):
            try:
                title = translator.translate(title) or title
            except:
                pass

        image = extract_image(e['_entry']) or DEFAULT_IMAGES[category]
        date_str = e['_date'].strftime('%m.%d %H:%M')

        articles.append({
            'title': title,
            'link': e['_link'],
            'date': date_str,
            'image': image
        })
    return articles

def fetch_news():
    all_data = {}
    translator = GoogleTranslator(source='auto', target='ko')

    for category, urls in FEEDS.items():
        print(f"\n[{category}] Processing...")
        entries = fetch_all_entries(category, urls)
        all_data[category] = build_articles(entries, category, translator)
        print(f"[{category}] Saved {len(all_data[category])} items.")

    return all_data

if __name__ == "__main__":
    start = datetime.now()
    print("=== H_NEWS Final Scraper Starting ===")
    news_data = fetch_news()

    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(f"const newsData = {json.dumps(news_data, ensure_ascii=False, indent=4)};")

    print(f"\n=== Done! ({datetime.now() - start}) ===")
