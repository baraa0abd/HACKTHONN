"""Learn P(clear night) from the day-ahead forecast and test it on a future year.

    python train_sky_model.py

Honest-evaluation rules:
  * temporal split: train < TEST_FROM, test = the following 12 months (a full seasonal cycle).
  * model choice uses forward-chaining CV inside train only (never a random split of days).
  * baselines on the same test nights: the raw forecast taken literally, and the hand-weighted
    formula currently in decision_engine.py.
"""
from __future__ import annotations
import json
from pathlib import Path
import joblib, numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from train_osdr_model import select

ROOT = Path(__file__).resolve().parent
DATA, MODELS = ROOT / 'data' / 'sky' / 'nights.csv', ROOT / 'models'
FEATURES = ['fc_cloud_mean', 'fc_cloud_max', 'fc_clear_hours', 'fc_rh_mean', 'fc_wind_max', 'fc_precip_sum',
            'month_sin', 'month_cos', 'site_light']
TEST_FROM, SEED = '2025-10-01', 42
MAX_WASTED_TRIPS = 0.02  # product rule: at most 2% of GO nights may turn out cloudy (today's engine level)


def candidates():
    out = {f'logreg C={C}': lambda C=C: make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=2000)) for C in (0.01, 0.1, 1.0)}
    for depth, leaf in ((2, 50), (3, 50), (None, 20)):
        out[f'hgb depth={depth} leaf={leaf}'] = lambda d=depth, l=leaf: HistGradientBoostingClassifier(
            max_depth=d, min_samples_leaf=l, learning_rate=0.05, max_iter=300, l2_regularization=1.0,
            early_stopping=True, validation_fraction=0.15, random_state=SEED)
    return out


def date_folds(dates, n=4):
    """Forward-chaining folds over whole days: validation days always come after training days."""
    days = np.array(sorted(set(dates)))
    for tr, va in TimeSeriesSplit(n_splits=n).split(days):
        yield np.flatnonzero(np.isin(dates, days[tr])), np.flatnonzero(np.isin(dates, days[va]))


def scores(y, p, threshold=0.5):
    pred = (p >= threshold).astype(int)
    return {'auc': roc_auc_score(y, p), 'brier': brier_score_loss(y, np.clip(p, 0, 1)),
            'f1_clear': f1_score(y, pred), 'precision_clear': precision_score(y, pred, zero_division=0),
            'recall_clear': recall_score(y, pred),
            'wasted_trip_rate': float(((pred == 1) & (y == 0)).sum() / max(1, pred.sum())),   # said clear, was cloudy
            'missed_clear_rate': float(((pred == 0) & (y == 1)).sum() / max(1, (y == 1).sum()))}


def engine_formula(df):
    """decision_engine.py weights (backtest variant without AOD) applied to the same forecast."""
    cloud, rh, wind = df.fc_cloud_mean / 100, df.fc_rh_mean, df.fc_wind_max
    return (1 - (0.60 * cloud + 0.20 * ((rh - 45) / 55).clip(0) + 0.20 * (wind / 45).clip(upper=1))).clip(0).to_numpy()


def reliability(y, p):
    bins = [(0, .25), (.25, .5), (.5, .75), (.75, 1.01)]
    return [{'predicted': f'{lo:.2f}-{min(hi, 1):.2f}', 'nights': int(m.sum()), 'actual_clear_rate': round(float(y[m].mean()), 3)}
            for lo, hi in bins if (m := (p >= lo) & (p < hi)).any()]


def train():
    df = pd.read_csv(DATA).sort_values(['date', 'site_id']).reset_index(drop=True)
    tr, te = df[df.date < TEST_FROM], df[df.date >= TEST_FROM]
    assert tr.date.max() < te.date.min(), 'temporal leakage'
    Xtr, ytr, Xte, yte = tr[FEATURES], tr.clear_night.to_numpy(), te[FEATURES], te.clear_night.to_numpy()
    results = {}
    for name, make in candidates().items():
        trs, vas = [], []
        for a, b in date_folds(tr.date.to_numpy()):
            m = make().fit(Xtr.iloc[a], ytr[a])
            trs.append(roc_auc_score(ytr[a], m.predict_proba(Xtr.iloc[a])[:, 1]))
            vas.append(roc_auc_score(ytr[b], m.predict_proba(Xtr.iloc[b])[:, 1]))
        results[name] = {'train_auc': float(np.mean(trs)), 'cv_auc': float(np.mean(vas)), 'cv_auc_std': float(np.std(vas)),
                         'overfit_gap': float(np.mean(trs) - np.mean(vas))}
        print(f"{name:22s} train {results[name]['train_auc']:.3f}  cv {results[name]['cv_auc']:.3f}±{results[name]['cv_auc_std']:.3f}  gap {results[name]['overfit_gap']:+.3f}")
    best = select(results)
    # GO threshold from out-of-fold train predictions only: highest recall with wasted trips <= MAX_WASTED_TRIPS.
    oof_p, oof_y = [], []
    for a, b in date_folds(tr.date.to_numpy()):
        oof_p.append(candidates()[best]().fit(Xtr.iloc[a], ytr[a]).predict_proba(Xtr.iloc[b])[:, 1]); oof_y.append(ytr[b])
    oof_p, oof_y = np.concatenate(oof_p), np.concatenate(oof_y)
    go = min((t for t in np.arange(0.50, 0.99, 0.01) if scores(oof_y, oof_p, t)['wasted_trip_rate'] <= MAX_WASTED_TRIPS), default=0.9)
    go = round(float(go), 2)
    model = candidates()[best]().fit(Xtr, ytr)
    p_tr, p_te = model.predict_proba(Xtr)[:, 1], model.predict_proba(Xte)[:, 1]

    raw_fc = te.fc_clear_hours.to_numpy() / 10  # "forecast says >=6 clear hours" taken literally
    formula = engine_formula(te)
    report = {
        'selected_model': best, 'features': FEATURES, 'cv_by_model': results,
        'split': {'train': [tr.date.min(), tr.date.max()], 'test': [te.date.min(), te.date.max()],
                  'train_nights': len(tr), 'test_nights': len(te), 'test_clear_rate': float(yte.mean())},
        'go_threshold': go, 'go_threshold_rule': f'lowest p with out-of-fold wasted-trip rate <= {MAX_WASTED_TRIPS}',
        'train': scores(ytr, p_tr, go), 'test': scores(yte, p_te, go), 'test_at_0.5': scores(yte, p_te),
        'baselines_test': {'raw_forecast_rule': scores(yte, raw_fc, threshold=0.6),
                           'current_engine_formula': scores(yte, formula, threshold=0.72),
                           'always_clear': scores(yte, np.ones(len(yte)) * yte.mean() + 1e-9, threshold=0)},
        'test_reliability': reliability(yte, p_te),
        'test_by_site': {s: scores(yte[m], p_te[m]) for s in sorted(te.site_id.unique()) if len(set(yte[m := (te.site_id == s).to_numpy()])) == 2},
    }
    report['checks'] = {
        'temporal_split': True,
        'train_test_gap_ok': report['train']['auc'] - report['test']['auc'] < 0.10,
        'beats_raw_forecast_brier': report['test']['brier'] < report['baselines_test']['raw_forecast_rule']['brier'],
        'wasted_trips_within_rule_on_test': report['test']['wasted_trip_rate'] <= MAX_WASTED_TRIPS + 0.01,
        'fewer_missed_nights_than_engine': report['test']['missed_clear_rate'] < report['baselines_test']['current_engine_formula']['missed_clear_rate'],
    }
    MODELS.mkdir(exist_ok=True)
    joblib.dump({'model': model, 'features': FEATURES, 'go_threshold': go}, MODELS / 'sky_clear_model.joblib')
    (MODELS / 'sky_clear_metrics.json').write_text(json.dumps(report, indent=2, default=float), encoding='utf-8')
    show = lambda s: {k: round(v, 3) for k, v in s.items()}
    print('selected', best, 'GO threshold', go)
    print('ML model   train', show(report['train'])); print('ML model   test ', show(report['test']))
    for k, v in report['baselines_test'].items(): print(f'{k:24s}', show(v))
    print('reliability', report['test_reliability']); print('checks', report['checks'])
    return report


_bundle = None


def clear_probability(nights: pd.DataFrame):
    """P(clear night) for rows holding the FEATURES columns (built from a live forecast)."""
    global _bundle
    _bundle = _bundle or joblib.load(MODELS / 'sky_clear_model.joblib')
    return _bundle['model'].predict_proba(nights[_bundle['features']])[:, 1]


if __name__ == '__main__':
    train()
