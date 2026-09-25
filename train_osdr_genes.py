"""Train and evaluate a Space Flight vs Control classifier on real GeneLab mouse RNA-seq.

    python train_osdr_genes.py                          # select, train, test once, save models/
    python train_osdr_genes.py predict GLDS-x_VST.csv   # score one study's GeneLab VST counts file

Same safeguards as train_osdr_model.py: held-out *studies*, grouped CV for selection, equal study
weights, and a null run. Here the null shuffles labels *within* each study, which is the strict test
for sample-level signal. Gene selection (SelectKBest) sits inside the pipeline, so CV folds never
see labels from their validation studies.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from train_osdr_model import MODELS, SEED, cv_scores, fit, metrics, study_weights

GENES = Path(__file__).resolve().parent / 'data' / 'osdr_genes'


def load(split):
    df = pd.read_csv(GENES / f'genes_{split}.csv.gz', index_col=0)
    g, y = df.pop('accession').to_numpy(), df.pop('label').to_numpy().astype(int)
    return df.astype('float32'), y, g


def candidates():
    return {f'k={k} C={C}': lambda k=k, C=C: make_pipeline(SelectKBest(f_classif, k=k), LogisticRegression(C=C, max_iter=5000))
            for k in (50, 300, 1500) for C in (0.001, 0.01, 0.1)}


def within_study_auc(y, p, g):
    s = [roc_auc_score(y[g == a], p[g == a]) for a in sorted(set(g)) if len(set(y[g == a])) == 2]
    return float(np.mean(s)), len(s)


def zscore_within(df):
    """Per-gene z-score across one study's samples (label-free), as done in build_osdr_genes.py."""
    return df.sub(df.mean(axis=1), axis=0).div(df.std(axis=1).replace(0, np.nan), axis=0).fillna(0)


def gene_symbols(ids):
    try:  # ponytail: labels for the report only; the model never needs them
        from urllib.request import Request, urlopen
        req = Request('https://rest.ensembl.org/lookup/id', data=json.dumps({'ids': list(ids)}).encode(),
                      headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        with urlopen(req, timeout=60) as r: data = json.load(r)
        return {i: (data.get(i) or {}).get('display_name', '') for i in ids}
    except Exception:
        return {i: '' for i in ids}


def train():
    Xtr, ytr, gtr = load('train'); Xte, yte, gte = load('test')
    assert not set(gtr) & set(gte), 'study leakage between train and test'
    assert list(Xtr.columns) == list(Xte.columns)
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    results = {}
    for name, make in candidates().items():
        tr, va, sd = cv_scores(make, Xtr, ytr, gtr, cv)
        results[name] = {'train_auc': tr, 'cv_auc': va, 'cv_auc_std': sd, 'overfit_gap': tr - va}
        print(f'{name:14s} train {tr:.3f}  cv {va:.3f}±{sd:.3f}  gap {tr - va:+.3f}', flush=True)
    top = max(r['cv_auc'] for r in results.values())
    best = min((k for k, r in results.items() if r['cv_auc'] >= top - 0.01), key=lambda k: results[k]['overfit_gap'])
    make = candidates()[best]

    rng = np.random.default_rng(SEED)
    y_null = ytr.copy()
    for a in set(gtr): m = gtr == a; y_null[m] = rng.permutation(ytr[m])  # keeps each study's flight share
    null_auc = cv_scores(make, Xtr, y_null, gtr, cv)[1]

    model = fit(make(), Xtr, ytr, study_weights(gtr))
    p_tr, p_te = model.predict_proba(Xtr)[:, 1], model.predict_proba(Xte)[:, 1]
    sel, lr = model.steps[0][1], model.steps[-1][1]
    coef = pd.Series(lr.coef_[0], index=Xtr.columns[sel.get_support()])
    top_genes = coef.reindex(coef.abs().nlargest(20).index)
    names = gene_symbols(top_genes.index)
    report = {'selected_model': best, 'cv_by_model': results,
              'train': metrics(ytr, p_tr, study_weights(gtr)), 'test': metrics(yte, p_te, study_weights(gte)),
              'within_study_shuffled_cv_auc': null_auc,
              'rows': {'train': len(ytr), 'test': len(yte)}, 'studies': {'train': len(set(gtr)), 'test': len(set(gte))},
              'top_genes': [{'ensembl': i, 'symbol': names[i], 'coef': float(c), 'direction': 'up in flight' if c > 0 else 'down in flight'}
                            for i, c in top_genes.items()]}
    report['train']['within_study_auc_mean'], _ = within_study_auc(ytr, p_tr, gtr)
    report['test']['within_study_auc_mean'], report['test']['mixed_studies'] = within_study_auc(yte, p_te, gte)
    report['checks'] = {
        'no_study_overlap': True,
        'within_study_shuffle_near_chance': abs(null_auc - 0.5) < 0.08,
        'train_test_gap_ok': report['train']['auc_study_weighted'] - report['test']['auc_study_weighted'] < 0.15,
        'beats_chance_within_study_on_test': report['test']['within_study_auc_mean'] > 0.6,
    }
    MODELS.mkdir(exist_ok=True)
    joblib.dump({'model': model, 'genes': list(Xtr.columns)}, MODELS / 'osdr_genes_model.joblib')
    (MODELS / 'osdr_genes_metrics.json').write_text(json.dumps(report, indent=2, default=float), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('selected_model', 'train', 'test', 'within_study_shuffled_cv_auc', 'checks')},
                     indent=2, default=float))
    print('top genes:', ', '.join(f"{t['symbol'] or t['ensembl']} ({t['direction']})" for t in report['top_genes'][:10]))
    return report


def score_vst(df: pd.DataFrame) -> pd.DataFrame:
    """Score one study's GeneLab VST counts (genes x samples). Scores are relative to that batch."""
    bundle = joblib.load(MODELS / 'osdr_genes_model.joblib')
    df = df.loc[df.index.astype(str).str.startswith('ENSMUSG')].apply(pd.to_numeric, errors='coerce').astype('float32')
    if df.shape[1] < 4: raise ValueError('need >=4 samples from one study: scores are relative to the batch')
    coverage = df.index.isin(bundle['genes']).sum() / len(bundle['genes'])
    if coverage < 0.5: raise ValueError(f'only {coverage:.0%} of model genes found; expected a mouse GeneLab VST counts file')
    X = zscore_within(df).reindex(bundle['genes']).fillna(0).T
    out = pd.DataFrame({'sample_name': X.index, 'p_space_flight': bundle['model'].predict_proba(X)[:, 1].round(4)})
    out.attrs['gene_coverage'] = float(coverage)
    return out


def predict(path):
    out = score_vst(pd.read_csv(path, index_col=0))
    dest = Path(path).with_suffix('.predictions.csv'); out.to_csv(dest, index=False)
    print(out.to_string(index=False)); print(f"wrote {dest} (model gene coverage {out.attrs['gene_coverage']:.1%})")

if __name__ == '__main__':
    predict(sys.argv[2]) if sys.argv[1:2] == ['predict'] else train()
