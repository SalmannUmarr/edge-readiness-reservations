# G25 IMPLEMENTATION

## Topic

Version Bound Readiness Reservations for Deadline Aware Edge Cloud Offloading
under Artifact Eviction and Updates

## Students

- Danish Atif  I22-1095
- Salman Umar  I22-0908

## Reproduce the work

Run these commands from the `code` directory using Python 3.9 or newer:

```bash
python3 scripts/reproduce_komet.py
python3 -m unittest discover -s tests -v
python3 scripts/run_experiments.py
```

The implementation uses only the Python standard library. No GPU, cloud account,
or dependency installation is required.

## Package contents

- `report` contains the final report and PDF.
- `code/src` contains the reservation simulator.
- `code/scripts` contains baseline reproduction and experiment runners.
- `code/tests` contains four automated correctness tests.
- `code/baseline` contains the four official Komet CSVs needed for the selected
  Section 8.1 reproduction and the upstream license.
- `code/results` contains precomputed results and is overwritten when experiments
  are rerun.
- `results` contains a stable copy of the submitted raw and summarized outputs.

## Claim boundary

The Komet result is reproduced from the authors released trace derived CSVs.
The readiness reservation results come from a controlled discrete event
simulation. The package does not claim that the full Komet Google Cloud testbed
or a real container deployment of the proposed method has been completed.

## Baseline provenance

- Paper: https://arxiv.org/abs/2410.05973
- Official repository: https://github.com/3s-rg/komet
- Commit used: `10207547993b78d812582a214e012728ee3a6fe5`
