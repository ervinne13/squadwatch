import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json


class NewsParser:
    """
    Parses football news articles to extract squad and transfer information.
    """
    
    def __init__(self):
        # Common team name patterns and their variations
        self.team_patterns = self._build_team_patterns()
        
        # Player name patterns (simplified)
        self.player_name_pattern = re.compile(r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)*\b')
        
        # Transfer action patterns
        self.transfer_patterns = [
            re.compile(r'(\w+(?:\s+\w+)*)\s+(?:has\s+)?(?:signed|joined|moved)\s+(?:to\s+)?(\w+(?:\s+\w+)*)', re.IGNORECASE),
            re.compile(r'(\w+(?:\s+\w+)*)\s+(?:leaves|left|departs)\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
            re.compile(r'(\w+(?:\s+\w+)*)\s+(?:confirms|announces)\s+(?:the\s+)?(?:signing|arrival)\s+of\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
            re.compile(r'(\w+(?:\s+\w+)*)\s+(?:agree|agreed)\s+(?:a\s+)?deal\s+for\s+(\w+(?:\s+\w+)*)', re.IGNORECASE),
        ]
        
        # Contract patterns
        self.contract_patterns = [
            re.compile(r'contract\s+(?:until|expires?)\s+(\d{4})', re.IGNORECASE),
            re.compile(r'(\d{4})\s+contract', re.IGNORECASE),
            re.compile(r'deal\s+until\s+(\d{4})', re.IGNORECASE),
            re.compile(r'(\d+)[-\s]year\s+(?:contract|deal)', re.IGNORECASE),
        ]
        
        # Position patterns
        self.position_patterns = [
            re.compile(r'\b(?:goalkeeper|keeper|gk)\b', re.IGNORECASE),
            re.compile(r'\b(?:defender|centre-back|left-back|right-back|full-back|cb|lb|rb|fb)\b', re.IGNORECASE),
            re.compile(r'\b(?:midfielder|midfield|central midfielder|attacking midfielder|defensive midfielder|cm|am|dm)\b', re.IGNORECASE),
            re.compile(r'\b(?:forward|striker|winger|left winger|right winger|lw|rw|cf|st)\b', re.IGNORECASE),
        ]

    def _build_team_patterns(self) -> Dict[str, List[str]]:
        """Build a dictionary of team name variations for better matching."""
        # This is a simplified version - in production, you'd want a comprehensive team database
        return {
            "manchester_united": ["Manchester United", "Man United", "Man Utd", "United"],
            "manchester_city": ["Manchester City", "Man City", "City"],
            "liverpool": ["Liverpool", "Liverpool FC", "LFC"],
            "chelsea": ["Chelsea", "Chelsea FC"],
            "arsenal": ["Arsenal", "Arsenal FC", "Gunners"],
            "tottenham": ["Tottenham", "Spurs", "Tottenham Hotspur"],
            "barcelona": ["Barcelona", "Barca", "FC Barcelona"],
            "real_madrid": ["Real Madrid", "Madrid", "Real"],
            "bayern_munich": ["Bayern Munich", "Bayern", "FC Bayern"],
            "psg": ["PSG", "Paris Saint-Germain", "Paris SG"],
        }

    def extract_squad_info(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract squad and transfer information from a news article.
        
        Args:
            article: News article dictionary
            
        Returns:
            Dictionary containing extracted squad information
        """
        # Combine all text content
        title = article.get('title', '')
        description = article.get('description', '')
        summary = article.get('summary', '')
        content = article.get('content', '')
        
        full_text = f"{title} {description} {summary} {content}"
        
        # Extract information
        transfers = self._extract_transfers(full_text)
        contracts = self._extract_contracts(full_text)
        teams_mentioned = self._extract_teams(full_text)
        players_mentioned = self._extract_players(full_text)
        
        return {
            "article_url": article.get('link', ''),
            "article_title": title,
            "published_date": article.get('published', ''),
            "source": article.get('source_name', ''),
            "transfers": transfers,
            "contracts": contracts,
            "teams_mentioned": teams_mentioned,
            "players_mentioned": players_mentioned,
            "relevance_score": article.get('relevance_score', 0),
            "raw_text": full_text[:1000],  # Keep first 1000 chars for reference
        }

    def _extract_transfers(self, text: str) -> List[Dict[str, Any]]:
        """Extract transfer information from text."""
        transfers = []
        
        for pattern in self.transfer_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if len(match) == 2:
                    player, team = match
                    transfer = {
                        "player": player.strip(),
                        "team": team.strip(),
                        "type": self._determine_transfer_type(pattern.pattern),
                        "context": self._extract_context(text, player, 100)
                    }
                    transfers.append(transfer)
        
        return transfers

    def _extract_contracts(self, text: str) -> List[Dict[str, Any]]:
        """Extract contract information from text."""
        contracts = []
        
        for pattern in self.contract_patterns:
            matches = pattern.findall(text)
            for match in matches:
                contract = {
                    "contract_info": match if isinstance(match, str) else str(match),
                    "context": self._extract_context(text, str(match), 100)
                }
                contracts.append(contract)
        
        return contracts

    def _extract_teams(self, text: str) -> List[str]:
        """Extract team names from text."""
        teams = set()
        
        for team_key, variations in self.team_patterns.items():
            for variation in variations:
                if variation.lower() in text.lower():
                    teams.add(team_key)
                    break
        
        return list(teams)

    def _extract_players(self, text: str) -> List[str]:
        """Extract potential player names from text."""
        # This is a simplified approach - in production you'd want a better NER system
        potential_names = self.player_name_pattern.findall(text)
        
        # Filter out common non-player words
        non_player_words = {
            'The', 'This', 'That', 'They', 'It', 'He', 'She', 'We', 'You',
            'Premier', 'League', 'Championship', 'Cup', 'Football', 'Club',
            'Manager', 'Coach', 'Director', 'Chairman', 'January', 'February',
            'March', 'April', 'May', 'June', 'July', 'August', 'September',
            'October', 'November', 'December', 'Monday', 'Tuesday', 'Wednesday',
            'Thursday', 'Friday', 'Saturday', 'Sunday'
        }
        
        filtered_names = [name for name in potential_names 
                         if name not in non_player_words and len(name.split()) <= 3]
        
        return list(set(filtered_names))

    def _determine_transfer_type(self, pattern: str) -> str:
        """Determine the type of transfer based on the pattern matched."""
        if 'signed' in pattern or 'joined' in pattern:
            return 'incoming'
        elif 'leaves' in pattern or 'left' in pattern or 'departs' in pattern:
            return 'outgoing'
        elif 'confirms' in pattern or 'announces' in pattern:
            return 'confirmed'
        elif 'agree' in pattern:
            return 'agreed'
        else:
            return 'unknown'

    def _extract_context(self, text: str, keyword: str, context_length: int = 100) -> str:
        """Extract context around a keyword."""
        try:
            index = text.lower().find(keyword.lower())
            if index == -1:
                return ""
            
            start = max(0, index - context_length // 2)
            end = min(len(text), index + len(keyword) + context_length // 2)
            
            return text[start:end].strip()
        except:
            return ""

    def process_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple articles and extract squad information from all.
        
        Args:
            articles: List of news articles
            
        Returns:
            List of processed squad information
        """
        processed_articles = []
        
        print(f"🔍 Processing {len(articles)} articles for squad information...")
        
        for i, article in enumerate(articles):
            try:
                squad_info = self.extract_squad_info(article)
                if squad_info['transfers'] or squad_info['contracts'] or squad_info['teams_mentioned']:
                    processed_articles.append(squad_info)
                    
                if (i + 1) % 10 == 0:
                    print(f"   → Processed {i + 1}/{len(articles)} articles")
                    
            except Exception as e:
                print(f"❌ Error processing article {i}: {e}")
                continue
        
        print(f"✅ Extracted squad information from {len(processed_articles)} articles")
        return processed_articles