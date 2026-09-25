"""Calibrated sky-brightness regression for preprocessed, matched observations.

Raw NASA HDF ingestion and instrument calibration are deliberately separate.
All synthetic data must retain provenance='synthetic'. Larger SQM is darker.
"""
import argparse
import csv
import hashlib
import json
from datetime import date
from pathlib import Path
import numpy as np

FEATURES = ('radiance_nw_cm2_sr', 'cloud_fraction', 'moon_illumination', 'aod')


def load_rows(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def validate(rows):
    if not rows:
        raise ValueError('No observations supplied')
    seen = set()
    for row in rows:
        for key in ('site_id', 'block_id', 'date', 'provenance', 'source_id'):
            if not str(row.get(key, '')).strip():
                raise ValueError(f'Missing {key}')
        if row['provenance'] not in ('synthetic', 'measured'):
            raise ValueError('provenance must be synthetic or measured')
        for key in FEATURES + ('sqm_mag_arcsec2', 'lat', 'lon'):
            if key not in row or str(row[key]).strip() == '':
                raise ValueError(f'Missing numeric field {key}')
        identity = (row['site_id'], row['date'])
        date.fromisoformat(row['date'])
        if identity in seen:
            raise ValueError('Duplicate site/date; aggregate repeated measurements first')
        seen.add(identity)
        vals = [float(row[k]) for k in FEATURES + ('sqm_mag_arcsec2', 'lat', 'lon')]
        if not np.isfinite(vals).all():
            raise ValueError('Non-finite measurement')
        r, cloud, moon, aod, sqm, lat, lon = vals
        if r < 0 or aod < 0 or not 0 <= cloud <= 1 or not 0 <= moon <= 1:
            raise ValueError('Invalid radiance, cloud, moon, or aerosol value')
        if not 0 < sqm < 30 or not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError('Invalid SQM or coordinates')
        if str(row.get('qa_valid')) not in ('0', '1'):
            raise ValueError('qa_valid must be an explicitly decoded 0 or 1')
    site_blocks = {}
    for row in rows:
        if row['site_id'] in site_blocks and site_blocks[row['site_id']] != row['block_id']:
            raise ValueError('Each site must belong to exactly one spatial block')
        site_blocks[row['site_id']] = row['block_id']
    if len({row['provenance'] for row in rows}) != 1:
        raise ValueError('Do not mix synthetic and measured provenance in one evaluation')


def matrix(rows):
    x = np.array([[float(r[k]) for k in FEATURES] for r in rows])
    x[:, 0] = np.log1p(x[:, 0])
    return x


def fit(x, y):
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale == 0] = 1
    z = np.column_stack([np.ones(len(x)), (x - mean) / scale])
    penalty = np.eye(z.shape[1]) * 0.1
    penalty[0, 0] = 0
    coef = np.linalg.solve(z.T @ z + penalty, z.T @ y)
    return mean, scale, coef


def predict(model, x):
    mean, scale, coef = model
    return np.column_stack([np.ones(len(x)), (x - mean) / scale]) @ coef


def evaluate(rows):
    validate(rows)
    accepted = [r for r in rows if str(r['qa_valid']) == '1']
    blocks = sorted({r['block_id'] for r in accepted})
    if len(blocks) < 5 or len(accepted) < 20:
        raise ValueError('Need at least 20 valid observations in 5 spatial blocks')
    errors, baseline_errors, radiance_errors, predictions = [], [], [], []
    block_metrics = []
    for block in blocks:
        train = [r for r in accepted if r['block_id'] != block]
        test = [r for r in accepted if r['block_id'] == block]
        if len(train) < 10:
            raise ValueError('Insufficient training data after holding out a block')
        y = np.array([float(r['sqm_mag_arcsec2']) for r in train])
        model = fit(matrix(train), y)
        pred = predict(model, matrix(test))
        simple = predict(fit(matrix(train)[:, :1], y), matrix(test)[:, :1])
        truth = np.array([float(r['sqm_mag_arcsec2']) for r in test])
        radiance_errors.extend((simple-truth).tolist())
        block_metrics.append({'block': block, 'n': len(test),
                              'mae': float(np.abs(pred-truth).mean())})
        for row, value in zip(test, pred):
            actual = float(row['sqm_mag_arcsec2'])
            errors.append(float(value) - actual)
            baseline_errors.append(float(np.median(y)) - actual)
            predictions.append({**row, 'predicted_sqm': float(value),
                                'held_out_block': block, 'residual': actual - float(value)})
    err, base = np.array(errors), np.array(baseline_errors)
    # Retain OOF results for evaluation. This refit is for future observations only.
    model = fit(matrix(accepted), np.array([float(r['sqm_mag_arcsec2']) for r in accepted]))
    return {
        'provenance': accepted[0]['provenance'],
        'validation': 'leave-one-spatial-block-out; no temporal generalization claim',
        'n_input': len(rows), 'n_valid': len(accepted), 'n_rejected_qa': len(rows)-len(accepted),
        'n_blocks': len(blocks), 'mae_mag_arcsec2': float(np.abs(err).mean()),
        'rmse_mag_arcsec2': float(np.sqrt((err**2).mean())),
        'median_baseline_mae': float(np.abs(base).mean()),
        'radiance_only_baseline_mae': float(np.abs(radiance_errors).mean()),
        'block_metrics': block_metrics,
        'oof_absolute_error_p90': float(np.quantile(np.abs(err), .9)),
        'uncertainty_note': 'Descriptive held-out error, not a calibrated prediction interval.',
        'features': list(FEATURES),
        'model': {'mean': model[0].tolist(), 'scale': model[1].tolist(),
                  'coef': model[2].tolist(), 'radiance_transform': 'log1p'},
        'predictions': predictions,
    }


def scenario(sqm, artificial_fraction, reduction):
    """Assumed fraction of ground sky luminance, NOT a VIIRS conversion."""
    values = [sqm, artificial_fraction, reduction]
    if not np.isfinite(values).all() or not 0 < sqm < 30:
        raise ValueError('Invalid scenario values')
    if not 0 <= artificial_fraction < 1 or not 0 <= reduction <= 1:
        raise ValueError('Use artificial fraction in [0,1), reduction in [0,1]')
    gain = -2.5 * np.log10(1 - artificial_fraction * reduction)
    return {'assumed_artificial_fraction': artificial_fraction,
            'assumed_artificial_light_reduction': reduction,
            'sqm_before': sqm, 'sqm_after': float(sqm + gain),
            'gain_mag_arcsec2': float(gain),
            'status': 'hypothetical sensitivity analysis, not measured impact'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv')
    parser.add_argument('--output', default='output/sky_results.json')
    parser.add_argument('--report', help='Optional offline HTML evaluation report')
    args = parser.parse_args()
    result = evaluate(load_rows(args.csv))
    result['input_sha256'] = hashlib.sha256(Path(args.csv).read_bytes()).hexdigest()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding='utf-8')
    if args.report:
        from demo import render_report
        scenarios = [scenario(18, f, r) for f in (.3, .6, .9) for r in (.2, .4)]
        report = Path(args.report)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(render_report(result, scenarios), encoding='utf-8')
    print(f"MAE {result['mae_mag_arcsec2']:.3f}; provenance: {result['provenance']}")
