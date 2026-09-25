# Real-data and validation protocol

This is the release protocol for Challenge 1. It separates proposed work from completed software checks. No authenticated local ground observations or satellite granules were supplied, and none are included in the current demonstration.

## A. Data acquisition and evidence

| Input | Purpose | Required evidence | Current availability |
|---|---|---|---|
| NASA Black Marble | Night-light context | Product/version, granule ID, dates, retrieval date, units, QA, spatial resolution, processing record | Reference verified; granules not acquired |
| Calibrated SQM measurements | Regression target | Instrument ID, calibration information, UTC, coordinates, protocol, repeat readings | Must be collected or obtained |
| Globe at Night | Additional ground context or compatible measurements | Download version, method field, location, time, attribution, method limitations | Website fetch returned 403; no dataset acquired |
| Weather and aerosol context | Explain variability | Source, observation time, coverage, uncertainty, missing-data handling | Not integrated |
| Candidate-site context | Practical site selection | Public access/permission, horizon obstructions, travel constraints | Not verified |

Use [NASA Earthdata Search](https://search.earthdata.nasa.gov/) to select the study area and dates. Inspect the region in [Worldview](https://worldview.earthdata.nasa.gov/). The Black Marble homepage now redirects to [NASA Earthdata's project page](https://www.earthdata.nasa.gov/data/projects/black-marble). Depending on the selected download route, an Earthdata account may be needed. Keep credentials outside the repository.

Select one corrected night-light product and freeze its version. In the Collection 2 guide, VNP46A2 is daily and VNP46A3 is monthly; the products use a 15 arc-second grid. Radiance is expressed in nW·cm⁻²·sr⁻¹. Product-specific quality flags must be decoded before analysis. [NASA Collection 2 documentation](https://landweb.modaps.eosdis.nasa.gov/data/userguide/BlackMarbleUserGuide_Collection2.0_20241203.pdf)

Do not scrape a colorized map screenshot and treat pixel colors as radiance. Preserve the original granule, its checksum, and the processing script. Read scaling, offsets, missing values, and valid ranges from the selected dataset's metadata. Keep observed and gap-filled values distinguishable. `qa_valid` in this prototype is a preprocessed Boolean, **not a raw NASA quality flag**.

For a first credible pilot, prioritize one study area with several spatially separated observing sites rather than national coverage. If local SQM records are unavailable, use the software for satellite-context exploration while arranging field measurement; do not substitute generated ground truth.

## B. File contract

`sky.py` expects one aggregated site/date record per row. This is a deliberately narrow pilot contract. Keep raw repeat readings separately. Multiple sessions on one date require a documented aggregation policy or a future session-ID schema extension.

| Column | Type and units | Meaning |
|---|---|---|
| `site_id` | Nonempty text | Stable station/candidate ID |
| `block_id` | Nonempty text | Predeclared spatial validation block |
| `date` | ISO date, YYYY-MM-DD | Aggregated observation date |
| `lat`, `lon` | Decimal degrees | WGS84 location |
| `radiance_nw_cm2_sr` | Nonnegative number, nW·cm⁻²·sr⁻¹ | Preprocessed matched satellite context |
| `cloud_fraction` | Number in [0,1] | Ground-session cloud estimate from a documented source |
| `moon_illumination` | Number in [0,1] | Ground-session illuminated lunar fraction |
| `aod` | Nonnegative dimensionless number | Aerosol optical depth from a documented product; record wavelength in manifest |
| `sqm_mag_arcsec2` | Number in (0,30), mag/arcsec² | Matched instrument reading; broad range is a software check, not a calibration guarantee |
| `qa_valid` | 0 or 1 | Explicitly accepted/rejected after your processing policy |
| `source_id` | Nonempty text | Key into the provenance manifest |
| `provenance` | Text, consistent per evaluation | E.g. synthetic or measured; never combine them in one benchmark |

The schema's minimum of 20 accepted rows across five blocks is a software guard against trivial inputs. It is **not a claim of statistical sufficiency**. The field-validation design governs sufficiency.

The current model cannot use missing AOD or lunar context. Do not replace unknown values with zero. Obtain the feature, or implement and separately validate a reduced feature model. The same rule applies to missing ground targets.

## C. Provenance manifest template

Create one record per source with the following structure. All values below are placeholders, not evidence of a download.

```json
{
  "source_id": "REPLACE_WITH_ACTUAL_SOURCE_ID",
  "source_url": "REPLACE_WITH_DOWNLOAD_OR_ARCHIVE_URL",
  "product_and_version": "REPLACE",
  "granule_or_file_id": "REPLACE",
  "retrieved_utc": "REPLACE",
  "sha256": "REPLACE",
  "license_or_attribution": "REPLACE",
  "measurement_units": "REPLACE",
  "spatial_resolution": "REPLACE",
  "observation_period_utc": "REPLACE",
  "instrument_or_sensor": "REPLACE",
  "processing_script_version": "REPLACE",
  "quality_policy": "REPLACE",
  "known_uncertainties": "REPLACE"
}
```

Add a run manifest recording software version, input hashes, feature definitions, block assignment, test cutoff date, exclusions and reasons, model configuration, and the analyst. The current CLI records the input SHA-256; the complete provenance manifest is a required addition for real data.

## D. Preprocessing workflow

1. **Freeze area and intent.** Record a bounding box, candidate locations, dates, and whether the target is dark-sky site comparison or date-specific observing conditions. Avoid changing the target after seeing model results.
2. **Inspect data coverage.** Count valid satellite observations and usable ground sessions per site. Map missingness before fitting.
3. **Decode satellite data.** Apply the selected product's metadata and quality policy. Record exclusions; do not silently turn invalid values into zeros. Audit a few values against the original files.
4. **Standardize ground records.** Preserve UTC, instrument ID, calibration, pointing, weather, and repeat readings. Keep SQM and naked-eye data separate.
5. **Align spatial support.** Extract a documented local pixel/neighborhood statistic. A distant lighting field can affect ground sky brightness, so explore larger neighborhoods only within training folds. Do not claim that one nearest pixel fully represents skyglow.
6. **Align time.** Satellite overpass time and ground-session time differ. Set an explicit matching tolerance appropriate to the product, record time gaps, and exclude pairs that violate it. A monthly composite supports monthly context, not a same-hour nowcast.
7. **Add context.** Align cloud, aerosol, lunar, and eventually solar altitude to the ground session. Lunar illumination alone does not describe the Moon's contribution if it is below the horizon.
8. **Assign blocks before fitting.** Group sites by shared light environment and geography, with buffer distances informed by spatial dependence. Do not distribute neighboring pixels randomly across train and test.
9. **Export and review.** Export the contract CSV, a quality summary, and the manifest. Have a second team member check several matched records before training.

## E. Ground-observation pilot

Proposed initial collection target: 12–20 sites spanning bright urban, fringe, and darker settings; several comparable nights per site. These are planning targets, not a power calculation or a guarantee of sufficiency. Increase coverage if blocks or conditions are poorly represented.

- Use the same calibrated instrument where practical, or cross-check instruments at the same place and time.
- Follow the instrument's documented warm-up and reading protocol. Record repeated readings, pointing, obstacles, direct light contamination, cloud conditions, and timing.
- Make matched comparisons under similar astronomical darkness and lunar conditions. Record deviations instead of silently normalizing them away.
- Record each session's site permission/access status separately from scientific brightness.
- Audit high-residual cases against original observation notes before deleting them as “outliers.”

Do not promise that all of this can be completed in a 48-hour event. If existing authentic records are unavailable, field collection is a post-hackathon milestone and must be identified as such in the pitch.

## F. Evaluation design

**Primary task:** predict held-out SQM readings for the declared use domain.

**Primary metric:** MAE in mag/arcsec². Also report RMSE, bias, per-block error, sample counts, exclusions, and residuals by brightness and conditions. Do not convert regression performance into “accuracy percent.”

**Baselines:** median target from the training partition and radiance-only regression. Same rows and folds for all models. Train preprocessing only on the training partition.

**Spatial validation:** use the supplied leave-one-block-out evaluator for early analysis. Preselect block geometry; the included synthetic block names are not a scientifically justified real geography partition.

**Final validation:** reserve untouched locations and later observation dates before tuning. If optimizing hyperparameters or selecting features, do so inside the remaining training folds. Report spatial and temporal tests separately. The current code does not implement a temporal holdout.

**Uncertainty:** use calibration data separate from model selection and final evaluation. Check empirical coverage by block and conditions before labeling intervals. Quantify uncertainty in performance differences by resampling blocks rather than treating all repeated rows as independent. With very few blocks, report that interval estimates are unstable.

**Proposed engineering acceptance gates:**

| Gate | Proposed criterion | If unmet |
|---|---|---|
| Data integrity | Every retained record has traceable source, units, and QA decision | Stop scientific evaluation |
| Added model value | At least 10% lower MAE than radiance-only baseline on untouched data, with block-level uncertainty reported | Retain simpler baseline; do not claim AI improvement |
| Intended usefulness | Initial target MAE ≤0.30 mag/arcsec², confirmed with the astronomy lead's needs | Restrict use or collect more evidence |
| Ranking relevance | Prospective comparison shows useful site-ordering performance under matched conditions | Present observations/context without recommendations |
| Reproducibility | Another team member reproduces metrics from immutable inputs | Fix the pipeline before submission |
| Local relevance | Authentic observations at the chosen Arab location | Mark brief requirement as unmet |

These thresholds are team proposals, not competition rules or universal astronomy standards. Revise them before viewing final test results if the actual observing task requires different tolerance.

## G. Intervention evaluation

Choose a small, permitted lighting change and a nearby comparable control site. Collect repeated before/after readings with unchanged instrument procedure. Match moon, cloud, and time conditions; record power and operating schedule where energy is an outcome.

For analysis, transform brightness to proportional linear luminance using `L ∝ 10^(-0.4m)`. Compare changes at intervention and control sites, accounting for repeated nights and conditions. Report the absolute and relative effect with uncertainty. The additive difference-in-differences on this linear scale is `(L_after - L_before)_intervention - (L_after - L_before)_control`. Its interpretation relies on a defensible parallel-trends assumption; a control site alone does not prove causality.

Only attribute a reduction to the intervention if design and evidence support it. The current scenario function is a sensitivity calculation, not an impact estimator.

## H. Verified software evidence

Executed on 2026-09-25 using bundled Python and NumPy:

- 96 synthetic input records; 84 retained and 12 excluded by the fixture's QA flag.
- Six spatial blocks, 14 retained rows each.
- MAE 0.1761; RMSE 0.2076 mag/arcsec².
- Radiance-only baseline MAE 0.3045; median baseline MAE 0.5500.
- Six unit tests passed: held-out-label isolation, QA exclusion, malformed/mixed inputs, duplicates/small datasets, site-block consistency, and intervention arithmetic.

These figures are reproducible software evidence only. No measured local performance or lighting outcome has been established.
