"""OSDR spaceflight model endpoints for the dashboard server. Everything served is read from
the real metrics files and trained models; nothing here fabricates values."""
from __future__ import annotations
import io, json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS, DATA = ROOT / 'models', ROOT / 'data' / 'osdr'
# Form fields shown on the phone: the ones a researcher can state from a study design.
FORM_FIELDS = ['char_organism', 'char_material_type', 'assay_technology_type', 'assay_measurement_type',
               'char_sex', 'char_strain', 'param_duration', 'char_launch_mission']
MAX_VALUE_LEN = 200


def _read(name):
    p = MODELS / name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


def metrics():
    meta, genes = _read('osdr_flight_metrics.json'), _read('osdr_genes_metrics.json')
    return {'metadata_model': meta, 'gene_model': genes,
            'dataset': json.loads((DATA / 'manifest.json').read_text(encoding='utf-8'))}


@lru_cache(maxsize=1)
def options():
    """Real values seen in training, most common first, so the form only offers known categories."""
    import pandas as pd
    df = pd.read_csv(DATA / 'train.csv', usecols=FORM_FIELDS, dtype=str, keep_default_na=False, encoding='utf-8-sig')
    return {f: [v for v in df[f].value_counts().index if v][:60] for f in FORM_FIELDS}


def predict(payload: dict):
    if not isinstance(payload, dict) or not payload: raise ValueError('send a JSON object of study fields')
    unknown = set(payload) - set(FORM_FIELDS)
    if unknown: raise ValueError(f'unknown fields: {sorted(unknown)}')
    if any(not isinstance(v, str) or len(v) > MAX_VALUE_LEN for v in payload.values()):
        raise ValueError('field values must be short strings')
    import pandas as pd, sys
    sys.path.insert(0, str(ROOT))
    from train_osdr_model import score
    p = float(score(pd.DataFrame([payload]))[0])
    known = options()
    unseen = [f for f, v in payload.items() if v and v.strip().lower() not in known[f]]
    return {'p_space_flight': round(p, 4), 'fields_used': {k: v for k, v in payload.items() if v},
            'unseen_values': unseen, 'model': (_read('osdr_flight_metrics.json') or {}).get('selected_model')}


def predict_genes(csv_bytes: bytes):
    if not (MODELS / 'osdr_genes_model.joblib').exists(): raise FileNotFoundError('gene model not trained yet')
    import pandas as pd, sys
    sys.path.insert(0, str(ROOT))
    from train_osdr_genes import score_vst
    out = score_vst(pd.read_csv(io.BytesIO(csv_bytes), index_col=0))
    return {'gene_coverage': round(out.attrs['gene_coverage'], 4), 'samples': out.to_dict(orient='records')}
