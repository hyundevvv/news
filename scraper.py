import feedparser
import json
import os
import re
from datetime import datetime

# RSS Feed URL (Google News - Technology - South Korea)
RSS_URL = "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko"

def fetch_news():
    feed = feedparser.parse(RSS_URL)
    articles = []
    
    # Extract top 10 articles
    for entry in feed.entries[:10]:
        # Google News RSS usually doesn't provide images directly.
        # For a premium look, we'll try to find a source image or use a high-quality placeholder 
        # from a space-themed collection if none is found.
        # But per requirements, let's try to extract if available.
        
        image_url = "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1000&auto=format&fit=crop" # Default Space Image
        
        # Simple extraction for some RSS feeds that might have media:content
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
            'category': 'Technology',
            'date': entry.published,
            'image': image_url
        })
    
    return articles

def save_to_json(data):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    print(f"[{datetime.now()}] Fetching news...")
    news_data = fetch_news()
    save_to_json(news_data)
    print(f"[{datetime.now()}] Successfully saved {len(news_data)} articles to data.json")
