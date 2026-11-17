# Methodology: Version-Bound Readiness Reservations

## Research question and hypotheses

**RQ:** Under artifact eviction, version replacement, dispatch delay, and
competing load, do short-lived joint artifact-and-slot reservations improve task
deadline satisfaction over periodic advertisements and on-demand readiness
checks without permitting incorrect-version execution?

- H1: with TTL at least the dispatch delay, joint reservations reduce
  dispatch-time readiness refusals relative to on-demand checking.
- H2: the refusal reduction improves deadline satisfaction and tail latency when
  fallback cannot consistently meet the original deadline.
- H3: artifact-only and slot-only reservations perform between on-demand checks
  and joint reservations when both hazards are present.
- H4: a TTL shorter than dispatch delay loses protection, while longer TTLs hold
  more resources without further readiness benefit in this model.

## System model

One scheduler chooses between a constrained edge worker and a reliable but
higher-latency cloud worker.  Each task has an arrival time, exact artifact
version, soft absolute deadline, edge RTT, and execution cost.  At decision time
the scheduler uses either a periodic advertisement or a current readiness check.
Dispatch follows after a configured delay.  Independent exponential hazards can
evict the artifact or replace it with another version during this gap; competing
load can claim the execution slot.

If the exact version or slot is unavailable at dispatch, the worker refuses the
request and the scheduler retries in the cloud after a fixed penalty.  Every
policy applies the same exact-version rule.  Consequently, the relevant safety
metric is zero invalid-version executions, not a speed/consistency trade-off.

The simulator is mechanism-focused and does not model satellite orbits, network
paths, container image transfer, correlated failures, multiple queued slots, or
real container startup.  It complements rather than replaces Komet's trace-driven
placement evaluation.

## Policies

1. **Advertisement:** choose using a periodic cached snapshot.
2. **On-demand:** query current artifact and slot state, but do not hold either.
3. **Artifact-only:** on-demand check plus exact-version pin until token expiry.
4. **Slot-only:** on-demand check plus one reserved execution slot.
5. **Joint reservation:** atomically bind both exact artifact and slot.

The last two single-resource variants are ablations.  All policies use identical
placement, deadline, fallback, execution, and correctness rules.

## Controlled variables

The frozen matrix varies:

| Factor | Values |
|---|---|
| Dispatch delay | 10, 30 ms |
| Artifact eviction rate | 2, 8 events/s |
| Competing load coefficient | 0.35, 0.75 |
| Reservation TTL | 20, 50, 100 ms |
| Seeds | 1–30 |
| Tasks per cell and policy | 1,000 |

Other defaults are stored in the immutable `Config` dataclass: 18 arrivals/s,
4 replacements/s, 24 ms edge runtime, 42 ms cloud runtime, 62 ms cloud RTT,
50 ms advertisement interval, 12 ms retry penalty, 128 MB artifact, and 2%
cancellation probability.  Deadlines are uniformly 92–142 ms after arrival and
edge RTT is uniformly 9–21 ms.  Random variables are generated once per seed and
reused across policies (common random numbers) for paired comparisons.

## Metrics and analysis

Primary: deadline satisfaction over all submitted tasks.  Secondary: readiness
refusal rate, artifact/slot refusal counts, cloud fallback, mean and p95 latency,
correct/invalid version executions, control messages, pinned MB-seconds, reserved
slot-seconds, and unused reserved slot-seconds.

Each summary is the arithmetic mean over 30 independent seeds with a normal
95% confidence interval (`1.96 × sample SD / sqrt(30)`).  The raw per-seed rows
are retained for paired analysis.  Cancellations remain in the denominator of
deadline satisfaction to avoid survivorship bias.  No significance claim is
made solely from overlapping or non-overlapping confidence intervals.

## Protocol invariants

- token worker epoch, version, nonce, and expiry must match;
- a token is single-use and cannot be replayed;
- exact-version mismatch is refusal, never fallback to another local version;
- artifact pin and slot hold end at use, explicit cancellation, or TTL;
- expired tokens have no protective effect;
- resource costs are recorded even when a reservation is unused.

The simulation implements the validity and expiry semantics.  Authentication,
epoch changes, distributed clocks, and replay storage remain implementation work
for a networked prototype and must not be claimed as experimentally validated.

## Reproduction commands

```bash
python3 scripts/reproduce_komet.py
python3 -m unittest discover -s tests -v
python3 scripts/run_experiments.py
```

Outputs are `results/komet_reproduction.csv`, `results/raw_results.csv`, and
`results/summary.csv`.  Re-running with the same Python semantics and seeds is
deterministic.
