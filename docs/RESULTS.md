# Experimental Results

## Baseline reproduction

The released Komet §8.1 traces reproduce all four reported migration counts
exactly.  Recalculated mean RTT differs from the printed paper values by at most
0.0049 ms, consistent with rounding.  See `docs/REPRODUCTION_REPORT.md` and
`results/komet_reproduction.csv`.

## Proposed method: representative stress condition

The table below is the mean of 30 seeds × 1,000 tasks for 30 ms dispatch delay,
8 evictions/s, competing-load coefficient 0.75, and 50 ms TTL.  The TTL is long
enough to cover dispatch.  “±” is a 95% confidence interval across seeds.

| Policy | Deadline satisfaction | Refusal rate | Mean latency (ms) | p95 (ms) | Control messages/run |
|---|---:|---:|---:|---:|---:|
| Advertisement | 46.04% ± 0.57 | 43.51% | 117.03 | 146 | 523 |
| On-demand | 59.88% ± 0.61 | 25.69% | 109.39 | 146 | 2,523 |
| Artifact-only | 67.47% ± 0.54 | 17.36% | 104.15 | 146 | 3,294 |
| Slot-only | 72.78% ± 0.57 | 13.59% | 98.88 | 146 | 3,429 |
| Joint reservation | **84.73% ± 0.46** | **0.00%** | **90.81** | **104** | 3,285 |

Joint reservation improves deadline satisfaction by **24.85 percentage points**
over on-demand readiness and by **38.69 points** over periodic advertisement in
this condition.  It removes the dispatch race by construction while the token is
valid.  Every tested policy has zero invalid-version executions.

## Ablation interpretation

Artifact-only reservation leaves slot contention exposed; slot-only reservation
leaves eviction and replacement exposed.  Their intermediate outcomes support
the claim that both dimensions contribute.  Slot-only happens to outperform
artifact-only in this frozen stress cell because the configured competing-slot
hazard is stronger than the combined artifact hazard.  This is not evidence that
slots are universally more important.

For the representative run, joint reservation additionally holds about 1,464
MB-seconds of artifact state per 1,000-task seed and wastes about 0.233 seconds
of reserved slot-time due to cancellation.  On-demand checking has neither cost
but uses fewer control messages and tolerates more refusals/fallbacks.  These are
the intended trade-offs, not free gains.

## TTL result

At 30 ms dispatch delay, the 20 ms TTL expires before dispatch and therefore
cannot guarantee readiness.  The tests assert that refusals remain possible in
this case.  TTLs of 50 and 100 ms both cover dispatch and eliminate the modeled
gap for joint reservation; 100 ms offers no extra readiness benefit in this
model.  A deployment should therefore choose a bounded TTL just above measured
control-plane delay rather than maximize it.

## Claim boundary and remaining limitations

These results establish internal behavior in a deterministic discrete-event
simulation, not production-cloud superiority.  Hazard rates are scenario
parameters rather than field measurements.  The model has one edge worker, one
slot, independent hazards, perfect clocks, and no reservation-service failure.
It does not measure real cache eviction, container startup, energy, monetary
cost, satellite handoff, or cryptographic-token overhead.

The next empirical step is to calibrate the event distributions using a
containerized two-edge/one-cloud testbed, implement worker epochs and signed or
unguessable tokens, and repeat the frozen comparison under measured churn and
network delay.  Until then, report the contribution as simulation-supported and
the Komet reproduction as trace-result verification rather than a rerun of its
full Google Cloud deployment.
