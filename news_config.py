# RSS News Configuration

# RSS feed URLs for football news
FOOTBALL_RSS_FEEDS = [
    "https://www.skysports.com/rss/football",
    "https://feeds.bbci.co.uk/sport/football/rss.xml", 
    "https://www.espn.com/espn/rss/soccer/news",
    "https://talksport.com/football/rss/",
    "https://www.goal.com/feeds/en/news"
]

# Processing parameters
DEFAULT_DAYS_BACK = 7  # How many days back to fetch news
MAX_ARTICLES_PER_FEED = 30  # Max articles per RSS feed
SIMILARITY_THRESHOLD = 0.7  # Player name similarity threshold for matching

# Output directories
NEWS_DATA_DIR = "./data/news"
COMPARISONS_DIR = "./data/comparisons"
NEWS_INDEX_DIR = "./data/index/news_faiss_index"

# Team name mappings (RSS format -> FootballTransfers format)
TEAM_MAPPINGS = {
    "manchester_united": "manchester-united",
    "manchester_city": "manchester-city",
    "liverpool": "liverpool", 
    "chelsea": "chelsea",
    "arsenal": "arsenal",
    "tottenham": "tottenham",
    "barcelona": "barcelona",
    "real_madrid": "real-madrid",
    "bayern_munich": "bayern-munich",
    "psg": "paris-saint-germain"
}

# Keywords for filtering squad-related news
SQUAD_KEYWORDS = [
    'transfer', 'transfers', 'signing', 'signed', 'contract', 'deal',
    'squad', 'lineup', 'team news', 'roster', 'player', 'joins',
    'leaves', 'departure', 'arrival', 'move', 'agreement', 'fee',
    'loan', 'free agent', 'release', 'extend', 'renewal', 'injury',
    'return', 'debut', 'confirmed', 'official', 'announces'
]