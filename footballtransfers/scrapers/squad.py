import json
import re
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from config import HEADERS

def to_iso_date(text: str):
    """Convert '30 Jun 27' or '30 Jun 2027' -> '2027-06-30'; else return original text."""
    if not text:
        return None
    s = text.replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    for fmt in ("%d %b %y", "%d %b %Y"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return s  # leave as-is if not parseable

def header_map(table):
    """Map normalized header text -> column index for a <table>."""
    hdrs = table.select("thead tr th")
    names = []
    for th in hdrs:
        txt = th.get_text(" ", strip=True).lower()
        txt = re.sub(r"\s+", " ", txt)
        names.append(txt)
    return {name: i for i, name in enumerate(names)}, names

def is_contract_header(names):
    # Look for a header that contains 'contract' in any column
    return any("contract" in n for n in names)

def parse_main_table(table, base_url):
    """
    Parse the main squad table (Skill | Player | Age | Height | Weight | ETV).
    Returns dict keyed by player key (url if present, else lowercased name).
    """
    col_idx, names = header_map(table)
    out = {}
    current_group = None

    for tr in table.select("tbody tr"):
        classes = tr.get("class", [])

        # Position group header row
        if "position-group-row" in classes:
            # group name is usually in first cell
            cell = tr.find(["td", "th"])
            current_group = cell.get_text(strip=True) if cell else None
            continue

        # Data row (must have a player link)
        player_link = tr.select_one("a[href*='/en/players/']")
        if not player_link:
            continue

        name = player_link.get_text(strip=True)
        url = urljoin(base_url, player_link.get("href", "").strip())

        # Player cell may be a <th scope="row" class="td-player">
        player_cell = player_link.find_parent(["th", "td"])
        position_tag = player_cell.select_one(".sub-text") if player_cell else None
        position = position_tag.get_text(strip=True) if position_tag else None

        # Map other fields via header indices where possible
        cells = tr.find_all(["th", "td"], recursive=False)
        # Build a text list aligned to headers (best effort)
        cell_texts = [c.get_text(" ", strip=True) for c in cells]

        # Age
        age = None
        for key in ("age",):
            if key in col_idx and col_idx[key] < len(cell_texts):
                txt = cell_texts[col_idx[key]]
                age = int(txt) if txt.isdigit() else txt
                break

        # Value/ETV
        value = None
        # Prefer the styled tag if present
        value_tag = tr.select_one("span.player-tag")
        if value_tag:
            value = value_tag.get_text(strip=True)
        else:
            # fallback to header index named 'etv' or 'value'
            for key in ("etv", "value", "estimated transfer value"):
                if key in col_idx and col_idx[key] < len(cell_texts):
                    value = cell_texts[col_idx[key]]
                    break

        key = url or name.lower()
        out[key] = {
            "name": name,
            "player_url": url or None,
            "position": position,
            "age": age,
            "value": value,
            "contract_until": None,
            "group": current_group,
        }

    return out

def parse_contract_table(table, base_url):
    """
    Parse the contracts table (Skill | Player | Contract end | Age | ETV).
    Returns dict keyed by player key (url if present, else lowercased name) -> contract fields.
    """
    col_idx, names = header_map(table)
    out = {}
    current_group = None

    for tr in table.select("tbody tr"):
        classes = tr.get("class", [])

        # Some pages might also repeat position-group-row here
        if "position-group-row" in classes:
            cell = tr.find(["td", "th"])
            current_group = cell.get_text(strip=True) if cell else None
            continue

        player_link = tr.select_one("a[href*='/en/players/']")
        if not player_link:
            continue

        name = player_link.get_text(strip=True)
        url = urljoin(base_url, player_link.get("href", "").strip())
        player_cell = player_link.find_parent(["th", "td"])

        cells = tr.find_all(["th", "td"], recursive=False)
        cell_texts = [c.get_text(" ", strip=True) for c in cells]

        # Contract end
        contract_until = None
        for key in ("contract end", "contract", "contract until"):
            if key in col_idx and col_idx[key] < len(cell_texts):
                contract_until = to_iso_date(cell_texts[col_idx[key]])
                break
        # Fallback: if contract cell is immediately after the player cell
        if contract_until is None and player_cell:
            nxt = player_cell.find_next_sibling("td")
            if nxt:
                contract_until = to_iso_date(nxt.get_text(strip=True))

        # Age (from contract table, if you prefer this one)
        age = None
        if "age" in col_idx and col_idx["age"] < len(cell_texts):
            txt = cell_texts[col_idx["age"]]
            age = int(txt) if txt.isdigit() else txt

        # Value/ETV
        value_tag = tr.select_one("span.player-tag")
        value = value_tag.get_text(strip=True) if value_tag else None

        key = url or name.lower()
        out[key] = {
            "name": name,
            "player_url": url or None,
            "contract_until": contract_until,
            "age_from_contract_table": age,
            "value_from_contract_table": value,
            "group": current_group,
        }

    return out

def scrape_squad(team_url: str):
    base_url = "https://www.footballtransfers.com"
    resp = requests.get(team_url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    team_name = soup.find("h1").get_text(strip=True) if soup.find("h1") else None

    tables = soup.select("table")
    main_tables = []
    contract_tables = []

    # Classify tables by header text (robust against small markup changes)
    for tbl in tables:
        col_idx, names = header_map(tbl)
        if not names:
            continue
        if is_contract_header(names):
            contract_tables.append(tbl)
        elif any(n in names for n in ("player",)) and any(n in names for n in ("age",)) and not is_contract_header(names):
            main_tables.append(tbl)

    # 1) Parse main squad (take the first candidate table)
    players_main = {}
    for t in main_tables[:1]:
        players_main.update(parse_main_table(t, base_url))

    # 2) Parse contracts table (take the first candidate contracts table)
    players_contracts = {}
    for t in contract_tables[:1]:
        players_contracts.update(parse_contract_table(t, base_url))

    # 3) Merge
    merged = {}
    keys = set(players_main.keys()) | set(players_contracts.keys())
    for k in keys:
        a = players_main.get(k, {})
        b = players_contracts.get(k, {})
        merged[k] = {
            "name": b.get("name") or a.get("name"),
            "player_url": b.get("player_url") or a.get("player_url"),
            "position": a.get("position"),
            # prefer age from main; fall back to contract-table age if missing
            "age": a.get("age") if a.get("age") is not None else b.get("age_from_contract_table"),
            "value": a.get("value") if a.get("value") else b.get("value_from_contract_table"),
            "contract_until": b.get("contract_until") or a.get("contract_until"),
            "group": a.get("group") or b.get("group"),
        }

    # 4) Re-group into the output shape you used earlier
    squad_grouped = {}
    for p in merged.values():
        grp = p.get("group") or "Unknown"
        squad_grouped.setdefault(grp, []).append({
            "name": p["name"],
            "player_url": p["player_url"],
            "position": p["position"],
            "age": p["age"],
            "value": p["value"],
            "contract_until": p["contract_until"],
        })

    return {
        "team": team_name,
        "squad": squad_grouped
    }