"""Build the NASA OSDR Space Flight vs Control dataset from every labelled OSDR sample.

Source: NASA Open Science Data Repository biodata API (~51k samples, includes OSD-53, the
astronaut gene-expression study). Nothing is generated. Test = whole held-out studies, so
the score measures generalisation to studies the model has never seen.
"""
from __future__ import annotations
import csv, hashlib, io, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
OUT, CACHE = ROOT / 'data' / 'osdr', ROOT / 'data' / 'cache' / 'osdr_metadata.csv'
API = 'https://visualization.osdr.nasa.gov/biodata/api/v2/query/metadata/'
QUERY = ['study.characteristics', 'study.parameter value', 'investigation.study assays', 'study.factor value.spaceflight']
TARGET = 'study.factor value.spaceflight'
ID_COLS = {'id.accession': 'accession', 'id.assay name': 'assay_name', 'id.sample name': 'sample_name'}
# Fields that restate where the sample was (ISS vs Earth) or define the control group itself.
# The leakage audit in train_osdr_model.py shows why; see data/osdr/README.md.
DENY = ('habitat', 'hardware', 'growth environment', 'location', 'gravity', 'file name', 'term ')
MIN_COVERAGE, TEST_FRAC, SEED = 0.02, 0.2, 42


def label(v: str):
    v = v.strip().lower()
    if v in ('space flight', 'in-flight'): return 1
    if v == 'ground' or ('control' in v and 'flight' not in v): return 0
    return None  # pre/post-flight, NaN, Not Applicable: ambiguous, dropped


def fetch(refresh=False) -> bytes:
    if CACHE.exists() and not refresh: return CACHE.read_bytes()
    url = API + '?' + '&'.join(quote(f) for f in QUERY) + '&format=csv'
    with urlopen(Request(url, headers={'User-Agent': 'LaylHackathonResearchBot/1.0'}), timeout=600) as r: raw = r.read()
    CACHE.parent.mkdir(parents=True, exist_ok=True); CACHE.write_bytes(raw)
    return raw


def feature_name(col: str) -> str:
    for a, b in (('investigation.study assays.study assay ', 'assay_'), ('study.characteristics.', 'char_'), ('study.parameter value.', 'param_')):
        col = col.replace(a, b)
    return col.replace(' ', '_')


def build(raw: bytes):
    csv.field_size_limit(10**9)
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
    labelled = [r for r in rows if label(r[TARGET]) is not None]
    feats = [c for c in rows[0] if c not in ID_COLS and c != TARGET and not any(d in c for d in DENY)
             and sum(r[c] not in ('NaN', '') for r in labelled) >= MIN_COVERAGE * len(labelled)]
    names = {c: feature_name(c) for c in feats}
    out = []
    for r in labelled:
        rec = {v: r[k] for k, v in ID_COLS.items()}
        rec.update({names[c]: ('' if r[c] == 'NaN' else r[c].strip().lower()) for c in feats})  # 'Male'=='male'
        rec['label'] = label(r[TARGET])
        out.append(rec)
    out = list({tuple(r.values()): r for r in out}.values())  # drop exact duplicates
    # Stratified-by-study split: sort studies by hash (stable, seedless), fill test to ~20% of rows.
    studies = sorted({r['accession'] for r in out}, key=lambda s: hashlib.sha256(f'{SEED}{s}'.encode()).hexdigest())
    size = Counter(r['accession'] for r in out)
    test_ids, n = set(), 0
    for s in studies:
        if n >= TEST_FRAC * len(out): break
        test_ids.add(s); n += size[s]
    train = [r for r in out if r['accession'] not in test_ids]
    test = [r for r in out if r['accession'] in test_ids]
    return len(rows), [*ID_COLS.values(), *names.values(), 'label'], train, test


def write(path: Path, cols, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)


def main(refresh=False):
    OUT.mkdir(parents=True, exist_ok=True)
    raw = fetch(refresh)
    total, cols, train, test = build(raw)
    assert not {r['accession'] for r in train} & {r['accession'] for r in test}, 'study leakage'
    write(OUT / 'train.csv', cols, train); write(OUT / 'test.csv', cols, test)
    for old in ('full_5000.csv',): (OUT / old).unlink(missing_ok=True)
    stats = lambda rs: {'rows': len(rs), 'studies': len({r['accession'] for r in rs}),
                        'label_counts': {str(k): v for k, v in sorted(Counter(r['label'] for r in rs).items())}}
    manifest = {'generated_utc': datetime.now(timezone.utc).isoformat(), 'source': API, 'query_fields': QUERY,
                'source_sha256': hashlib.sha256(raw).hexdigest(), 'source_rows': total,
                'label': '1=Space Flight/in-flight, 0=ground/vivarium/basal control; other rows dropped',
                'denylisted_substrings': DENY, 'feature_columns': cols[3:-1],
                'split': 'grouped by accession (no study in both files)', 'train': stats(train), 'test': stats(test),
                'files': {p: hashlib.sha256((OUT / p).read_bytes()).hexdigest() for p in ('train.csv', 'test.csv')}}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({k: manifest[k] for k in ('source_rows', 'train', 'test')}, indent=2), f'\n{len(cols) - 4} features')


if __name__ == '__main__':
    import sys
    main(refresh='--refresh' in sys.argv)
