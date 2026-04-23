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
# 주제별 RSS 피드 목록 (이미지 직접 제공 or 파싱 가능한 소스 중심)
# ─────────────────────────────────────────────────────────────────
FEEDS = {
    'TOP': [
        # 글로벌 주요 뉴스 (중요도 높은 소스 우선)
        "https://feeds.reuters.com/reuters/topNews",
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        # 한국 주요 (연합뉴스)
        "https://www.yonhapnewstv.co.kr/browse/feed/",
    ],
    'FINANCE': [
        # 글로벌 금융·주식
        "https://feeds.reuters.com/reuters/businessNews",
        "https://feeds.reuters.com/reuters/technologyNews",
        "https://finance.yahoo.com/news/rssindex",
        # 한국 경제
        "https://rss.hankyung.com/economy.rss",
        "https://rss.edaily.co.kr/RSS/Section/rss_main.xml",
        # Bloomberg (공개 피드)
        "https://feeds.bloomberg.com/markets/news.rss",
    ],
    'TECH': [
        # 글로벌 기술
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/index",
        # 한국 IT
        "https://www.zdnet.co.kr/rss/news/",
        "https://www.etnews.com/etnews/rss/section/",
    ]
}

DEFAULT_IMAGES = {
    'TOP':     "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop",
    'FINANCE': "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?q=80&w=800&auto=format&fit=crop",
    'TECH':    "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=800&auto=format&fit=crop",
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*'
}

def parse_date(entry):
    """RSS entry의 날짜를 datetime 객체로 변환합니다."""
    for attr in ['published', 'updated', 'created']:
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return parsedate_to_datetime(raw)
            except:
                try:
                    return datetime.fromisoformat(raw.replace('Z', '+00:00'))
                except:
                    pass
    return datetime.now(timezone.utc)

def extract_image(entry):
    """RSS entry에서 이미지 URL을 추출합니다."""
    # 1. media:content
    if hasattr(entry, 'media_content') and entry.media_content:
        for m in entry.media_content:
            url = m.get('url', '')
            if url and re.search(r'\.(jpg|jpeg|png|webp)', url, re.I):
                return url

    # 2. media:thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        url = entry.media_thumbnail[0].get('url', '')
        if url: return url

    # 3. enclosures
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if 'image' in enc.get('type', ''):
                return enc.get('href') or enc.get('url', '')

    # 4. summary/description HTML의 img 태그
    for field in ['summary', 'description']:
        val = getattr(entry, field, '') or ''
        if val:
            soup = BeautifulSoup(val, 'html.parser')
            img = soup.find('img')
            if img:
                src = img.get('src') or img.get('data-src', '')
                if src:
                    if src.startswith('//'): src = 'https:' + src
                    if src.startswith('http') and re.search(r'\.(jpg|jpeg|png|webp)', src, re.I):
                        return src

    return None

def fetch_all_entries(category, feed_urls):
    """여러 피드에서 기사를 수집하고 날짜순으로 정렬합니다."""
    all_entries = []
    seen_titles = set()

    for url in feed_urls:
        try:
            print(f"  [Fetch] {url[:55]}...")
            resp = requests.get(url, headers=HEADERS, timeout=12)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)

            if not feed.entries:
                print(f"  [Skip] No entries")
                continue

            print(f"  [OK] {len(feed.entries)} entries")
            for entry in feed.entries[:5]: # 피드당 최대 5개
                title = (entry.get('title') or '').strip()
                # 중복 제거 (제목 앞 20자 기준)
                key = re.sub(r'\W', '', title[:20].lower())
                if key in seen_titles or not title:
                    continue
                seen_titles.add(key)

                all_entries.append({
                    '_entry': entry,
                    '_date': parse_date(entry),
                    '_title': title,
                    '_link': entry.get('link', '#'),
                })

        except Exception as e:
            print(f"  [Error] {url[:40]}: {e}")
        time.sleep(0.3)

    # 최신순 정렬
    all_entries.sort(key=lambda x: x['_date'], reverse=True)
    return all_entries[:10] # 상위 10개만

def build_articles(entries, category, translator):
    """정렬된 entry 목록을 최종 기사 객체로 변환합니다."""
    articles = []
    for e in entries:
        title = e['_title']
        # 언론사 이름 제거 (` - Reuters`, ` | BBC News` 등)
        title = re.sub(r'\s*[-|]\s*(Reuters|BBC|Bloomberg|NYT|TechCrunch|The Verge)[^\-|]*$', '', title).strip() or title

        # 한국어 번역 (이미 한국어인 경우 스킵)
        if not any('\uAC00' <= c <= '\uD7A3' for c in title):
            try:
                title = translator.translate(title) or title
            except Exception as ex:
                print(f"  [Translate Error] {ex}")

        image = extract_image(e['_entry']) or DEFAULT_IMAGES[category]
        date_str = e['_date'].strftime('%a, %d %b %Y %H:%M:%S GMT')

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
        print(f"\n=== [{category}] Processing ===")
        entries = fetch_all_entries(category, urls)

        if entries:
            articles = build_articles(entries, category, translator)
        else:
            print(f"[{category}] All feeds failed. Using placeholder.")
            articles = [{
                'title': '현재 뉴스를 불러올 수 없습니다.',
                'link': 'https://news.google.com',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'image': DEFAULT_IMAGES[category]
            }]

        all_data[category] = articles
        print(f"[{category}] Saved {len(articles)} articles.")

    return all_data

if __name__ == "__main__":
    start = datetime.now()
    print("=== Anti-Gravity Scraper Starting ===")
    news_data = fetch_news()

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(news_data, f, ensure_ascii=False, indent=4)

    print(f"\n=== Done! ({datetime.now() - start}) ===")
