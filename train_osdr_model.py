"""Train and honestly evaluate the OSDR Space Flight vs Control classifier.

    python train_osdr_model.py                 # audit, select, train, test, save
    python train_osdr_model.py predict in.csv  # write in.predictions.csv

Guards against overfitting and leakage:
  * test.csv = whole studies never seen in training; it is scored once, after selection.
  * model selection uses StratifiedGroupKFold on train only (folds never share a study).
  * every study weighs the same (weight 1/rows), so one 6k-row study cannot dominate.
  * features that split flight/control *inside* studies are dropped as label proxies.
  * a shuffled-label run must score ~0.5, proving the pipeline cannot invent signal.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

ROOT = Path(__file__).resolve().parent
DATA, MODELS = ROOT / 'data' / 'osdr', ROOT / 'models'
IDS, SEED = ['accession', 'assay_name', 'sample_name'], 42
MAX_GAP = 0.15  # models whose train AUC beats grouped-CV AUC by more are treated as overfit
PROXY_RATE = 0.10  # drop a feature if it perfectly splits flight/control inside >=10% of mixed studies


def load(name):
    df = pd.read_csv(DATA / name, dtype=str, keep_default_na=False, encoding='utf-8-sig')
    return df, df.pop('label').astype(int).to_numpy()


def study_weights(groups):
    """Each study weighs the same; scaled to mean 1 so a model's C means what it says."""
    s = pd.Series(groups); w = (1 / s.map(s.value_counts())).to_numpy()
    return w * len(w) / w.sum()


def proxy_audit(X, y, groups):
    """Share of mixed-label studies in which the feature alone separates flight from control perfectly."""
    mixed = [g for g, ys in pd.Series(y).groupby(groups) if ys.nunique() == 2]
    rates = {}
    for c in X.columns:
        hits = 0
        for g in mixed:
            m = groups == g; v = X.loc[m, c]
            if v.nunique() > 1 and pd.crosstab(v, y[m]).gt(0).sum(axis=1).eq(1).all(): hits += 1
        rates[c] = hits / len(mixed)
    return rates


def candidates(n_feats):
    onehot = lambda: OneHotEncoder(handle_unknown='infrequent_if_exist', min_frequency=20, sparse_output=True)
    ordinal = lambda: OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1, encoded_missing_value=-1,  # HGB reads negatives as missing
                                     min_frequency=20, max_categories=250)
    out = {f'logreg C={C}': lambda C=C: make_pipeline(onehot(), LogisticRegression(C=C, max_iter=3000))
           for C in (0.01, 0.1, 1.0)}
    for depth, l2 in ((3, 1.0), (5, 1.0), (None, 0.0)):
        out[f'hgb depth={depth} l2={l2}'] = lambda d=depth, l=l2: make_pipeline(
            ordinal(), HistGradientBoostingClassifier(categorical_features=[True] * n_feats, max_depth=d, l2_regularization=l,
                                                      learning_rate=0.05, max_iter=400, early_stopping=True,
                                                      validation_fraction=0.15, random_state=SEED))
    return out


def select(results):
    """Drop overfit candidates, then take the smallest gap within 0.01 of the best CV AUC (1-SE style)."""
    ok = {k: r for k, r in results.items() if r['overfit_gap'] <= MAX_GAP} or results
    top = max(r['cv_auc'] for r in ok.values())
    return min((k for k, r in ok.items() if r['cv_auc'] >= top - 0.01), key=lambda k: ok[k]['overfit_gap'])


def fit(model, X, y, w):
    model.fit(X, y, **{model.steps[-1][0] + '__sample_weight': w}); return model


def cv_scores(make, X, y, groups, splitter):
    tr_auc, va_auc = [], []
    for tr, va in splitter.split(X, y, groups if isinstance(splitter, StratifiedGroupKFold) else None):
        m = fit(make(), X.iloc[tr], y[tr], study_weights(groups[tr]))
        tr_auc.append(roc_auc_score(y[tr], m.predict_proba(X.iloc[tr])[:, 1], sample_weight=study_weights(groups[tr])))
        va_auc.append(roc_auc_score(y[va], m.predict_proba(X.iloc[va])[:, 1], sample_weight=study_weights(groups[va])))
    return float(np.mean(tr_auc)), float(np.mean(va_auc)), float(np.std(va_auc))


def metrics(y, p, w):
    pred = (p >= 0.5).astype(int)
    return {'auc_study_weighted': roc_auc_score(y, p, sample_weight=w), 'auc_row': roc_auc_score(y, p),
            'accuracy_study_weighted': accuracy_score(y, pred, sample_weight=w),
            'f1_flight': f1_score(y, pred), 'brier': brier_score_loss(y, p, sample_weight=w)}


def train():
    Xtr, ytr = load('train.csv'); Xte, yte = load('test.csv')
    gtr, gte = Xtr.pop('accession').to_numpy(), Xte.pop('accession').to_numpy()
    Xtr, Xte = Xtr.drop(columns=IDS[1:]), Xte.drop(columns=IDS[1:])
    assert not set(gtr) & set(gte), 'study leakage between train and test'

    rates = proxy_audit(Xtr, ytr, gtr)
    dropped = sorted(c for c, r in rates.items() if r >= PROXY_RATE)
    feats = [c for c in Xtr.columns if c not in dropped]
    print('label-proxy features dropped:', {c: round(rates[c], 2) for c in dropped})
    Xtr, Xte = Xtr[feats], Xte[feats]

    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    results = {}
    for name, make in candidates(len(feats)).items():
        tr, va, sd = cv_scores(make, Xtr, ytr, gtr, cv)
        results[name] = {'train_auc': tr, 'cv_auc': va, 'cv_auc_std': sd, 'overfit_gap': tr - va}
        print(f'{name:24s} train {tr:.3f}  cv {va:.3f}±{sd:.3f}  gap {tr - va:+.3f}')
    best = select(results)

    make = candidates(len(feats))[best]
    shuffled = np.random.default_rng(SEED).permutation(ytr)
    null_auc = cv_scores(make, Xtr, shuffled, gtr, cv)[1]
    random_split_auc = cv_scores(make, Xtr, ytr, gtr, StratifiedKFold(5, shuffle=True, random_state=SEED))[1]

    model = fit(make(), Xtr, ytr, study_weights(gtr))
    p_tr, p_te = model.predict_proba(Xtr)[:, 1], model.predict_proba(Xte)[:, 1]
    report = {'selected_model': best, 'features': feats, 'dropped_label_proxies': {c: rates[c] for c in dropped},
              'cv_by_model': results, 'train': metrics(ytr, p_tr, study_weights(gtr)), 'test': metrics(yte, p_te, study_weights(gte)),
              'baseline_test_auc': 0.5, 'shuffled_label_cv_auc': null_auc,
              'random_row_split_cv_auc': random_split_auc,
              'rows': {'train': len(ytr), 'test': len(yte)}, 'studies': {'train': len(set(gtr)), 'test': len(set(gte))}}
    # Separating flight from control *inside* one study is the hard, useful task; metadata rarely can.
    within = [roc_auc_score(yte[gte == g], p_te[gte == g]) for g in sorted(set(gte)) if len(set(yte[gte == g])) == 2]
    report['test']['within_study_auc_mean'] = float(np.mean(within))
    report['test']['mixed_studies'] = len(within)
    report['checks'] = {
        'no_study_overlap': True,
        'shuffled_labels_near_chance': abs(null_auc - 0.5) < 0.08,
        'train_test_gap_ok': report['train']['auc_study_weighted'] - report['test']['auc_study_weighted'] < 0.15,
        'beats_baseline_on_test': report['test']['auc_study_weighted'] > 0.55,
    }
    MODELS.mkdir(exist_ok=True)
    joblib.dump({'model': model, 'features': feats}, MODELS / 'osdr_flight_model.joblib')
    (MODELS / 'osdr_flight_metrics.json').write_text(json.dumps(report, indent=2, default=float), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('selected_model', 'train', 'test', 'shuffled_label_cv_auc',
                                             'random_row_split_cv_auc', 'checks')}, indent=2, default=float))
    return report


_bundle = None


def score(df: pd.DataFrame):
    """p(Space Flight) for rows of OSDR metadata; unknown columns ignored, missing ones blank."""
    global _bundle
    _bundle = _bundle or joblib.load(MODELS / 'osdr_flight_model.joblib')
    X = df.reindex(columns=_bundle['features'], fill_value='').fillna('').astype(str).apply(lambda s: s.str.strip().str.lower())
    return _bundle['model'].predict_proba(X)[:, 1]


def predict(path):
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding='utf-8-sig')
    df['p_space_flight'] = score(df).round(4)
    out = Path(path).with_suffix('.predictions.csv'); df.to_csv(out, index=False, encoding='utf-8-sig')
    print(f'wrote {out}')

if __name__ == '__main__':
    predict(sys.argv[2]) if sys.argv[1:2] == ['predict'] else train()
