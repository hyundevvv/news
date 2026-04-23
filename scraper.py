import feedparser
import json
import os
from datetime import datetime

# 국가별 RSS 피드 설정 (Google News Tech)
FEEDS = {
    'KR': "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko",
    'US': "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
    'JP': "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ja&gl=JP&ceid=JP:ja"
}

def fetch_news():
    all_data = {}
    for country, url in FEEDS.items():
        print(f"Fetching news for {country}...")
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:10]:
            # 기본 우주 테마 이미지
            image_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop"
            
            # RSS 내부 미디어 링크 탐색 시도
            if 'media_content' in entry:
                image_url = entry.media_content[0]['url']
            elif 'links' in entry:
                for link in entry.links:
                    if 'image' in link.get('type', ''):
                        image_url = link.get('href')
                        break
            
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'date': entry.published,
                'image': image_url
            })
        all_data[country] = articles
    return all_data

if __name__ == "__main__":
    print(f"[{datetime.now()}] Multi-region scraper started...")
    news_data = fetch_news()
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(news_data, f, ensure_ascii=False, indent=4)
    print(f"[{datetime.now()}] Data saved successfully.")
