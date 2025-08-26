import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
from config import HEADERS


# Popular football RSS feeds
FOOTBALL_RSS_FEEDS = [
    "https://www.skysports.com/rss/football",
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.espn.com/espn/rss/soccer/news",
    "https://talksport.com/football/rss/",
    "https://www.goal.com/feeds/en/news",
]


def fetch_rss_feed(feed_url: str, max_entries: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch and parse an RSS feed, returning list of news entries.
    
    Args:
        feed_url: URL of the RSS feed
        max_entries: Maximum number of entries to return
        
    Returns:
        List of dictionaries containing news article data
    """
    try:
        # Use requests with headers to fetch RSS content
        response = requests.get(feed_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Parse RSS content
        feed = feedparser.parse(response.content)
        
        articles = []
        for entry in feed.entries[:max_entries]:
            article = {
                "title": getattr(entry, 'title', ''),
                "link": getattr(entry, 'link', ''),
                "description": getattr(entry, 'description', ''),
                "summary": getattr(entry, 'summary', ''),
                "published": getattr(entry, 'published', ''),
                "published_parsed": getattr(entry, 'published_parsed', None),
                "source_feed": feed_url,
                "source_name": getattr(feed.feed, 'title', feed_url),
            }
            
            # Get the full content if available
            content = ""
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value if isinstance(entry.content, list) else str(entry.content)
            
            article["content"] = content
            articles.append(article)
            
        return articles
        
    except Exception as e:
        print(f"❌ Failed to fetch RSS feed {feed_url}: {e}")
        return []


def fetch_all_football_news(days_back: int = 7, max_per_feed: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch football news from all configured RSS feeds.
    
    Args:
        days_back: Number of days back to consider articles (for filtering)
        max_per_feed: Maximum articles per RSS feed
        
    Returns:
        List of all football news articles
    """
    all_articles = []
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    print(f"📰 Fetching football news from {len(FOOTBALL_RSS_FEEDS)} RSS feeds...")
    
    for feed_url in FOOTBALL_RSS_FEEDS:
        print(f"   → Fetching from {feed_url}")
        articles = fetch_rss_feed(feed_url, max_per_feed)
        
        # Filter by date if possible
        filtered_articles = []
        for article in articles:
            if article.get('published_parsed'):
                try:
                    pub_date = datetime(*article['published_parsed'][:6])
                    if pub_date >= cutoff_date:
                        filtered_articles.append(article)
                except:
                    # If date parsing fails, include the article anyway
                    filtered_articles.append(article)
            else:
                # If no date available, include the article
                filtered_articles.append(article)
        
        all_articles.extend(filtered_articles)
        print(f"     ✅ Found {len(filtered_articles)} recent articles")
    
    print(f"📊 Total articles fetched: {len(all_articles)}")
    return all_articles


def filter_squad_related_news(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter articles that are likely to contain squad or transfer information.
    
    Args:
        articles: List of news articles
        
    Returns:
        Filtered list of squad/transfer related articles
    """
    squad_keywords = [
        'transfer', 'transfers', 'signing', 'signed', 'contract', 'deal',
        'squad', 'lineup', 'team news', 'roster', 'player', 'joins',
        'leaves', 'departure', 'arrival', 'move', 'agreement', 'fee',
        'loan', 'free agent', 'release', 'extend', 'renewal', 'injury',
        'return', 'debut', 'confirmed', 'official', 'announces'
    ]
    
    filtered_articles = []
    
    for article in articles:
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        summary = article.get('summary', '').lower()
        content = article.get('content', '').lower()
        
        # Combine all text fields for searching
        full_text = f"{title} {description} {summary} {content}"
        
        # Check if any squad keywords are present
        if any(keyword in full_text for keyword in squad_keywords):
            article['relevance_score'] = sum(1 for keyword in squad_keywords if keyword in full_text)
            filtered_articles.append(article)
    
    # Sort by relevance score (most relevant first)
    filtered_articles.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    print(f"🎯 Filtered to {len(filtered_articles)} squad/transfer related articles")
    return filtered_articles