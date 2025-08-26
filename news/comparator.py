import os
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from difflib import SequenceMatcher
from datetime import datetime


class SquadComparator:
    """
    Compares squad information from RSS news with existing footballtransfers data.
    """
    
    def __init__(self):
        self.team_name_mappings = self._build_team_mappings()
        
    def _build_team_mappings(self) -> Dict[str, str]:
        """Build mappings between different team name formats."""
        return {
            # RSS news format -> footballtransfers format
            "manchester_united": "manchester-united",
            "manchester_city": "manchester-city", 
            "liverpool": "liverpool",
            "chelsea": "chelsea",
            "arsenal": "arsenal",
            "tottenham": "tottenham",
            "barcelona": "barcelona",
            "real_madrid": "real-madrid",
            "bayern_munich": "bayern-munich",
            "psg": "paris-saint-germain",
        }

    def load_footballtransfers_data(self, base_dir: str = "./data/squads") -> Dict[str, Dict[str, Any]]:
        """
        Load the latest footballtransfers squad data.
        
        Args:
            base_dir: Directory containing footballtransfers squad data
            
        Returns:
            Dictionary of team data keyed by team name
        """
        if not os.path.exists(base_dir):
            print(f"⚠️  Footballtransfers data directory not found: {base_dir}")
            return {}
        
        # Find latest snapshot
        snapshots = [d for d in os.listdir(base_dir) 
                    if os.path.isdir(os.path.join(base_dir, d))]
        
        if not snapshots:
            print("⚠️  No footballtransfers snapshots found")
            return {}
        
        latest_snapshot = sorted(snapshots)[-1]
        snapshot_dir = os.path.join(base_dir, latest_snapshot)
        
        teams_data = {}
        for filename in os.listdir(snapshot_dir):
            if filename.endswith('.json'):
                team_name = filename.replace('.json', '')
                filepath = os.path.join(snapshot_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        team_data = json.load(f)
                        teams_data[team_name] = team_data
                except Exception as e:
                    print(f"❌ Error loading {filepath}: {e}")
        
        print(f"📊 Loaded footballtransfers data for {len(teams_data)} teams")
        return teams_data

    def normalize_player_name(self, name: str) -> str:
        """Normalize player names for comparison."""
        if not name:
            return ""
        
        # Remove common prefixes/suffixes and normalize
        name = name.strip()
        name = name.replace("'", "")  # Remove apostrophes
        name = " ".join(name.split())  # Normalize whitespace
        
        return name.lower()

    def calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two player names."""
        norm1 = self.normalize_player_name(name1)
        norm2 = self.normalize_player_name(name2)
        
        if not norm1 or not norm2:
            return 0.0
        
        return SequenceMatcher(None, norm1, norm2).ratio()

    def find_matching_team(self, news_team: str, ft_teams: Dict[str, Any]) -> Optional[str]:
        """
        Find the matching footballtransfers team for a news team.
        
        Args:
            news_team: Team name from news
            ft_teams: Available footballtransfers team data
            
        Returns:
            Matching team key or None
        """
        # Direct mapping check
        if news_team in self.team_name_mappings:
            mapped_name = self.team_name_mappings[news_team]
            if mapped_name in ft_teams:
                return mapped_name
        
        # Fuzzy matching
        best_match = None
        best_score = 0.0
        
        for ft_team_key in ft_teams.keys():
            # Try matching against team key
            score = self.calculate_name_similarity(news_team, ft_team_key)
            if score > best_score and score > 0.6:  # 60% similarity threshold
                best_score = score
                best_match = ft_team_key
            
            # Try matching against team name in data
            ft_team_data = ft_teams[ft_team_key]
            if isinstance(ft_team_data, dict) and 'team' in ft_team_data:
                team_name = ft_team_data['team']
                score = self.calculate_name_similarity(news_team, team_name)
                if score > best_score and score > 0.6:
                    best_score = score
                    best_match = ft_team_key
        
        return best_match

    def extract_ft_players(self, team_data: Dict[str, Any]) -> Set[str]:
        """Extract normalized player names from footballtransfers team data."""
        players = set()
        
        if 'squad' in team_data and isinstance(team_data['squad'], dict):
            for position_group, group_players in team_data['squad'].items():
                if isinstance(group_players, list):
                    for player in group_players:
                        if isinstance(player, dict) and 'name' in player:
                            normalized_name = self.normalize_player_name(player['name'])
                            if normalized_name:
                                players.add(normalized_name)
        
        return players

    def compare_squad_lists(self, 
                           news_articles: List[Dict[str, Any]], 
                           ft_teams: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare squad information from news with footballtransfers data.
        
        Args:
            news_articles: Processed news articles with squad info
            ft_teams: Footballtransfers team data
            
        Returns:
            Dictionary containing comparison results and discrepancies
        """
        comparison_results = {
            "comparison_date": datetime.utcnow().isoformat(),
            "teams_compared": 0,
            "discrepancies_found": 0,
            "teams": {}
        }
        
        # Group news by team
        news_by_team = {}
        for article in news_articles:
            for team in article.get('teams_mentioned', []):
                if team not in news_by_team:
                    news_by_team[team] = []
                news_by_team[team].append(article)
        
        print(f"🔍 Comparing squad data for {len(news_by_team)} teams from news...")
        
        for news_team, team_articles in news_by_team.items():
            # Find matching footballtransfers team
            ft_team_key = self.find_matching_team(news_team, ft_teams)
            
            if not ft_team_key:
                print(f"⚠️  No matching team found for '{news_team}' in footballtransfers data")
                continue
            
            print(f"🔄 Comparing {news_team} -> {ft_team_key}")
            
            # Extract player information from news
            news_players = self._extract_news_players(team_articles)
            
            # Extract player information from footballtransfers
            ft_players = self.extract_ft_players(ft_teams[ft_team_key])
            
            # Compare and find discrepancies
            discrepancies = self._find_discrepancies(news_players, ft_players, team_articles)
            
            comparison_results["teams"][news_team] = {
                "footballtransfers_team": ft_team_key,
                "news_players_count": len(news_players),
                "ft_players_count": len(ft_players),
                "discrepancies": discrepancies,
                "news_transfers": self._extract_transfer_summary(team_articles)
            }
            
            comparison_results["teams_compared"] += 1
            if discrepancies["missing_in_ft"] or discrepancies["missing_in_news"]:
                comparison_results["discrepancies_found"] += 1
        
        print(f"✅ Comparison complete: {comparison_results['teams_compared']} teams compared, "
              f"{comparison_results['discrepancies_found']} with discrepancies")
        
        return comparison_results

    def _extract_news_players(self, team_articles: List[Dict[str, Any]]) -> Set[str]:
        """Extract normalized player names mentioned in news for a team."""
        players = set()
        
        for article in team_articles:
            # Add players from transfers
            for transfer in article.get('transfers', []):
                player_name = transfer.get('player', '')
                normalized = self.normalize_player_name(player_name)
                if normalized:
                    players.add(normalized)
            
            # Add players mentioned in general
            for player in article.get('players_mentioned', []):
                normalized = self.normalize_player_name(player)
                if normalized:
                    players.add(normalized)
        
        return players

    def _find_discrepancies(self, 
                           news_players: Set[str], 
                           ft_players: Set[str],
                           team_articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find discrepancies between news and footballtransfers player lists."""
        
        # Find exact matches first
        exact_matches = news_players & ft_players
        
        # Find fuzzy matches for remaining players
        news_remaining = news_players - exact_matches
        ft_remaining = ft_players - exact_matches
        
        fuzzy_matches = []
        news_unmatched = set(news_remaining)
        ft_unmatched = set(ft_remaining)
        
        for news_player in news_remaining:
            best_match = None
            best_score = 0.0
            
            for ft_player in ft_remaining:
                score = self.calculate_name_similarity(news_player, ft_player)
                if score > best_score and score > 0.7:  # 70% similarity for fuzzy match
                    best_score = score
                    best_match = ft_player
            
            if best_match:
                fuzzy_matches.append({
                    "news_player": news_player,
                    "ft_player": best_match,
                    "similarity": best_score
                })
                news_unmatched.discard(news_player)
                ft_unmatched.discard(best_match)
        
        return {
            "exact_matches": list(exact_matches),
            "fuzzy_matches": fuzzy_matches,
            "missing_in_ft": list(news_unmatched),
            "missing_in_news": list(ft_unmatched),
            "news_context": self._get_player_contexts(news_unmatched, team_articles)
        }

    def _get_player_contexts(self, players: Set[str], team_articles: List[Dict[str, Any]]) -> Dict[str, str]:
        """Get context for players mentioned in news."""
        contexts = {}
        
        for player in players:
            for article in team_articles:
                # Look for context in transfers
                for transfer in article.get('transfers', []):
                    if self.normalize_player_name(transfer.get('player', '')) == player:
                        contexts[player] = transfer.get('context', '')
                        break
                
                if player in contexts:
                    break
        
        return contexts

    def _extract_transfer_summary(self, team_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract summary of transfers mentioned in news for a team."""
        transfers = []
        
        for article in team_articles:
            for transfer in article.get('transfers', []):
                transfers.append({
                    "player": transfer.get('player', ''),
                    "type": transfer.get('type', ''),
                    "team": transfer.get('team', ''),
                    "source": article.get('source', ''),
                    "date": article.get('published_date', ''),
                    "article_url": article.get('article_url', '')
                })
        
        return transfers