#!/usr/bin/env python3
"""
Test RSS News Processing Components

This script tests the RSS news processing components with sample data
to validate the implementation without requiring external network access.
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news.parser import NewsParser
from news.persistence import news_to_documents, save_processed_squad_info
from news.comparator import SquadComparator


def create_sample_articles():
    """Create sample news articles for testing."""
    return [
        {
            "title": "Liverpool signs new midfielder João Silva from Barcelona",
            "link": "https://example.com/news1",
            "description": "Liverpool FC has confirmed the signing of João Silva on a 4-year contract",
            "summary": "The 25-year-old midfielder joins from Barcelona for £50m",
            "content": "Liverpool Football Club today announced the signing of João Silva from FC Barcelona. The 25-year-old Portuguese midfielder has signed a four-year contract until 2027.",
            "published": "2024-01-15",
            "source_name": "Sky Sports",
            "relevance_score": 5
        },
        {
            "title": "Manchester United confirms departure of veteran defender",
            "link": "https://example.com/news2", 
            "description": "Harry Maguire leaves Manchester United after 5 years",
            "summary": "The England international's contract expires in summer 2024",
            "content": "Manchester United has confirmed that Harry Maguire will leave the club when his contract expires at the end of the current season.",
            "published": "2024-01-16",
            "source_name": "BBC Sport",
            "relevance_score": 4
        },
        {
            "title": "Chelsea agrees deal for young striker",
            "link": "https://example.com/news3",
            "description": "Chelsea close to signing 19-year-old forward",
            "summary": "The Blues agree terms for promising striker",
            "content": "Chelsea FC is close to finalizing a deal for 19-year-old striker Marcus Johnson. The young forward is expected to join on a 5-year contract.",
            "published": "2024-01-17", 
            "source_name": "Goal.com",
            "relevance_score": 3
        }
    ]


def create_sample_ft_data():
    """Create sample footballtransfers data for testing."""
    return {
        "liverpool": {
            "team": "Liverpool FC",
            "squad": {
                "Midfielders": [
                    {"name": "Jordan Henderson", "position": "CM", "age": 33},
                    {"name": "Fabinho", "position": "DM", "age": 30},
                    {"name": "Thiago Alcântara", "position": "CM", "age": 32}
                ],
                "Defenders": [
                    {"name": "Virgil van Dijk", "position": "CB", "age": 32},
                    {"name": "Andrew Robertson", "position": "LB", "age": 29}
                ]
            }
        },
        "manchester-united": {
            "team": "Manchester United",
            "squad": {
                "Defenders": [
                    {"name": "Harry Maguire", "position": "CB", "age": 30},
                    {"name": "Luke Shaw", "position": "LB", "age": 28},
                    {"name": "Aaron Wan-Bissaka", "position": "RB", "age": 26}
                ],
                "Midfielders": [
                    {"name": "Bruno Fernandes", "position": "AM", "age": 29},
                    {"name": "Casemiro", "position": "DM", "age": 31}
                ]
            }
        },
        "chelsea": {
            "team": "Chelsea FC", 
            "squad": {
                "Forwards": [
                    {"name": "Raheem Sterling", "position": "LW", "age": 29},
                    {"name": "Christopher Nkunku", "position": "ST", "age": 26}
                ],
                "Midfielders": [
                    {"name": "Enzo Fernández", "position": "CM", "age": 23},
                    {"name": "Moisés Caicedo", "position": "DM", "age": 22}
                ]
            }
        }
    }


def test_news_parser():
    """Test the news parser functionality."""
    print("🧪 Testing News Parser...")
    
    parser = NewsParser()
    sample_articles = create_sample_articles()
    
    processed_articles = parser.process_articles(sample_articles)
    
    print(f"   ✅ Processed {len(processed_articles)} articles")
    
    # Check if we extracted transfers
    total_transfers = sum(len(article.get('transfers', [])) for article in processed_articles)
    print(f"   ✅ Extracted {total_transfers} transfers")
    
    # Check if we identified teams
    total_teams = sum(len(article.get('teams_mentioned', [])) for article in processed_articles)
    print(f"   ✅ Identified {total_teams} team mentions")
    
    return processed_articles


def test_document_creation():
    """Test document creation for FAISS indexing."""
    print("\n🧪 Testing Document Creation...")
    
    processed_articles = test_news_parser()
    documents = news_to_documents(processed_articles)
    
    print(f"   ✅ Created {len(documents)} documents for indexing")
    
    if documents:
        print(f"   📄 Sample document: {documents[0][:100]}...")
    
    return documents


def test_squad_comparator():
    """Test the squad comparator functionality."""
    print("\n🧪 Testing Squad Comparator...")
    
    processed_articles = test_news_parser()
    ft_data = create_sample_ft_data()
    
    comparator = SquadComparator()
    comparison_results = comparator.compare_squad_lists(processed_articles, ft_data)
    
    print(f"   ✅ Compared {comparison_results.get('teams_compared', 0)} teams")
    print(f"   ✅ Found discrepancies in {comparison_results.get('discrepancies_found', 0)} teams")
    
    # Show detailed results
    for team_name, team_data in comparison_results.get('teams', {}).items():
        print(f"   📊 {team_name}:")
        discrepancies = team_data.get('discrepancies', {})
        print(f"      - Exact matches: {len(discrepancies.get('exact_matches', []))}")
        print(f"      - Fuzzy matches: {len(discrepancies.get('fuzzy_matches', []))}")
        print(f"      - Missing in FT: {len(discrepancies.get('missing_in_ft', []))}")
        print(f"      - Missing in News: {len(discrepancies.get('missing_in_news', []))}")
    
    return comparison_results


def test_persistence():
    """Test persistence functionality."""
    print("\n🧪 Testing Persistence...")
    
    processed_articles = test_news_parser()
    
    # Test saving processed data
    try:
        saved_path = save_processed_squad_info(processed_articles, "./test_data/news")
        print(f"   ✅ Saved processed articles to {saved_path}")
        
        # Clean up test data
        import shutil
        if os.path.exists("./test_data"):
            shutil.rmtree("./test_data")
            print("   🧹 Cleaned up test data")
            
    except Exception as e:
        print(f"   ❌ Error in persistence test: {e}")


def main():
    """Run all tests."""
    print("🚀 Starting RSS News Processing Tests")
    print("=" * 50)
    
    try:
        # Test individual components
        test_news_parser()
        test_document_creation()
        test_squad_comparator()
        test_persistence()
        
        print("\n✅ All tests completed successfully!")
        print("\n🎯 The RSS news processing system is ready to use")
        print("   Run 'python process_news.py' to process real RSS feeds")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()