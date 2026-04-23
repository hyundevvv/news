import feedparser
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 뉴스 소스 설정
FEEDS = {
    'KR': "https://news.naver.com/rss/main_section105.xml", # 네이버 IT/과학
    'US': "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
    'JP': "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ja&gl=JP&ceid=JP:ja"
}

def get_og_image(url):
    """기사 링크에서 대표 이미지(og:image)를 추출합니다."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                img_url = og_image['content']
                # 상대 경로 처리
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                return img_url
    except Exception as e:
        print(f"Image fetch error for {url}: {e}")
    return "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop"

def fetch_news():
    all_data = {}
    for country, url in FEEDS.items():
        print(f"[{country}] Fetching news and thumbnails...")
        feed = feedparser.parse(url)
        articles = []
        
        # 속도를 위해 8개로 제한
        for entry in feed.entries[:8]:
            link = entry.link
            image_url = get_og_image(link)
            
            # 제목 정제 (네이버 뉴스의 경우 대괄호 등 제거 가능)
            title = entry.title
            
            articles.append({
                'title': title,
                'link': link,
                'date': entry.published,
                'image': image_url
            })
        all_data[country] = articles
    return all_data

if __name__ == "__main__":
    start_time = datetime.now()
    news_data = fetch_news()
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(news_data, f, ensure_ascii=False, indent=4)
    print(f"Completed! Duration: {datetime.now() - start_time}")
