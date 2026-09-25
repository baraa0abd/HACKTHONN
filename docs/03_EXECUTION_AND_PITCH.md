# Execution, ownership, and presentation

## Team roles — proposed, not assigned by the PDFs

| Role | Owned decision | Deliverable | Review partner |
|---|---|---|---|
| Astronomy/domain lead | Target, observing conditions, interpretation | Measurement protocol and usability criteria | Data lead |
| Data/geospatial lead | Provenance, QA, spatial/time matching | Immutable matched dataset and manifest | Domain lead |
| AI lead | Baselines, leakage prevention, error analysis | Reproducible evaluation and model card | Software lead |
| Software/product lead | Input contract, reliability, user workflow | Runnable prototype and evidence report | AI lead |
| Pitch/validation owner | Claim-to-evidence consistency | Demo script and evidence checklist | Entire team |

For a three-person team, combine domain/pitch and data/AI responsibilities. One person should review another's key output; do not let the person tuning the model silently redefine the final test set.

## Provisional 48-hour plan

The actual deadline is unknown. This is a planning template, not the event timetable. The user's instruction is to complete the challenges sequentially; do not start Challenge 2 during this workstream.

| Time | Work | Exit criterion |
|---|---|---|
| 0–3 h | Confirm locality, user decision, available authentic data, and evaluation target | One-page scope and data feasibility decision |
| 3–10 h | Acquire/inspect data; record provenance; match observations | Audited dataset or explicit decision that scientific validation is unavailable |
| 10–18 h | Run baselines, spatial holdouts, and residual review | Honest benchmark with counts and limitations |
| 18–28 h | Build the minimal report/workflow around verified outputs | End-to-end demonstration without manual metric editing |
| 28–34 h | Add scenario sensitivity and model evidence export | Assumptions visible and outputs reproducible |
| 34–40 h | Independent reproduction and final untouched test | Another member verifies claims and failures |
| 40–44 h | Prepare pitch, screenshots, and offline fallback | Every numeric claim linked to evidence |
| 44–48 h | Rehearse and freeze artifacts | Reliable demonstration and submission package |

If no real labels exist by the data-feasibility checkpoint, stop expanding model complexity. Demonstrate the tested analytical prototype and state that local calibration remains pending. Do not spend the rest of the event polishing invented performance.

## Backlog and definition of done

| Priority | Work item | Definition of done | Status |
|---|---|---|---|
| P0 | Read the briefs fully | All 12 pages and links reviewed; requirements extracted | Done |
| P0 | Implement numerical core | Reproducible fitting, held-out metrics, baselines | Done |
| P0 | Test data and leakage handling | Automated tests pass | Done |
| P0 | Demonstration report | Offline diagram, tables, metrics, provenance notice | Done |
| P0 | Authentic local dataset | Raw files, metadata, manifest, audited matches | Pending external data |
| P0 | Final local evaluation | Untouched sites/dates and domain review | Pending dataset |
| P1 | Supplied-data report rendering | Render CLI results with input-dependent coordinates and appropriate provenance | Implemented; authentic dataset still pending |
| P1 | Satellite ingestion | Version-specific metadata/QA handling with audited sample outputs | Not implemented |
| P1 | Conditions and support checks | Lunar/solar context, missingness policy, out-of-domain rejection | Not implemented |
| P1 | Observing-site release | Access/horizon review and uncertainty-aware comparison | Not implemented |
| P2 | Intervention field trial | Measured pre/post result with control and uncertainty | Protocol ready |
| P2 | More complex AI | Repeatable improvement over strong baselines | Conditional on evidence |

## Three-minute pitch — current truthful version

**0:00–0:25 — User problem**

“An astronomy team can find a night-light map, but it still needs to decide where to observe. Satellite brightness alone does not tell us the sky conditions measured from the ground. Layl connects those two types of evidence.”

**0:25–0:55 — Solution**

“We designed a ground-calibrated sky-quality decision tool. It evaluates predictions against withheld locations, compares a simple baseline, and shows lighting scenarios with their assumptions. Our first intended case is a Baghdad-area pilot.”

**0:55–1:40 — Demonstration**

Open `output/layl_demo.html`. Point to the synthetic-data notice first. Show the candidate diagram and explain that higher SQM is darker. Show the held-out error table and the radiance-only baseline. Explain that the fixture verifies workflow behavior and does not establish local accuracy.

“The software prevents withheld observations from entering model training. Six automated tests check this and other failure cases. The output is reproducible from a fixed input file.”

**1:40–2:15 — Action**

Show the intervention sensitivity table. “This example asks what could happen if a known share of artificial sky brightness were reduced. It is not a forecast of actual municipal savings. A field trial must measure the result.”

**2:15–2:45 — Evidence and limitations**

“The numerical core and report work. The next release gate is authentic satellite data paired with calibrated local observations, followed by untouched site and date evaluation. We do not yet claim a measured reduction or verified local prediction accuracy.”

**2:45–3:00 — Request**

“We seek an astronomy group with a calibrated sky meter and a small set of accessible local sites to validate this decision tool.”

After authentic evaluation, replace the synthetic passage with the actual sample size, split design, baseline comparison, uncertainty, and measured decision outcome. Do not retain the example metric as if it were real.

## Judge questions and defensible answers

| Question | Answer |
|---|---|
| Why use AI? | To test whether learned relationships between satellite context and local conditions improve estimation over a simpler baseline. If they do not, use the baseline. |
| What is new? | The proposed contribution is a locally validated decision workflow with explicit provenance and uncertainty. Global novelty has not been established. |
| Does a darker satellite pixel guarantee better observing? | No. The system requires ground calibration and additional observing constraints. |
| Is the data real? | Yes. The primary build uses 1,313 Iraq records from the World Bank Space2Stats annual Black Marble resource, derived from NASA satellite observations. |
| How do you prevent data leakage? | Keep sites in spatial blocks, fit preprocessing inside each fold, and test that altering held-out labels cannot alter that fold's predictions. |
| Why not a large neural network? | There is no demonstrated dataset scale or benchmark result that justifies that complexity. |
| Can you identify the offending streetlight? | Not with this prototype. That needs a ground inventory or suitable higher-resolution evidence. |
| Is the scenario causal? | No. It explores assumptions. A controlled field design is needed to estimate a real intervention effect. |
| Does the software meet every brief requirement today? | No. The testable software is implemented; real local data, scientific validation, and measured practical value remain pending. |

## Product and adoption hypothesis

Start with a university astronomy group as a pilot user. The first deliverable is a verified report for a small candidate-site set. A later service could provide recurring observation comparisons and municipal lighting-pilot analysis. Validate willingness to use/pay through actual interviews; there are no claimed customers, partnerships, revenue, or market-size figures in this package.

A sensible first agreement is access to calibration equipment and field sites, followed by a jointly reviewed pilot report. Do not build a nationwide commercial platform before demonstrating local usefulness.

## Final submission checklist

- Confirm actual organizer rules, submission format, and allowed pre-event work.
- State whether the result is a software proof of concept or field-validated prototype.
- Include requirements, method, authentic data manifest where available, baselines, tests, and limitations.
- Use `output/real/layl_real_report.html` for every demonstration and screenshot; the former generated fixture is not a submission artifact.
- Use the offline report as a demonstration fallback.
- Freeze input hashes and software revision; reproduce once on a second machine.
- Attribute resources and distinguish borrowed concepts from original implementation.
- Remove unsupported claims of accuracy, savings, site safety, or novelty.
- Move to Challenge 2 only after this workstream is reviewed or explicitly handed off.
