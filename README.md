# Version-Bound Readiness Reservations for Deadline-Aware Edge–Cloud Offloading under Artifact Eviction and Updates

Research project in **Edge–Cloud Intelligence**, addressing adaptive offloading when artifact readiness and execution capacity change between discovery and task start.

**Status:** baseline selected and its core scheduling result reproduced; a
mechanism-focused simulator, ablations, tests, and seeded preliminary experiments
are complete. Instructor approval and a real container/cloud validation remain
pending. The reported improvement is simulation evidence, not a deployment claim.

## Team

| Member | Student ID | Role |
| --- | --- | --- |
| Danish Atif | I22-1095 | Primary researcher: Overleaf ownership, protocol implementation, integration and submission coordination |
| Salman Umar | I220908 | Co-researcher: literature review, experimental design, workload generation, analysis and reproducibility |

Group **G25**, **Section 7A**. Both members contribute to writing, correctness review, experiments and the defense.

## Problem

A scheduler can discover a worker with the requested artifact version and a free slot, then find that readiness has changed before dispatch. Artifact eviction, updates and competing arrivals can produce refusals, initialization delays, retries or cloud fallback. A short reservation may prevent this race, but unused reservations consume scarce cache and compute capacity.

## Research question

Can short-lived, version-bound readiness reservations improve deadline satisfaction under artifact eviction and updates, while preserving correct-version execution and acceptable worker utilization, compared with readiness advertisements and on-demand readiness checks without reservations?

## Proposed contribution

- A bounded, single-use token binding an exact artifact hash and an execution slot within one worker epoch.
- A controlled evaluation of joint readiness preservation under artifact eviction and version updates.
- Evidence about the tradeoff between deadline satisfaction, resource holding and control overhead.

## Reproducible baseline

The selected baseline is Pfandzelter and Bermbach's **Komet: A Serverless
Platform for Low-Earth Orbit Edge Services** (ACM SoCC 2024). Its official
artifact is checked out at commit `10207547993b78d812582a214e012728ee3a6fe5`
under `baseline/komet/`. The released §8.1 CSVs reproduce all migration counts
exactly and mean RTT within 0.005 ms of the paper's rounded values. See
`docs/REPRODUCTION_REPORT.md`.

## Run the current artifact

```bash
python3 scripts/reproduce_komet.py
python3 -m unittest discover -s tests -v
python3 scripts/run_experiments.py
```

The implementation uses only Python's standard library. Raw and summarized
outputs are retained under `results/`; methodology and claim boundaries are in
`docs/METHODOLOGY.md` and `docs/RESULTS.md`.

Leases and caching are established mechanisms. Novelty is a hypothesis to validate through full-text comparison with the closest literature. The protocol provides no hard deadline or crash-survival guarantee.

## Current method and next validation phase

The completed mechanism-focused simulator uses one scheduler, one constrained edge worker and one reliable cloud fallback. It runs deterministic, independent function tasks with identifiable artifact versions and soft deadlines. The next validation phase should use two CPU edge workers and one cloud worker in containers with controlled cache limits, compute capacity and network conditions. AWS EC2 is optional rather than required.

The implemented comparison covers periodic advertisements, on-demand readiness checks without reservations, joint artifact/slot reservations, and artifact-only and slot-only ablations. All policies enforce the exact requested version and share placement, deadline and fallback rules.

The preliminary matrix varies churn, delay, competing load and reservation duration over 30 independent seeds, retaining raw per-seed rows and 95% confidence intervals. A real testbed must calibrate initialization/execution costs and re-freeze the configuration before confirmatory runs.

## Planned metrics

| Metric | Purpose |
| --- | --- |
| Deadline satisfaction over all submitted tasks | Includes rejection, timeout and fallback failure costs |
| Correct-version execution and invalid-version refusals | Verifies semantic correctness without weakening baselines |
| Readiness refusals, retries and cloud fallback | Measures dispatch-to-start races |
| End-to-end latency and throughput | Measures service performance |
| Unused reserved slot-time and pinned byte-seconds | Measures reservation waste |
| Control messages, bytes and handshake latency | Accounts for protocol overhead |

## Files available now

```text
README.md
baseline/komet/                 official paper artifact at pinned commit
docs/REPRODUCTION_REPORT.md     paper, dataset, environment, gap, reproduction
docs/METHODOLOGY.md             proposed protocol and experimental design
docs/RESULTS.md                 preliminary comparison and limitations
src/readiness_reservations/     simulator implementation
scripts/reproduce_komet.py      baseline result verification
scripts/run_experiments.py      seeded experiment matrix and analysis
tests/test_simulator.py         correctness and expiry tests
results/                        reproduced, raw, and summarized CSVs
proposal/
overleaf/
```

The older proposal artifacts remain for provenance but have not yet been revised to
incorporate the selected Komet baseline and preliminary results.

## Reproducibility plan

Publish the implemented source, pinned dependencies, machine/container specifications, artifact hashes, workload generators, seeds, run configurations, measured raw outputs and analysis/plot scripts. Document exact installation and execution commands when tested. Separate pilot from final runs and preserve negative results and failure categories. Add an agreed license and `CITATION.cff` before artifact release. Do not commit credentials.

## Course milestones

| Milestone | Guide deadline | Planned evidence |
| --- | --- | --- |
| C1: proposal | 8 September 2026 | Proposal and setup; completion/late acceptance unconfirmed |
| C2: literature and gap | 3 October 2026 | Approximately 15–20-paper matrix and refined gap |
| C3: method and preliminary results | 2 November 2026 | Working policies and pilot evidence |
| Complete draft | 17 November 2026 | Full manuscript draft |
| Final | 7 December 2026 | Manuscript, poster, public artifacts, submission evidence and defense |

## Project links

- Overleaf: https://www.overleaf.com/project/REPLACE_PROJECT_ID
- Public repository: https://github.com/SalmannUmarr/edge-readiness-reservations
- Course registration: https://docs.google.com/spreadsheets/d/REPLACE_SHEET_ID/edit

Replace the remaining Overleaf and registration placeholders. The course requires instructor editor access to Overleaf and the public repository URL as the final line of the abstract. Repository publication, Overleaf sharing, and registration completion remain external manual actions; this README does not claim that they have been performed.

## Initial academic references

1. X. Li, L. Chen, Z. Yuan and G. Liu. “AIHO: Enhancing task offloading and reducing latency in serverless multi-edge-to-cloud systems.” *Future Generation Computer Systems*, 165, 107607, 2025. [DOI](https://doi.org/10.1016/j.future.2024.107607).
2. S. A. Hamid, Y. Boujelben and F. Zarai. “Exploiting and Mitigating Staleness in Distributed Edge Offloading via Predictive Load Awareness.” *Network*, 6(3), 69, 2026. [DOI](https://doi.org/10.3390/network6030069).
3. Y. Fu et al. “ServerlessLLM: Low-Latency Serverless Inference for Large Language Models.” *OSDI*, pp. 135–153, 2024. [USENIX](https://www.usenix.org/conference/osdi24/presentation/fu).
4. S. Abdi, M. Ashjaei and S. Mubeen. “Task Offloading in Edge-Cloud Computing Using a Q-Learning Algorithm.” *CLOSER*, pp. 159–166, 2024. [DOI](https://doi.org/10.5220/0012590800003711).
5. C. G. Gray and D. R. Cheriton. “Leases: An Efficient Fault-Tolerant Mechanism for Distributed File Cache Consistency.” *SOSP*, pp. 202–210, 1989. [DOI](https://doi.org/10.1145/74850.74870).
