# Team execution and pitch

## Proposed ownership

| Role | Accountability | Concrete output |
|---|---|---|
| Systems/mission lead | Payload requirement, constraints, acceptable tradeoffs | Approved mission assumptions and acceptance criteria |
| EPS engineer | Power model, interfaces, excluded physics | Reviewed equations and component assumptions |
| Software engineer | Solver, tests, packaging, reproducibility | Maintained implementation and reproducible release |
| Verification/lab lead | Independent checks and measured validation | Test procedure, calibration records, validation report |
| Product/localization lead | Pilot need, supply dependencies, sustainment | Partner verification and deployment/support plan |

These roles are proposed by this solution; the PDFs do not assign them. With a small team, combine roles but retain independent review of the calculations and results.

## Hackathon execution

Provisional schedule; confirm actual duration and allowed pre-event work with the organizers.

| Window | Work | Exit condition |
|---|---|---|
| 0–4 hours | Confirm target user, required duty, and available evidence | Fixed scope and assumptions |
| 4–12 hours | Implement and independently check model | Analytical test cases pass |
| 12–22 hours | Run requirement checks and stress search | Reproducible failure and candidate comparison |
| 22–30 hours | Build evidence report and review corner cases | Report matches raw results |
| 30–36 hours | Document local development, dependencies, and TRL | Every claim mapped to evidence or marked pending |
| 36–42 hours | Independent reproduction and tradeoff review | Team can explain why a candidate passes and what it cannot prove |
| 42–48 hours | Rehearse, freeze package, prepare fallback | Reliable demonstration and coherent pitch |

The software proof of concept is already implemented. Bench integration is a later milestone unless actual facilities and operators are available; do not promise a fabricated hardware demonstration.

## Three-minute pitch

**0:00–0:25 — Problem and local capability**

“Building a space industry requires the ability to understand and verify spacecraft data locally. OrbitBench converts authentic CubeSat flight telemetry into a repeatable EPS health and energy decision record.”

**0:25–0:50 — Product**

“OrbitBench is a locally maintainable engineering tool. The team has the source, equations, tests, and reports. It can be extended toward a university-operated validation service.”

**0:50–1:35 — Live evidence**

Open `output/real/flight_data_report.html`. Show the pinned BIRDS commit, the four-spacecraft overview, then the table of every operational recording. Point out that malformed rows are counted and rejected.

“This run analyzed 48 on-orbit recordings and 31,725 accepted samples. Every power and energy result comes from calibrated telemetry channels and recorded timestamps.”

**1:35–2:00 — Explain the real tradeoff**

“The explainable health rules identify RAAVANA's inactive PY face and three battery-voltage excursions for investigation. These are transparent rule outputs, not unsupported AI diagnoses.”

**2:00–2:30 — Verification and maturity**

“Eight automated tests check the numerical implementation against independent arithmetic and failure cases. The software is a proof of concept. Our next validation step is a calibrated bench comparison; we do not claim hardware qualification or a certified TRL.”

**2:30–3:00 — Localization and request**

“The local capability is the engineering software, maintenance knowledge, test automation, and future instrument adapters. Our proposed pilot partner is a university CubeSat team with electronics-lab access. We seek a real load profile and supervised validation campaign.”

## Judge questions

| Question | Defensible answer |
|---|---|
| What exactly have you localized? | A maintainable analysis and verification software capability has been delivered. Local operational independence still needs a team handoff and pilot. |
| Is this just a simulator? | The solver is the core; the deliverable adds explicit requirements, independent tests, stress search, raw evidence, and a route to validation services. |
| Why not manufacture a satellite component? | That would require hardware and facilities not provided. The brief permits design/test tools and simulation, so we selected a capability we can demonstrate honestly. |
| Where is the AI? | The delivered optimizer is transparent exhaustive search, not ML. A learned residual model is a later option only when authentic bench data justify it. |
| Is this real data? | Yes. It is the authors' public BIRDS on-orbit EPS dataset, pinned to an exact commit and verified by workbook hashes. |
| Does it certify 65% payload duty? | No public dataset can certify an unmeasured new payload. OrbitBench now provides the real ingestion and verification pipeline; the gate is a payload-specific hardware-in-the-loop dataset. |
| What TRL is it? | Provisional TRL 2 to candidate TRL 3 for the software concept, subject to independent review. No hardware TRL is inferred. |
| What is the evidence of savings? | None yet. Search time is measured, but cost and human-time savings require a controlled pilot comparison. |
| What is novel? | The proposed value is a maintainable local engineering workflow. Novel physics or global novelty has not been established. |

## Submission checklist

- Confirm organizer requirements, allowed prior work, and submission format.
- Submit the engineering dossier, source, example assumptions, tests, and evidence outputs together.
- Retain the analytical-prototype notice on screenshots and slides.
- Include the mission tradeoff, model exclusions, narrow energy margin, and unresolved validation work.
- Present suppliers and partners as proposed until verified.
- Separate software maturity from hardware/spacecraft maturity.
- Have another member reproduce the example without editing results.
- Use the generated offline report if internet access is unavailable.
- Do not claim guaranteed funding, customer adoption, flight readiness, or measured localization savings.
