# SquadWatch: Football Data Quality Assurance (QA)

## Overview
A QA assistant for ensuring data correctness of footballtransfers.com, now enhanced with RSS news processing capabilities for comprehensive squad validation.

## Features

### 1. FootballTransfers.com Data Scraping
- Scrapes squad information from footballtransfers.com
- Stores data in timestamped snapshots
- Creates FAISS vector database for squad embeddings

### 2. RSS News Processing (NEW)
- Fetches football news from multiple RSS feeds
- Extracts squad and transfer information using NLP
- Compares news data with existing footballtransfers data
- Generates discrepancy reports in JSON format

## Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Configuration
Create a `.env` file:
```
TEAMS_TO_CHECK_JSON=/path/to/your/teams.json
OPENAI_API_KEY=your_openai_key_here  # Optional, for embeddings
```

### Usage

#### 1. Refresh FootballTransfers Data
```bash
python refresh-ft.py
```

#### 2. Process RSS News and Compare
```bash
python process_news.py
```

#### 3. Index Squad Data
```bash
python main.py
```

#### 4. Test Components
```bash
python test_news.py
```

## RSS News Processing Pipeline

The RSS news processor follows this workflow:

1. **Fetch News**: Retrieves articles from football RSS feeds
2. **Filter Relevance**: Identifies squad/transfer-related articles
3. **Parse Information**: Extracts player names, transfers, contracts
4. **Compare Data**: Matches against footballtransfers.com data
5. **Generate Reports**: Creates JSON discrepancy reports
6. **Create Index**: Builds FAISS embeddings for news data

### Supported RSS Sources
- Sky Sports Football
- BBC Sport Football
- ESPN Soccer
- TalkSport Football
- Goal.com

## Output Structure

### Discrepancy Reports
Generated in `data/comparisons/discrepancies_TIMESTAMP.json`:

```json
{
  "comparison_date": "2024-01-15T10:30:00Z",
  "teams_compared": 5,
  "discrepancies_found": 2,
  "teams": {
    "liverpool": {
      "footballtransfers_team": "liverpool",
      "discrepancies": {
        "missing_in_ft": ["João Silva"],
        "missing_in_news": ["Jordan Henderson"],
        "fuzzy_matches": [...],
        "news_context": {...}
      },
      "news_transfers": [...]
    }
  }
}
```

### News Data Storage
- Raw articles: `data/news/TIMESTAMP/articles.json`
- Processed data: `data/news/TIMESTAMP/squad_info.json`
- FAISS index: `data/index/news_faiss_index/`

## Architecture

```
squadwatch/
├── footballtransfers/          # Original FT.com scraping
│   ├── scrapers/
│   └── persistence.py
├── news/                       # NEW: RSS news processing
│   ├── rss_scraper.py         # Fetch RSS feeds
│   ├── parser.py              # Extract squad info
│   ├── persistence.py         # Save and index news
│   └── comparator.py          # Compare with FT data
├── main.py                     # Original FAISS indexing
├── process_news.py            # NEW: RSS pipeline entry point
└── test_news.py               # NEW: Test suite
```

## Key Objectives Achieved

- ✅ **Squad Lists**: Extract correct squad lists per team from RSS news
- ✅ **Transfer Tracking**: Identify confirmed transfers and contract end dates
- ✅ **Data Comparison**: Compare RSS data with footballtransfers.com
- ✅ **Discrepancy Reporting**: Generate JSON reports of differences
- ✅ **RAG Integration**: Store news in FAISS for semantic search
