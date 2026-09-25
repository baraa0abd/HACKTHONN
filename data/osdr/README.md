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

## Results (`models/osdr_flight_metrics.json`)
| | AUC |
|---|---|
| Train (study-weighted) | 0.709 |
| Group-CV on train, `logreg C=0.1` | 0.662 ± 0.091 |
| **Held-out studies (test)** | **0.684** |
| Shuffled labels (should be ~0.5) | 0.517 |
| Within one study (flight vs control, test) | 0.577 |

The train/test gap is 0.03. Gradient boosting fit the training data better but generalised worse (gap +0.13), so it was rejected.

**Limitation:** inside a study, flight and control samples usually share identical metadata. The model ranks studies well but mostly can't tell samples apart within a study. Adding assay measurements, such as OSDR processed gene-expression data, is the upgrade that would fix this.
