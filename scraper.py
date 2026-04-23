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
# 최종 검증된 안정적 RSS 피드 목록
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
        "https://www.mk.co.kr/rss/30100041/", 
        "https://www.hankyung.com/feed/economy",
        "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko"
    ],
    'TECH': [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "http://rss.etnews.com/03.xml", 
        "https://www.hankyung.com/feed/it"
    ]
}

# 언론사별 로고 매핑
PUBLISHER_LOGOS = {
    '연합뉴스': "https://www.yonhapnewstv.co.kr/static/images/common/logo.png",
    '매일경제': "https://www.mk.co.kr/static/common/img/mk_logo.png",
    '한국경제': "https://www.hankyung.com/img/common/hankyung_logo.png",
    '전자신문': "https://www.etnews.com/etnews/images/common/logo.png",
    'bbc': "https://navis.bbci.co.uk/news-app/assets/apple-touch-icon-180x180.png",
    'nyt': "https://static01.nyt.com/images/icons/t_logo_291_black.png",
    'techcrunch': "https://techcrunch.com/wp-content/uploads/2015/02/cropped-tc-favicon-lg.png",
    'verge': "https://cdn.vox-cdn.com/uploads/chorus_asset/asset/24011409/verge_logo_icon_color_2022.png",
    'guardian': "https://assets.guim.co.uk/images/favicons/023dafadbf5ef53e0865e4ba8a834547/114x114.png",
    'yahoo': "https://s.yimg.com/cv/apiv2/myy/yahoo_logo_v3.png"
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

def get_publisher_info(url, original_title):
    text = (url + " " + original_title).lower()
    mapping = {
        '연합뉴스': '연합뉴스', '매일경제': '매일경제', '한국경제': '한국경제', '전자신문': '전자신문',
        'bbc': 'BBC News', 'nyt': 'NYT', 'techcrunch': 'TechCrunch', 'verge': 'The Verge',
        'guardian': 'The Guardian', 'yahoo': 'Yahoo Finance'
    }
    found_pub = "Global News"
    for key, name in mapping.items():
        if key in text:
            found_pub = name
            break
    logo = PUBLISHER_LOGOS.get(found_pub.lower().split()[0], PUBLISHER_LOGOS.get(found_pub, ''))
    if not logo:
        # 키워드 매칭 실패시 개별 언론사 로직
        if '연합' in found_pub: logo = PUBLISHER_LOGOS['연합뉴스']
        elif 'finance' in found_pub.lower(): logo = PUBLISHER_LOGOS['yahoo']
        else: logo = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop"
    return found_pub, logo

def fetch_all_entries(category, feed_urls):
    all_entries = []
    seen_titles = set()
    for url in feed_urls:
        try:
            print(f"  [Fetch] {url}")
            resp = requests.get(url, headers=HEADERS, timeout=10)
            feed = feedparser.parse(resp.content)
            for entry in feed.entries[:15]:
                title = (entry.get('title') or '').strip()
                if not title or title in seen_titles: continue
                seen_titles.add(title)
                all_entries.append({'_entry': entry, '_date': parse_date(entry), '_title': title, '_link': entry.get('link', '#')})
        except Exception as e: print(f"  [Error] {e}")
    all_entries.sort(key=lambda x: x['_date'], reverse=True)
    return all_entries[:40]

def build_articles(entries, category, translator):
    articles = []
    for e in entries:
        original_title = e['_title']
        publisher, logo = get_publisher_info(e['_link'], original_title)
        title = re.sub(r'\s*[-|]\s*[^[-|]*$', '', original_title).strip()
        if not re.search('[가-힣]', title):
            try: title = translator.translate(title) or title
            except: pass
        image = extract_image(e['_entry'])
        if not image or 'googleusercontent' in image: image = logo
        articles.append({
            'title': title, 'link': e['_link'], 'date': e['_date'].strftime('%m.%d %H:%M'),
            'image': image, 'publisher': publisher
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
    print("=== H_NEWS Scraper Starting ===")
    news_data = fetch_news()
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(f"const newsData = {json.dumps(news_data, ensure_ascii=False, indent=4)};")
    print(f"\n=== Done! ({datetime.now() - start}) ===")
