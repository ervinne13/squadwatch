import os, re, json
from datetime import datetime
from typing import Callable, List, Tuple
from footballtransfers.scrapers.squad import scrape_squad

def _slugify(name: str) -> str:
    s = (name or "").lower().strip()
    s = re.sub(r"[^a-z0-9\-_.]+", "-", s)      # allow -, _, .
    s = re.sub(r"[-_\.]{2,}", "-", s)          # collapse runs
    return s.strip("-_.") or "team"

def remember_team_squads(
    teams: List[dict],
    out_dir: str = "./data/squads"
) -> Tuple[str, List[str]]:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = os.path.join(out_dir, timestamp)
    os.makedirs(snapshot_dir, exist_ok=True)

    saved_paths: List[str] = []

    for team in teams:
        url = team.get("url")
        if not url:
            print("⚠️  Skipping team with no url:", team)
            continue

        raw_name = team.get("slug") or url.rstrip("/").split("/")[-1] or team.get("name")
        safe_name = _slugify(raw_name)

        try:
            data = scrape_squad(url)
            out_path = os.path.join(snapshot_dir, f"{safe_name}.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            saved_paths.append(out_path)
            print(f"✅ Saved {raw_name} -> {out_path}")

        except Exception as e:
            print(f"❌ Failed to fetch {url} ({raw_name}): {e}")

    return snapshot_dir, saved_paths
