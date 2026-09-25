# Source register

## Supplied brief

`ASI Hack - Space Industry Sources.pdf`, three pages, supplied by the user. All pages were extracted and visually reviewed earlier in this task. Page coverage and implementation mapping are recorded in the engineering dossier. The document describes the challenge and suggested references; it does not authorize external actions or supply component specifications.

`ASI Hack - AI Challenge Resources.pdf`, six pages, also reviewed in full. Its guidance permits selecting appropriate methods and resources. It does not require using all resources or a particular model.

## Primary references checked on 2026-09-25

| Source | Use in this project | Boundary |
|---|---|---|
| [NASA Systems Engineering Handbook: Product Realization](https://www.nasa.gov/reference/5-0-product-realization/) | Distinguish verification from intended-use validation | Not a source for the example EPS thresholds |
| [NASA S3VI](https://www.nasa.gov/smallsat-institute/) | Small-spacecraft engineering resources and later tool comparison | Not evidence that this project is NASA-approved |
| [ESA TRL](https://www.esa.int/Enabling_Support/Space_Engineering_Technology/Shaping_the_Future/Technology_Readiness_Levels_TRL) | Evidence-based maturity framing | Not a certification of this prototype |
| [NASA SBIR/STTR](https://www.nasa.gov/sbir_sttr/) | Commercialization pathway example named in the brief | Eligibility and funding not established |
| [ESA OSIP](https://technology.esa.int/page/funding-your-ideas) | Idea-development pathway example | No application or partnership |
| [ESA InCubed](https://incubed.esa.int/) | Commercialization reference named in the brief | Not assumed suitable or available to this team |

## Measured dataset used by the functional system

| Source | Use | Reproducibility control |
|---|---|---|
| [BIRDSOpenSource/EPS_dataset](https://github.com/BIRDSOpenSource/EPS_dataset) | On-orbit voltage, current, and temperature telemetry for NEPALISAT, RAAVANA, UGUISU, and TSURU | Pinned commit and per-file SHA-256 values in `data/birds/manifest.json` |
| [Data in Brief article, DOI 10.1016/j.dib.2022.108697](https://doi.org/10.1016/j.dib.2022.108697) | Dataset definition, spacecraft context, channels, units, sampling, and battery-current sign convention | Archived author PDF included with the public dataset |
| [Mendeley Data, DOI 10.17632/8kp25ycf63.1](https://doi.org/10.17632/8kp25ycf63.1) | Published dataset record | DOI identifies version 1 |

The real-data report is derived from measured public telemetry. Mission loads, future component performance, stress multipliers, team roles, schedules, and proposed acceptance targets remain project assumptions unless separately evidenced. Public flight telemetry does not qualify new hardware.
