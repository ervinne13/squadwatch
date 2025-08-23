import os
import json
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

def get_latest_snapshot(base_dir="data/squads"):
    snapshots = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    if not snapshots:
        raise ValueError("No snapshots found in data/squads")
    latest = sorted(snapshots)[-1]  # pick latest by timestamp string
    return os.path.join(base_dir, latest)

def load_squads(snapshot_dir):
    squads = {}
    for fname in os.listdir(snapshot_dir):
        if fname.endswith(".json"):
            team = fname.replace(".json", "")
            path = os.path.join(snapshot_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                squads[team] = json.load(f)
    return squads

def squad_to_docs(team, data):
    docs = []
    for player in data.get("players", []):
        text = f"""
        Player: {player.get('name')}
        Team: {team}
        Position: {player.get('position')}
        Nationality: {player.get('nationality')}
        Age: {player.get('age')}
        Contract Until: {player.get('contract_until')}
        """
        docs.append(text.strip())
    return docs

def index_squads(squads, index_path="data/index/faiss_index"):
    embeddings = OpenAIEmbeddings()
    all_docs = []
    for team, data in squads.items():
        all_docs.extend(squad_to_docs(team, data))

    # Create FAISS index
    db = FAISS.from_texts(all_docs, embeddings)
    db.save_local(index_path)
    return db

if __name__ == "__main__":
    try:
        print("📂 Finding latest snapshot...")
        snapshot_dir = get_latest_snapshot()
        print(f"   → Using snapshot: {snapshot_dir}")

        print("📥 Loading squads...")
        squads = load_squads(snapshot_dir)
        print(f"   → Loaded {len(squads)} teams")

        print("📦 Indexing squads...")
        db = index_squads(squads)
        print("✅ Squads indexed and saved to data/index/faiss_index")

    except Exception as e:
        print(f"❌ Error: {e}")
