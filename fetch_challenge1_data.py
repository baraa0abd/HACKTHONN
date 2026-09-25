"""Download the authentic Iraq annual Black Marble ADM2 records from World Bank."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
RESOURCE = "DR0095685"
BASE = "https://datacatalogapi.worldbank.org/ddhxext/v3"


def get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Layl/2.0 hackathon research client"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    destination = ROOT / "data" / "real"
    destination.mkdir(parents=True, exist_ok=True)
    query = urllib.parse.urlencode({"top": 5000, "filter": "ISO_A3='IRQ'"})
    data_url = f"{BASE}/resources/{RESOURCE}/data?{query}"
    metadata_url = f"{BASE}/resources/{RESOURCE}/metadata"
    payload = get_json(data_url)
    metadata = get_json(metadata_url)
    if payload.get("count") != len(payload.get("value", [])) or payload.get("count", 0) < 1000:
        raise ValueError("World Bank API returned an incomplete Iraq dataset")
    raw = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    schema = json.dumps(metadata, indent=2, ensure_ascii=False).encode("utf-8")
    (destination / "worldbank_iraq_annual.json").write_bytes(raw)
    (destination / "worldbank_schema.json").write_bytes(schema)
    manifest = {
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "provider": "World Bank Space2Stats",
        "upstream": "NASA Black Marble nighttime lights aggregated to World Bank ADM2 boundaries",
        "dataset_page": "https://datacatalog.worldbank.org/search/dataset/0066940/space2stats-monthly-annual-black-marble-nighttime-lights",
        "resource_id": RESOURCE,
        "query": "ISO_A3='IRQ'",
        "data_url": data_url,
        "metadata_url": metadata_url,
        "records": payload["count"],
        "files": {
            "worldbank_iraq_annual.json": hashlib.sha256(raw).hexdigest(),
            "worldbank_schema.json": hashlib.sha256(schema).hexdigest(),
        },
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Downloaded {payload['count']} authentic Iraq ADM2-year records")


if __name__ == "__main__":
    main()
