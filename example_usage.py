#!/usr/bin/env python3
"""
Example Usage of SquadWatch RSS News Processing

This script demonstrates how to use the RSS news processing system
to fetch football news and compare it with existing squad data.
"""

import os
import sys
import json

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news.rss_scraper import fetch_all_football_news, filter_squad_related_news
from news.parser import NewsParser
from news.comparator import SquadComparator
from news.persistence import save_discrepancies


def example_basic_usage():
    """Example: Basic RSS news processing."""
    print("📰 Example 1: Basic RSS News Processing")
    print("-" * 50)
    
    # Fetch news (this would work with internet access)
    print("Fetching football news from RSS feeds...")
    # articles = fetch_all_football_news(days_back=3, max_per_feed=10)
    
    # For this example, we'll use sample data
    sample_articles = [
        {
            "title": "Manchester City signs new striker for £100m",
            "description": "City completes record deal for prolific goalscorer",
            "content": "Manchester City has completed the signing of Erling Haaland's replacement after a successful medical. The striker signs a 5-year contract.",
            "source_name": "Sky Sports",
            "published": "2024-01-15",
            "relevance_score": 5
        }
    ]
    
    print(f"Found {len(sample_articles)} articles")
    
    # Parse for squad information
    parser = NewsParser()
    processed = parser.process_articles(sample_articles)
    
    print(f"Extracted squad info from {len(processed)} articles")
    for article in processed:
        print(f"  - Teams: {article.get('teams_mentioned', [])}")
        print(f"  - Transfers: {len(article.get('transfers', []))}")


def example_squad_comparison():
    """Example: Compare news data with footballtransfers data."""
    print("\n🔄 Example 2: Squad Comparison")
    print("-" * 50)
    
    # Sample news data
    news_data = [
        {
            "teams_mentioned": ["manchester_city"],
            "transfers": [
                {"player": "Viktor Gyökeres", "type": "incoming", "team": "manchester_city"}
            ],
            "players_mentioned": ["Viktor Gyökeres", "Erling Haaland"],
            "source": "Sky Sports"
        }
    ]
    
    # Sample footballtransfers data
    ft_data = {
        "manchester-city": {
            "team": "Manchester City",
            "squad": {
                "Forwards": [
                    {"name": "Erling Haaland", "position": "ST", "age": 23},
                    {"name": "Julian Álvarez", "position": "ST", "age": 24}
                ]
            }
        }
    }
    
    # Compare
    comparator = SquadComparator()
    results = comparator.compare_squad_lists(news_data, ft_data)
    
    print(f"Teams compared: {results.get('teams_compared', 0)}")
    print(f"Discrepancies found: {results.get('discrepancies_found', 0)}")
    
    # Show discrepancies
    for team_name, team_data in results.get('teams', {}).items():
        discrepancies = team_data.get('discrepancies', {})
        print(f"\n{team_name}:")
        if discrepancies.get('missing_in_ft'):
            print(f"  New in news: {discrepancies['missing_in_ft']}")
        if discrepancies.get('missing_in_news'):
            print(f"  Not mentioned in news: {discrepancies['missing_in_news']}")


def example_discrepancy_report():
    """Example: Generate and save discrepancy report."""
    print("\n📊 Example 3: Discrepancy Report")
    print("-" * 50)
    
    # Sample comparison results
    comparison_results = {
        "comparison_date": "2024-01-15T10:30:00Z",
        "teams_compared": 2,
        "discrepancies_found": 1,
        "teams": {
            "manchester_city": {
                "footballtransfers_team": "manchester-city",
                "news_players_count": 2,
                "ft_players_count": 2,
                "discrepancies": {
                    "exact_matches": ["erling haaland"],
                    "missing_in_ft": ["viktor gyökeres"],
                    "missing_in_news": ["julian álvarez"],
                    "fuzzy_matches": []
                },
                "news_transfers": [
                    {
                        "player": "Viktor Gyökeres",
                        "type": "incoming",
                        "source": "Sky Sports",
                        "date": "2024-01-15"
                    }
                ]
            }
        }
    }
    
    # Save report
    try:
        os.makedirs("./example_output", exist_ok=True)
        report_file = save_discrepancies(comparison_results, "./example_output")
        print(f"Discrepancy report saved to: {report_file}")
        
        # Show sample of what's in the report
        print("\nSample discrepancy data:")
        for team, data in comparison_results["teams"].items():
            print(f"  {team}:")
            disc = data["discrepancies"]
            print(f"    - Players in news but not FT: {disc['missing_in_ft']}")
            print(f"    - Players in FT but not news: {disc['missing_in_news']}")
            
    except Exception as e:
        print(f"Error saving report: {e}")


def example_integration_workflow():
    """Example: Complete integration workflow."""
    print("\n🔄 Example 4: Complete Workflow")
    print("-" * 50)
    
    print("Step 1: Fetch and filter news")
    print("Step 2: Parse squad information")  
    print("Step 3: Load existing footballtransfers data")
    print("Step 4: Compare and find discrepancies")
    print("Step 5: Generate reports")
    print("Step 6: Create FAISS index for news")
    
    print("\nThis is the workflow that 'python process_news.py' executes!")
    print("Each step can also be run individually for custom processing.")


def main():
    """Run all examples."""
    print("🚀 SquadWatch RSS News Processing Examples")
    print("=" * 60)
    
    try:
        example_basic_usage()
        example_squad_comparison()
        example_discrepancy_report() 
        example_integration_workflow()
        
        print("\n✅ All examples completed!")
        print("\n📚 Learn more:")
        print("  - Run 'python test_news.py' for comprehensive tests")
        print("  - Run 'python process_news.py' for real RSS processing")
        print("  - Check README.md for detailed documentation")
        
    except Exception as e:
        print(f"\n❌ Error in examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()