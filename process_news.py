#!/usr/bin/env python3
"""
RSS News Processor for Football Squad Data

This script fetches football news from RSS feeds, extracts squad and transfer 
information, and compares it with existing footballtransfers.com data to find discrepancies.
"""

import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news.rss_scraper import fetch_all_football_news, filter_squad_related_news
from news.parser import NewsParser
from news.persistence import (
    save_news_articles, 
    save_processed_squad_info, 
    save_discrepancies,
    create_news_index
)
from news.comparator import SquadComparator


def main():
    """Main function to run the RSS news processing pipeline."""
    
    print("🚀 Starting RSS Football News Processing Pipeline")
    print("=" * 60)
    
    try:
        # Step 1: Fetch news from RSS feeds
        print("\n📰 Step 1: Fetching football news from RSS feeds...")
        all_articles = fetch_all_football_news(days_back=7, max_per_feed=30)
        
        if not all_articles:
            print("❌ No articles fetched. Exiting.")
            return
        
        # Step 2: Filter for squad/transfer related articles
        print("\n🎯 Step 2: Filtering for squad/transfer related articles...")
        relevant_articles = filter_squad_related_news(all_articles)
        
        if not relevant_articles:
            print("❌ No relevant articles found. Exiting.")
            return
        
        # Step 3: Save raw articles
        print("\n💾 Step 3: Saving raw articles...")
        save_news_articles(relevant_articles)
        
        # Step 4: Parse articles for squad information
        print("\n🔍 Step 4: Parsing articles for squad information...")
        parser = NewsParser()
        processed_articles = parser.process_articles(relevant_articles)
        
        if not processed_articles:
            print("❌ No squad information extracted. Exiting.")
            return
        
        # Step 5: Save processed squad information
        print("\n💾 Step 5: Saving processed squad information...")
        save_processed_squad_info(processed_articles)
        
        # Step 6: Create FAISS index for news data
        print("\n📦 Step 6: Creating FAISS index for news data...")
        create_news_index(processed_articles)
        
        # Step 7: Compare with existing footballtransfers data
        print("\n🔄 Step 7: Comparing with footballtransfers data...")
        comparator = SquadComparator()
        ft_teams = comparator.load_footballtransfers_data()
        
        if ft_teams:
            comparison_results = comparator.compare_squad_lists(processed_articles, ft_teams)
            
            # Step 8: Save discrepancies
            print("\n💾 Step 8: Saving discrepancies...")
            discrepancies_file = save_discrepancies(comparison_results)
            
            # Summary
            print(f"\n✅ Pipeline completed successfully!")
            print(f"📊 Summary:")
            print(f"   • Total articles fetched: {len(all_articles)}")
            print(f"   • Relevant articles: {len(relevant_articles)}")
            print(f"   • Articles with squad info: {len(processed_articles)}")
            print(f"   • Teams compared: {comparison_results.get('teams_compared', 0)}")
            print(f"   • Teams with discrepancies: {comparison_results.get('discrepancies_found', 0)}")
            print(f"   • Discrepancies saved to: {discrepancies_file}")
            
            # Show some example discrepancies
            if comparison_results.get('discrepancies_found', 0) > 0:
                print(f"\n🔍 Example discrepancies found:")
                for team_name, team_data in comparison_results.get('teams', {}).items():
                    discrepancies = team_data.get('discrepancies', {})
                    if discrepancies.get('missing_in_ft') or discrepancies.get('missing_in_news'):
                        print(f"   • {team_name}:")
                        if discrepancies.get('missing_in_ft'):
                            print(f"     - Players in news but not in FT: {discrepancies['missing_in_ft'][:3]}")
                        if discrepancies.get('missing_in_news'):
                            print(f"     - Players in FT but not in news: {discrepancies['missing_in_news'][:3]}")
        else:
            print("⚠️  No footballtransfers data found for comparison")
            print("   Run 'python refresh-ft.py' first to fetch footballtransfers data")
        
    except KeyboardInterrupt:
        print("\n⏹️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error in pipeline: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()