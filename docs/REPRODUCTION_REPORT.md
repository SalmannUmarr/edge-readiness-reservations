# Baseline Selection and Initial Reproduction Report

## Selected paper

**Tobias Pfandzelter and David Bermbach, “Komet: A Serverless Platform for
Low-Earth Orbit Edge Services,” ACM Symposium on Cloud Computing (SoCC ’24),
2024.**

- Paper: <https://arxiv.org/abs/2410.05973>
- DOI: <https://doi.org/10.1145/3698038.3698517>
- Official artifact: <https://github.com/3s-rg/komet>
- Checked-out artifact commit: `10207547993b78d812582a214e012728ee3a6fe5`
- License: MIT for Komet; the bundled Celestial scheduling code is GPLv3.

## Why this is the baseline

Komet is a recent paper at a reputable cloud-systems venue, releases its
prototype and per-experiment scripts, and includes the input configurations and
output traces for its scheduling study.  It is a closer methodological fit than
an AI-only offloading paper because it combines edge FaaS placement, cached
function execution, proactive service movement, and a central scheduler.  Its
released scheduling simulator is small enough to audit and reproduce locally.

The extension does **not** claim that Komet is defective.  Komet studies a
different layer and explicitly isolates its heuristics from resource
variability.  That abstraction leaves a well-defined question for this project:
after a scheduler selects a supposedly ready worker, can artifact eviction,
version replacement, or competing work invalidate readiness before execution?

## Original problem and approach

Komet provides virtual stationarity for services on moving LEO satellites.  It
combines per-satellite FaaS and replicated storage, proactively deploys functions
and data, and hands clients between instances.  Its one-to-one scheduling
heuristic initially selects the closest satellite and changes placement only
when another server improves network distance by a configured threshold.  The
central scheduler is cloud-based, considers global and predicted network state,
and is assumed to operate asynchronously outside the request critical path.

The paper evaluates container migration, three example applications, and trace-
driven scheduling.  This project reproduces the core §8.1 one-to-one result
because it is deterministic, directly supported by the released traces, and
captures the placement/migration trade-off on which our extension builds.

## Data and experimental assets

Komet does not use a conventional ML training dataset.  Its §8.1 scheduling
input is a 20-minute Celestial-generated network trace at one-second resolution
for one ground client in Redmond and the 1,584 satellites in the first shell of
the phase-I Starlink model.  The official repository includes configuration,
simulation code, and result CSVs.  Each CSV has timestamp, ground station,
selected satellite, and one-way link latency in microseconds.  There is no
train/validation/test split and no augmentation.  RTT is calculated as twice the
one-way latency.

Other paper experiments use IoT locations and Wikimedia Mediacounts requests,
but they are outside this focused reproduction.  The proposed experiment uses
synthetic event traces generated from documented distributions; it does not
mislabel synthetic tasks as a public dataset.

## Original environment and requirements

The paper reports Ubuntu 22.04 LTS on a host with two 12-core Intel Xeon Silver
4310 CPUs, 64 GB RAM, and SSD storage for the container study.  Its larger CDN
experiment uses sixteen Google Compute Engine `n2-standard-16` instances.  The
artifact uses Docker, Celestial, Python, Redis, gRPC, and experiment-specific
shell/Makefile automation.  Regenerating the complete Celestial traces or the
distributed cloud experiments requires substantially more software and compute
than recalculating §8.1 from the released result traces.

Local verification used macOS 26.6 on arm64 and Python 3.9.6.  The reproduction
and proposed simulator use only the Python standard library.  No GPU or cloud
account is required.

## Reproduced result

Run:

```bash
python3 scripts/reproduce_komet.py
```

| Strategy | Paper mean RTT (ms) | Reproduced (ms) | Difference (ms) | Paper migrations | Reproduced | Difference |
|---|---:|---:|---:|---:|---:|---:|
| MinMax | 4.980 | 4.9849 | +0.0049 | 16 | 16 | 0 |
| Komet 10% | 4.990 | 4.9901 | +0.0001 | 12 | 12 | 0 |
| Komet 25% | 5.220 | 5.2177 | -0.0023 | 9 | 9 | 0 |
| Komet 1 ms | 5.040 | 5.0373 | -0.0027 | 12 | 12 | 0 |

The migration counts reproduce exactly.  RTT differences are explained by the
paper printing two decimal places while the released CSVs retain finer values.
The machine and library versions cannot affect this deterministic aggregation.
The generated table is in `results/komet_reproduction.csv`.

## Reproducibility audit

Strengths:

- official public repository and paper link;
- experiment-specific directories and scripts;
- released trace-derived CSVs allow result verification without cloud access;
- pinned artifact commit recorded here;
- readable scheduling implementation and configurations.

Limitations:

- the root README gives high-level execution guidance but not a one-command,
  container-pinned reproduction of every figure;
- full distributed experiments require Docker, Celestial images, and multiple
  hosts or Google Cloud resources;
- the paper does not publish repeated-run uncertainty for deterministic §8;
- §8 explicitly excludes service performance and resource variability;
- there is no deadline, artifact-version, queue-capacity, or dispatch-refusal
  outcome in the released scheduling model.

## Research gap

Komet's scheduler selects a location and initiates proactive deployment, but its
isolated scheduling evaluation assumes that the selected service remains usable.
In a resource-constrained multi-tenant edge, the scheduler's observation and the
request's actual start are separated by a control and transport delay.  During
that interval, an exact function artifact can be evicted or superseded and a
compute slot can be claimed.  A fresh on-demand check narrows this interval but
does not close it.  The gap is therefore **time-of-check to time-of-use readiness
under exact versions, deadlines, and concurrent capacity demand**.

This gap is supported by the baseline's abstraction boundary: Komet states that
its §8 simulation excludes resource variability and discusses server resource
and fluctuating-demand scheduling as future work.  The proposed mechanism is a
small, bounded protocol change rather than an unrelated new feature.

## Proposed contribution

A worker grants a single-use token containing worker epoch, exact artifact hash
or version, one execution slot, issue time, expiry time, and request nonce.  A
valid token temporarily prevents eviction/replacement of that artifact and
prevents the reserved slot from being allocated to competing work.  Dispatch is
accepted only once, at the granting worker and epoch, for the exact version, and
before expiry.  Expired or mismatched tokens are refused; there is no execution
of a stale version.

The claims tested are intentionally narrow: a valid joint reservation should
reduce readiness refusals and improve deadline satisfaction under churn, while
incurring control messages, pinned byte-seconds, and potentially unused reserved
slot-time.
