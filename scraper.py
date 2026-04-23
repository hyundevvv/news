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

PUBLISHER_LOGOS = {
    '연합뉴스': "https://www.yonhapnewstv.co.kr/static/images/common/logo.png",
    '매일경제': "https://www.mk.co.kr/static/common/img/mk_logo.png",
    '한국경제': "https://www.hankyung.com/img/common/hankyung_logo.png",
    '전자신문': "https://www.etnews.com/etnews/images/common/logo.png",
    'bbc': "https://navis.bbci.co.uk/news-app/assets/apple-touch-icon-180x180.png",
    'nyt': "https://static01.nyt.com/images/icons/t_logo_291_black.png",
    'techcrunch': "https://techcrunch.com/wp-content/uploads/2015/02/cropped-tc-favicon-lg.png",
    'the verge': "https://cdn.vox-cdn.com/uploads/chorus_asset/asset/24011409/verge_logo_icon_color_2022.png",
    'the guardian': "https://assets.guim.co.uk/images/favicons/023dafadbf5ef53e0865e4ba8a834547/114x114.png",
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

def get_publisher_name(entry, url):
    if hasattr(entry, 'source') and 'title' in entry.source:
        return entry.source.title
    low_url = url.lower()
    mapping = {'bbc': 'BBC News', 'nytimes': 'NYT', 'mk.co.kr': '매일경제', 'hankyung': '한국경제', 'etnews': '전자신문', 'yonhap': '연합뉴스TV', 'techcrunch': 'TechCrunch', 'theverge': 'The Verge', 'guardian': 'The Guardian', 'yahoo': 'Yahoo Finance'}
    for key, name in mapping.items():
        if key in low_url: return name
    return "Global News"

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
        raw_title = e['_title']
        publisher = get_publisher_name(e['_entry'], e['_link'])
        title = re.sub(r'\s*[-|]\s*[^[-|]*$', '', raw_title).strip()
        
        # 기사 요약 및 작성자 추출
        summary = clean_text(getattr(e['_entry'], 'summary', '') or getattr(e['_entry'], 'description', ''))
        author = getattr(e['_entry'], 'author', '') or getattr(e['_entry'], 'dc_creator', '')
        
        # 번역
        if not re.search('[가-힣]', title):
            try: 
                title = translator.translate(title) or title
                if summary: summary = translator.translate(summary[:300]) or summary
            except: pass
        
        image = extract_image(e['_entry'])
        if not image or 'googleusercontent' in image:
            image = PUBLISHER_LOGOS.get(publisher.lower().split()[0], "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=800&auto=format&fit=crop")

        articles.append({
            'title': title,
            'summary': summary[:200], # 최대 200자
            'author': author,
            'link': e['_link'],
            'date': e['_date'].strftime('%m.%d %H:%M'),
            'image': image,
            'publisher': publisher
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
    print(f"\n=== Done! ({datetime.now() - start}) ===\n")
