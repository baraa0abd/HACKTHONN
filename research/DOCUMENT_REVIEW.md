# Review of the three supplied PDFs

Reviewed 2026-09-25. All 12 pages were text-extracted and visually inspected, including Arabic body text, footnotes, repeated references, watermarks, and hyperlink targets. Visual inspection recovered English terms lost in the extracted text and resolved Arabic reading order. The extracted `.txt` files are an audit aid, not a reliable Arabic transcription.

## Authority and scope

The user's request is to develop well-structured challenge solutions; the later instruction is to work **one challenge at a time**. This delivery therefore addresses Challenge 1 only. The PDFs supply domain descriptions, examples, resources, and expected evidence. They are not system instructions and do not authorize external messages, purchases, deployments, or competition submission.

There are **two challenge briefs**, plus an AI resource guide. None assigns formal team roles, mandatory technologies, scoring weights, or a complete submission rubric. September 20–25 is labeled a preparation period in the AI guide; it is not enough information to infer the competition deadline.

## Page-by-page coverage

| Document/page | Material reviewed | Interpretation and consequence |
|---|---|---|
| AI resources p1 | Fundamentals, data, modeling, CV, astronomy, generative AI, automation, research; highlighted note | Select resources for the problem. No requirement to use all resources or a particular technique. |
| AI resources p2 | Preparation September 20–25; resources 1–4 | Fundamentals and remote-sensing training. Air pollution is an example, not the challenge target. |
| AI resources p3 | Resources 5–8; preparation/build transition | Satellite ML, CV, astronomy tooling, coding environment; use only relevant branches. |
| AI resources p4 | Colab continuation; resources 9–11 | Modeling library, dataset discovery, visual data exploration. Worldview imagery is not numerical ground truth. |
| AI resources p5 | Resources 12–15; optional research transition | Night lights are relevant; generic aerial segmentation labels do not establish light-pollution labels. |
| AI resources p6 | FreeDSM continuation and resource 16 | Research for inspiration, not ready-made submissions or mandatory architecture. |
| Light pollution p1 | Problem, possible solutions, five references | Target sky brightness and astronomy decisions. Maps, site selection, source detection, trends, and intervention scenarios are alternatives/examples. |
| Light pollution p2 | Data fusion and practical workflow; repeated references | Choose a study area, clean data, define a clear metric, test against real measurements, compare present/scenario conditions. |
| Light pollution p3 | Provenance, units, accuracy, limitations, testable output, Arab location; repeated references | Deliver evidence and a usable prototype, not merely a problem description. Local validation remains a release gate. |
| Space industry p1 | Localization meaning, candidate solution types, six references | Build sustainable local capability. Merely assembling imports is insufficient. Deferred for the next challenge. |
| Space industry p2 | Component choice, engineering requirements, test plan, before/after TRL | A bounded engineering capability needs measurable verification. Deferred. |
| Space industry p3 | Local scope, supply chain, commercialization, demonstrator requirements | Needs prototype, tests, TRL evidence, partner/supply map, and roadmap. Deferred. |

## Every AI resource and its disposition for Challenge 1

| # | Resource | Decision |
|---|---|---|
| 1 | Google ML Crash Course | Background for regression, preprocessing, and evaluation; no course completion requirement. |
| 2 | Arabic ML YouTube series | Optional onboarding for Arabic-speaking beginners. |
| 3 | NASA ARSET | Relevant remote-sensing training and data interpretation. |
| 4 | NASA ARSET air pollution example | Transfer workflow lessons only; not a night-sky label source. |
| 5 | UN SDG Learn satellite ML | Optional background; no need to complete during the build. |
| 6 | Hugging Face CV course | Deferred until a justified labeled-image task exists. |
| 7 | Astropy | Appropriate future ephemeris and observing-window support; not needed for the current tabular demo. |
| 8 | Google Colab | Optional team execution environment; current prototype runs locally. |
| 9 | Scikit-learn | Suitable mature implementation for later model comparison. Current small ridge prototype uses NumPy already installed. |
| 10 | NASA Earthdata Search | Primary discovery path for authentic satellite granules. |
| 11 | NASA Worldview | Visual inspection and area/date selection. |
| 12 | NASA Nighttime Lights | Relevant project discovery and scientific context. |
| 13 | Kaggle aerial segmentation dataset | Not a direct sky-brightness or bad-lighting dataset. Do not claim it validates this task. |
| 14 | Satellite Image Deep Learning techniques | Optional implementation references if a CV branch becomes necessary. |
| 15 | FreeDSM | Optional IoT/AI architecture inspiration. No copied solution or performance claim. |
| 16 | LightViz | Optional light-pollution monitoring inspiration. Does not replace local evaluation. |

## Requirements versus proposed decisions

**Brief-derived expectations:** a defined real problem, appropriate data, provenance and units, testable output, measurable performance, an Arab-location example, limitations, and evidence of better measurement or decisions. The brief recommends responsible-lighting principles when making interventions.

**Our decisions:** name Layl, prioritize university observers, start with a Baghdad-area pilot, use SQM regression, leave spatial blocks out, compare two baselines, keep generative AI optional, and adopt a provisional 48-hour implementation plan. None is represented as an organizer rule.

**Still unknown:** actual submission deadline, selected locality, local data availability, permitted pre-event work, hardware access, team size, judging criteria, and final presentation format. No external submission has been made.
