# NASA OSDR: Space Flight vs Control

```powershell
python build_osdr_dataset.py --refresh   # fetch all ~51k OSDR samples, write train.csv / test.csv
python train_osdr_model.py               # leakage audit, grouped CV, test once, save models/
python train_osdr_model.py predict x.csv # adds p_space_flight column
python -m unittest tests.test_osdr
```

## Data
- Source: NASA OSDR biodata API, 51,255 samples. This includes OSD-53, the astronaut blood study.
- The label is 1 for Space Flight or in-flight, and 0 for ground, vivarium or basal control. 18,679 samples have one of these labels. Rows without a label (NaN, pre-flight or post-flight) can't train a supervised model, so they're dropped.
- `train.csv` has 14,933 rows from 240 studies. `test.csv` has 3,746 rows from 91 other studies. **No study is in both files.**

## Leakage controls
- **Denylisted by name:** habitat, hardware, growth environment, location, gravity, and file names. These fields restate "ISS vs Earth" or define the control group itself.
- **Dropped by audit:** any feature that perfectly splits flight from control inside at least 10% of mixed studies. The audit removed the radiation dose, radiation dose rate, radiation source, exposure duration and vehicle fields.
- **Balanced by study:** each study carries equal weight, so the 6.5k-row OSD-366 doesn't dominate.

## Results
Both models are checked the same way:
- The test set is whole studies the model never saw during training.
- Models are chosen with study-grouped CV on train only. A candidate is rejected if its train AUC beats its CV AUC by more than 0.15.
- Every study carries equal weight.

| | Metadata model (`logreg C=0.01`) | Gene model (`k=50 C=0.001`) |
|---|---|---|
| Train AUC (study-weighted) | 0.748 | 0.815 |
| Group-CV AUC | 0.664 ± 0.077 | 0.736 ± 0.075 |
| **Test AUC, unseen studies** | **0.705** | **0.753** |
| **Within one study (flight vs control)** | 0.604 | **0.745** |
| Shuffled-label control (should be ~0.5) | 0.514 | 0.470 (labels shuffled within each study) |
| Test Brier score | see metrics JSON | 0.199 |

**Metadata model:** 67 study-design fields. It ranks studies but barely separates samples within one study.

**Gene model:** real NASA GeneLab RNA-seq for 71 mouse studies, 1,960 samples, using the VST counts from the GLbulkRNAseq pipeline. 39 studies had no processed file on OSDR and are listed in `data/osdr_genes/manifest.json`.
- Genes are z-scored within each study, without using labels. The model picks 50 genes inside each CV fold.
- Probabilities are Platt-calibrated on out-of-fold predictions. On test, predictions of 0-25% were flight 11% of the time, 25-50% → 32%, 50-75% → 51%, and 75%+ → 71%.
- The strongest genes form the circadian clock (*Per2, Per3, Dbp, Npas2, Bmal1, Nr1d2, Ciart*) plus *Cdkn1a*. Spaceflight studies report the same set.
- To score new samples, upload one study's VST file with at least 4 samples. Each score is relative to the other samples in that file.

## Use it from a phone (no app build)
```powershell
cd dashboard
python serve.py --host 0.0.0.0     # allow Python on *Private* networks if Windows Firewall asks
ipconfig                           # note the laptop's IPv4 address, e.g. 192.168.1.20
```
On a phone on the same Wi-Fi, open `http://<laptop-ip>:8903/osdr.html`.

| Endpoint | What it returns |
|---|---|
| `GET /api/osdr/metrics` | the real `models/*_metrics.json` and the dataset manifest |
| `GET /api/osdr/options` | valid form values, taken from `train.csv` |
| `POST /api/osdr/predict` | JSON of study fields in, `p_space_flight` out; unknown fields are rejected |
| `POST /api/osdr/predict-genes` | one study's GeneLab VST counts CSV in, a probability for each sample out |

**Using a Stitch design:** export the screen as HTML and save it as `dashboard/static/osdr.html`. Keep the `<script>` block, and put `data-bind="metadata_model.test.auc_study_weighted"` (any path into `/api/osdr/metrics`) on the elements that should show live values. Keep the element ids `fields`, `predict`, `result`, `prob`, `probbar`, `genes`, `vst` and `gtable`.
