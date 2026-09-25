"""Validated analysis for real World Bank/NASA Black Marble Iraq night-light data."""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics

FIELDS = ("ISO_A3", "ADM1CD_c", "ADM2CD_c", "NAM_0", "NAM_1", "NAM_2", "year",
          "ntl_quality_prop_na", "ntl_quality_prop_0_good", "ntl_quality_prop_1_poor",
          "ntl_quality_prop_2_gapfilled", "ntl_nogf_5km_mean", "ntl_nogf_5km_median",
          "ntl_nogf_5km_q95")


def load_verified(data_dir: Path):
    manifest = json.loads((data_dir / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        actual = hashlib.sha256((data_dir / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Hash mismatch for {name}")
    payload = json.loads((data_dir / "worldbank_iraq_annual.json").read_text(encoding="utf-8"))
    if payload.get("count") != len(payload.get("value", [])):
        raise ValueError("API count does not match returned records")
    return payload["value"], manifest


def validate(records):
    if not records:
        raise ValueError("No night-light records")
    seen = set()
    clean = []
    for row in records:
        missing = [field for field in FIELDS if field not in row or row[field] in (None, "")]
        if missing:
            raise ValueError(f"Missing fields: {missing}")
        if row["ISO_A3"] != "IRQ" or row["NAM_0"] != "Iraq":
            raise ValueError("Non-Iraq record in filtered source")
        identity = (row["ADM2CD_c"], int(row["year"]))
        if identity in seen:
            raise ValueError(f"Duplicate ADM2/year: {identity}")
        seen.add(identity)
        numeric = {key: float(row[key]) for key in FIELDS if key.startswith("ntl_")}
        if not all(math.isfinite(value) for value in numeric.values()):
            raise ValueError(f"Non-finite value at {identity}")
        quality = [numeric[key] for key in ("ntl_quality_prop_na", "ntl_quality_prop_0_good",
                                             "ntl_quality_prop_1_poor", "ntl_quality_prop_2_gapfilled")]
        if any(value < 0 or value > 1 for value in quality) or abs(sum(quality) - 1) > .02:
            raise ValueError(f"Invalid quality proportions at {identity}")
        if numeric["ntl_nogf_5km_mean"] < 0 or numeric["ntl_nogf_5km_median"] < 0:
            raise ValueError(f"Negative radiance at {identity}")
        clean.append({**row, "year": int(row["year"]), **numeric})
    return clean


def _slope(points):
    xs = [year for year, _ in points]
    ys = [math.log1p(value) for _, value in points]
    xbar, ybar = statistics.fmean(xs), statistics.fmean(ys)
    denominator = sum((x - xbar) ** 2 for x in xs)
    return sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denominator


def analyse(records):
    rows = validate(records)
    by_district = defaultdict(list)
    by_year = defaultdict(list)
    for row in rows:
        by_district[row["ADM2CD_c"]].append(row)
        by_year[row["year"]].append(row)
    years = sorted(by_year)
    if len(years) < 5:
        raise ValueError("Need at least five annual observations")
    districts = []
    for code, group in by_district.items():
        group.sort(key=lambda x: x["year"])
        if [r["year"] for r in group] != years:
            raise ValueError(f"Incomplete annual series for {code}")
        values = [(r["year"], r["ntl_nogf_5km_mean"]) for r in group]
        first, latest = group[0], group[-1]
        percent = ((latest["ntl_nogf_5km_mean"] / first["ntl_nogf_5km_mean"] - 1) * 100
                   if first["ntl_nogf_5km_mean"] > 0 else None)
        districts.append({"adm2_code": code, "governorate": latest["NAM_1"], "district": latest["NAM_2"],
                          "first_year": years[0], "latest_year": years[-1],
                          "first_radiance": first["ntl_nogf_5km_mean"],
                          "latest_radiance": latest["ntl_nogf_5km_mean"],
                          "latest_median": latest["ntl_nogf_5km_median"],
                          "latest_q95": latest["ntl_nogf_5km_q95"],
                          "latest_good_quality": latest["ntl_quality_prop_0_good"],
                          "change_percent": percent,
                          "log_radiance_slope_per_year": _slope(values)})
    districts.sort(key=lambda x: x["latest_radiance"])
    national_series = [{"year": year,
                        "district_median_radiance": statistics.median(r["ntl_nogf_5km_mean"] for r in by_year[year]),
                        "district_p90_radiance": sorted(r["ntl_nogf_5km_mean"] for r in by_year[year])[int(.9*(len(by_year[year])-1))],
                        "median_good_quality": statistics.median(r["ntl_quality_prop_0_good"] for r in by_year[year])}
                       for year in years]
    candidates = [d for d in districts if d["latest_good_quality"] >= .9][:10]
    watchlist = sorted([d for d in districts if d["change_percent"] is not None],
                       key=lambda x: x["log_radiance_slope_per_year"], reverse=True)[:10]
    return {"source_type": "measured satellite radiance aggregated by the World Bank; no synthetic observations",
            "metric": "ntl_nogf_5km_mean: annual mean radiance excluding pixels within 5 km of gas flares",
            "unit": "nW cm-2 sr-1 (NASA Black Marble radiance)",
            "records": len(rows), "districts": len(districts), "years": years,
            "national_series": national_series, "dark_screening_candidates": candidates,
            "rapid_increase_watchlist": watchlist, "district_results": districts,
            "interpretation": "Low upward radiance is a screening signal, not measured zenith sky brightness or site approval."}
