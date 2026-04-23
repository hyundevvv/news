import feedparser
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from deep_translator import GoogleTranslator
import time

# 뉴스 소스 설정 (안정적인 피드 주소로 재검토)
FEEDS = {
    'KR': "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko",
    'US': "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
    'JP': "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ja&gl=JP&ceid=JP:ja"
}

def get_real_image(url):
    """기사 페이지에서 최선의 이미지를 찾아냅니다."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    try:
        # 1. 기사 페이지 접속 (리다이렉션 포함)
        response = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. 우선순위에 따른 이미지 추출
        # og:image -> twitter:image -> 첫 번째 고해상도 img
        img_meta = soup.find('meta', property='og:image') or soup.find('meta', name='twitter:image')
        if img_meta and img_meta.get('content'):
            img_url = img_meta['content']
            if img_url.startswith('//'): img_url = 'https:' + img_url
            return img_url
            
        # 메타데이터 없을 시 본문 내 큰 이미지 탐색
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and ('.jpg' in src or '.png' in src or 'jpeg' in src):
                if src.startswith('//'): src = 'https:' + src
                elif src.startswith('/'): continue # 상대경로는 복잡하므로 패스
                return src
                
    except Exception as e:
        print(f"Image Error ({url[:30]}...): {e}")
    return None

def fetch_news():
    all_data = {}
    headers = {'User-Agent': 'Mozilla/5.0'}
    translator = GoogleTranslator(source='auto', target='ko')

    for country, url in FEEDS.items():
        print(f"[{country}] Processing...")
        articles = []
        try:
            # RSS 가져오기
            resp = requests.get(url, headers=headers, timeout=15)
            feed = feedparser.parse(resp.content)
            
            if not feed.entries:
                print(f"[{country}] No entries found! Check URL or blocking.")
                # 구글 뉴스 차단 대비 대안 주소 시도 (KR인 경우)
                if country == 'KR':
                    print(f"[{country}] Trying alternative KR feed...")
                    alt_url = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtdHZHZ0pKVGlnQVAB?hl=ko&gl=KR&ceid=KR:ko"
                    resp = requests.get(alt_url, headers=headers, timeout=15)
                    feed = feedparser.parse(resp.content)

            for entry in feed.entries[:8]:
                link = entry.link
                title = entry.title.split(' - ')[0]
                
                # 번역
                if country != 'KR':
                    try: title = translator.translate(title)
                    except: pass
                
                # 이미지 추출 (실패 시 우주 배경)
                image = get_real_image(link)
                if not image:
                    image = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop"

                articles.append({
                    'title': title,
                    'link': link,
                    'date': getattr(entry, 'published', datetime.now().strftime('%Y-%m-%d')),
                    'image': image
                })
                time.sleep(0.5) # 과도한 요청 방지
                
        except Exception as e:
            print(f"[{country}] Error: {e}")
            
        all_data[country] = articles
    return all_data

if __name__ == "__main__":
    start = datetime.now()
    news_data = fetch_news()
    
    # 데이터 강제 검증 (비어있으면 더미 데이터라도 삽입)
    for c in FEEDS.keys():
        if not news_data.get(c):
            news_data[c] = [{
                "title": f"[{c}] 뉴스를 동기화할 수 없습니다. 잠시 후 다시 시도하세요.",
                "link": "https://news.google.com",
                "date": datetime.now().strftime('%Y-%m-%d'),
                "image": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop"
            }]

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(news_data, f, ensure_ascii=False, indent=4)
    print(f"Finished! Time: {datetime.now() - start}")
