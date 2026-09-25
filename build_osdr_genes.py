"""Download real NASA GeneLab RNA-seq expression for every mouse OSDR study with flight + control samples.

Uses GeneLab's processed VST counts (GLbulkRNAseq pipeline): no simulation, no imputation of labels.
Labels and the train/test study split come from data/osdr/{train,test}.csv (build_osdr_dataset.py),
so a study's expression is only ever in the split its metadata is in.

Each gene is z-scored *within its study* (label-free), which removes tissue and batch offsets.
Consequence: new samples must be scored as a study batch with at least a few flight and control-like
samples. See data/osdr/README.md.
"""
from __future__ import annotations
import hashlib, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parent
META, OUT, CACHE = ROOT / 'data' / 'osdr', ROOT / 'data' / 'osdr_genes', ROOT / 'data' / 'cache' / 'genelab'
BASE = 'https://osdr.nasa.gov'
UA = {'User-Agent': 'LaylHackathonResearchBot/1.0'}
MIN_STUDY_SHARE, N_GENES = 0.9, 3000  # gene must exist in 90% of studies; keep top-N by within-study variance


def get(url, timeout=600):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers=UA), timeout=timeout) as r: return r.read()
        except Exception:
            if attempt == 2: raise
            time.sleep(5 * (attempt + 1))


def studies():
    meta = pd.concat([pd.read_csv(META / f'{s}.csv', dtype=str, keep_default_na=False, encoding='utf-8-sig').assign(split=s)
                      for s in ('train', 'test')])
    rna = meta[meta.char_organism.eq('mus musculus') & meta.assay_technology_type.str.contains('rna sequencing')]
    mixed = rna.groupby('accession').label.nunique().eq(2)
    return rna[rna.accession.isin(mixed[mixed].index)][['accession', 'sample_name', 'label', 'split']]


def vst_file(accession):
    """Path to the cached VST counts CSV, downloading it if needed. None when OSDR has none."""
    num = accession.split('-')[1]
    listing = json.loads(get(f'{BASE}/osdr/data/osd/files/{num}', 120))
    files = [f for s in listing['studies'].values() for f in s['study_files']]
    pick = [f for f in files if f['file_name'].endswith('_VST_Counts_GLbulkRNAseq.csv')]
    if not pick: return None
    f = pick[0]; path = CACHE / f['file_name']
    if not path.exists() or path.stat().st_size != f['file_size']:
        CACHE.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix('.part'); tmp.write_bytes(get(BASE + f['remote_url'])); tmp.replace(path)
    return path


def load_study(path, samples):
    df = pd.read_csv(path, index_col=0)
    df = df.loc[df.index.str.startswith('ENSMUSG'), [c for c in df.columns if c in samples]]
    return df.astype('float32')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = studies(); log, blocks, raw_var = {}, {}, []
    for i, (acc, rows) in enumerate(s.groupby('accession')):
        try: path = vst_file(acc)
        except Exception as e: log[acc] = f'error: {type(e).__name__}: {e}'; continue
        if path is None: log[acc] = 'no VST counts file'; continue
        df = load_study(path, set(rows.sample_name))
        labels = rows.drop_duplicates('sample_name').set_index('sample_name').label.reindex(df.columns)
        if df.shape[1] < 4 or labels.nunique() < 2: log[acc] = f'only {df.shape[1]} matched samples'; continue
        raw_var.append(df.var(axis=1).rename(acc))
        z = df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1).replace(0, np.nan), axis=0).fillna(0)  # label-free
        blocks[acc] = z; log[acc] = f'ok: {df.shape[1]} samples, {df.shape[0]} genes'
        print(f'[{i + 1}/{s.accession.nunique()}] {acc} {log[acc]}', flush=True)
    var = pd.concat(raw_var, axis=1)
    common = var.index[var.notna().mean(axis=1) >= MIN_STUDY_SHARE]
    genes = var.loc[common].mean(axis=1).nlargest(N_GENES).index  # label-free: most variable within studies
    X = pd.concat([b.reindex(genes).fillna(0).T for b in blocks.values()])  # samples x genes
    info = s.drop_duplicates(['accession', 'sample_name']).set_index('sample_name')
    info = pd.concat([info[info.accession == a].reindex(b.columns) for a, b in blocks.items()])
    X.insert(0, 'accession', info.accession.values); X.insert(1, 'label', info.label.astype(int).values)
    X.index.name = 'sample_name'
    for split in ('train', 'test'):
        X[info.split.values == split].round(4).to_csv(OUT / f'genes_{split}.csv.gz', encoding='utf-8')
    manifest = {'generated_utc': datetime.now(timezone.utc).isoformat(), 'source': 'NASA GeneLab GLbulkRNAseq VST counts',
                'normalisation': 'VST, then per-gene z-score within each study (no labels used)',
                'gene_selection': f'top {N_GENES} by mean within-study variance, present in >={MIN_STUDY_SHARE:.0%} of studies',
                'studies': log, 'rows': {sp: int((info.split == sp).sum()) for sp in ('train', 'test')},
                'studies_used': {sp: int(info[info.split == sp].accession.nunique()) for sp in ('train', 'test')},
                'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('genes_*.csv.gz'))}}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({k: manifest[k] for k in ('rows', 'studies_used')}))


if __name__ == '__main__':
    sys.exit(main())
