import feedparser
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 뉴스 소스 설정
FEEDS = {
    'KR': "https://news.naver.com/rss/main_section105.xml",
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
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                return img_url
    except Exception as e:
        print(f"Image fetch error for {url}: {e}")
    return "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop"

def fetch_news():
    all_data = {}
    # RSS 요청 시에도 헤더 추가하여 블로킹 방지
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    for country, url in FEEDS.items():
        print(f"[{country}] Fetching news and thumbnails...")
        articles = []
        try:
            # feedparser.parse(url) 대신 requests로 먼저 가져오기
            response = requests.get(url, headers=headers, timeout=15)
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                print(f"[{country}] No entries found in feed.")

            for entry in feed.entries[:8]:
                link = entry.link
                image_url = get_og_image(link)
                
                articles.append({
                    'title': entry.title,
                    'link': link,
                    'date': getattr(entry, 'published', datetime.now().strftime('%Y-%m-%d')),
                    'image': image_url
                })
        except Exception as e:
            print(f"[{country}] Critical error: {e}")
            
        all_data[country] = articles
    return all_data

if __name__ == "__main__":
    start_time = datetime.now()
    news_data = fetch_news()
    
    # KR이 비어있을 경우 로그 남기기
    if not news_data.get('KR'):
        print("ALERT: KR news data is still empty!")

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(news_data, f, ensure_ascii=False, indent=4)
    print(f"Completed! Duration: {datetime.now() - start_time}")
