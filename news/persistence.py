import os
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
import re


def _slugify(name: str) -> str:
    """Convert a name to a safe filename slug."""
    s = (name or "").lower().strip()
    s = re.sub(r"[^a-z0-9\-_.]+", "-", s)      # allow -, _, .
    s = re.sub(r"[-_\.]{2,}", "-", s)          # collapse runs
    return s.strip("-_.") or "news"


def save_news_articles(articles: List[Dict[str, Any]], out_dir: str = "./data/news") -> str:
    """
    Save news articles to timestamped JSON files.
    
    Args:
        articles: List of news articles to save
        out_dir: Output directory for saving articles
        
    Returns:
        Path to the saved articles directory
    """
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = os.path.join(out_dir, timestamp)
    os.makedirs(snapshot_dir, exist_ok=True)
    
    # Save all articles in a single file
    articles_file = os.path.join(snapshot_dir, "articles.json")
    with open(articles_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved {len(articles)} articles to {articles_file}")
    return snapshot_dir


def save_processed_squad_info(processed_articles: List[Dict[str, Any]], out_dir: str = "./data/news") -> str:
    """
    Save processed squad information to timestamped JSON files.
    
    Args:
        processed_articles: List of processed squad information
        out_dir: Output directory for saving processed data
        
    Returns:
        Path to the saved squad info file
    """
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = os.path.join(out_dir, timestamp)
    os.makedirs(snapshot_dir, exist_ok=True)
    
    # Save processed squad information
    squad_info_file = os.path.join(snapshot_dir, "squad_info.json")
    with open(squad_info_file, "w", encoding="utf-8") as f:
        json.dump(processed_articles, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved processed squad info from {len(processed_articles)} articles to {squad_info_file}")
    return squad_info_file


def save_discrepancies(discrepancies: Dict[str, Any], out_dir: str = "./data/comparisons") -> str:
    """
    Save squad comparison discrepancies to JSON file.
    
    Args:
        discrepancies: Dictionary containing comparison results
        out_dir: Output directory for saving comparison results
        
    Returns:
        Path to the saved discrepancies file
    """
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(out_dir, exist_ok=True)
    
    discrepancies_file = os.path.join(out_dir, f"discrepancies_{timestamp}.json")
    with open(discrepancies_file, "w", encoding="utf-8") as f:
        json.dump(discrepancies, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved squad discrepancies to {discrepancies_file}")
    return discrepancies_file


def load_latest_squad_info(base_dir: str = "./data/news") -> List[Dict[str, Any]]:
    """
    Load the most recent processed squad information.
    
    Args:
        base_dir: Base directory containing news snapshots
        
    Returns:
        List of processed squad information
    """
    if not os.path.exists(base_dir):
        return []
    
    # Find latest snapshot directory
    snapshots = [d for d in os.listdir(base_dir) 
                if os.path.isdir(os.path.join(base_dir, d))]
    
    if not snapshots:
        return []
    
    latest_snapshot = sorted(snapshots)[-1]
    squad_info_file = os.path.join(base_dir, latest_snapshot, "squad_info.json")
    
    if not os.path.exists(squad_info_file):
        return []
    
    try:
        with open(squad_info_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading squad info: {e}")
        return []


def news_to_documents(processed_articles: List[Dict[str, Any]]) -> List[str]:
    """
    Convert processed news articles to text documents for embedding.
    
    Args:
        processed_articles: List of processed squad information
        
    Returns:
        List of text documents ready for embedding
    """
    documents = []
    
    for article in processed_articles:
        # Create a document for each transfer found
        for transfer in article.get('transfers', []):
            doc = f"""
            Transfer News: {transfer.get('player', 'Unknown')} {transfer.get('type', '')} {transfer.get('team', 'Unknown')}
            Source: {article.get('source', 'Unknown')}
            Date: {article.get('published_date', 'Unknown')}
            Context: {transfer.get('context', '')}
            Teams: {', '.join(article.get('teams_mentioned', []))}
            """
            documents.append(doc.strip())
        
        # Create a document for each contract found
        for contract in article.get('contracts', []):
            doc = f"""
            Contract News: {contract.get('contract_info', 'Unknown')}
            Source: {article.get('source', 'Unknown')}
            Date: {article.get('published_date', 'Unknown')}
            Context: {contract.get('context', '')}
            Teams: {', '.join(article.get('teams_mentioned', []))}
            """
            documents.append(doc.strip())
        
        # Create a general document for articles with team mentions but no specific transfers
        if article.get('teams_mentioned') and not article.get('transfers') and not article.get('contracts'):
            doc = f"""
            Team News: {', '.join(article.get('teams_mentioned', []))}
            Title: {article.get('article_title', 'Unknown')}
            Source: {article.get('source', 'Unknown')}
            Date: {article.get('published_date', 'Unknown')}
            Players: {', '.join(article.get('players_mentioned', []))}
            """
            documents.append(doc.strip())
    
    return documents


def create_news_index(processed_articles: List[Dict[str, Any]], index_path: str = "./data/index/news_faiss_index"):
    """
    Create FAISS index from processed news articles.
    
    Args:
        processed_articles: List of processed squad information
        index_path: Path to save the FAISS index
        
    Returns:
        FAISS database object
    """
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings
        
        # Convert articles to documents
        documents = news_to_documents(processed_articles)
        
        if not documents:
            print("⚠️  No documents to index")
            return None
        
        # Create embeddings and FAISS index
        embeddings = OpenAIEmbeddings()
        db = FAISS.from_texts(documents, embeddings)
        
        # Save the index
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        db.save_local(index_path)
        
        print(f"✅ Created news FAISS index with {len(documents)} documents at {index_path}")
        return db
        
    except ImportError:
        print("⚠️  OpenAI embeddings not available, skipping index creation")
        return None
    except Exception as e:
        print(f"❌ Error creating news index: {e}")
        return None