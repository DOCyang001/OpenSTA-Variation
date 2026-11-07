# OpenSTA V24 design variation and bottleneck

This fork extends the existing `report_design_variation` command and adds
`report_variation_bottleneck`. It ships the user's two standalone V24 Python
algorithms unchanged. Native C++ exports selected OpenSTA graph/PathEnd moments;
the algorithms do not launch or require PrimeTime or PrimeShield.

## Build and environment

Build OpenSTA normally using CMake. The backend is copied to
`build/share/OpenSTA/variation` and installed to `share/OpenSTA/variation`.
The selected Python must provide NumPy and SciPy:

```sh
python3 -m pip install -r tools/variation/requirements.txt
```

For Bazel, embedded OpenSTA, or an executable moved without its share directory,
supply `-script_dir /path/to/OpenSTA/tools/variation` or set
`STA_VARIATION_SCRIPTS`. Use `-python /path/to/python3` to select Python.
A Python executable is one Tcl argument, not a shell command.

## Existing Design Variation interface

```tcl
set sta_pocv_mode normal
set sta_pocv_quantile 6.0
# Read/link libraries, design and SDC; configure propagated clocks as usual.
set paths [find_timing_paths -path_delay max \
    -from [get_pins launch_reg/CK] -to [get_pins capture_reg/D] \
    -group_path_count 1000 -endpoint_count 3]

report_design_variation $paths \
    -samples 316000 -tail_samples 316000 \
    -sigma_limit 6 -seed 20260908 -bottlenecks 10 \
    -output_dir ./variation_run
```

The existing positional path collection and `-samples`, `-sigma_limit`,
`-seed`, and `-bottlenecks` options remain accepted. The command prints the
V24 design report and up to `-bottlenecks` cell scores for compatibility.
Detailed bottleneck reporting is also available independently below.

| Option | Default | Meaning |
| --- | --- | --- |
| `-samples` | 1000 | Ordinary, unbounded Gaussian Monte Carlo count; at least 2 |
| `-tail_samples` | `-samples` | Separate ALOE sample count per bank; at least 2 |
| `-sigma_limit` | 6 | Target Gaussian-equivalent lower-tail quantile; 0 < sigma <= 8 |
| `-seed` | 1 | Positive base seed; V24 uses distinct offsets for validation banks |
| `-bottlenecks` | 10 | Cell scores printed after the design report; full CSV retained |
| `-output_dir` | Unique directory in current working directory | Fresh/empty output directory |
| `-python` | python3 | Python executable |
| `-script_dir` | Build/install share directory | Directory containing the backend files |

**Semantic change:** the old implementation truncated Gaussian sources at
`-sigma_limit`. V24 uses unbounded Gaussian sources and interprets this existing
option as the target quantile. Keeping truncation would invalidate rare-tail
analysis. It does not change OpenSTA's `sta_pocv_quantile`; that variable controls
the corner/Variation column during export.

The V24 backend retains ordinary-MC WNS, GPD candidates, ALOE validation and
fallback, independent holdout results, endpoint shifts, and the correlated
adjusted-design probability. A solved 6-sigma endpoint target does not by itself
prove the combined design has 6-sigma yield.

## New Bottleneck interface

```tcl
report_variation_bottleneck $paths \
    -clock_paths exclude -exclude_VT {ULVT,LVT} \
    -variation_threshold 0.02 -sigma_threshold 0.1 \
    -max_violators 20 -output_dir ./bottleneck_run
```

All options except the path collection are optional. The new command does not
perform design Monte Carlo. It uses the standalone V24 deterministic HSFR
integrals and context selection.

| Option | Default | Meaning |
| --- | --- | --- |
| `-clock_paths` | include | `exclude` hides clock cells while protecting terminal registers |
| `-exclude_VT` | None | Comma/space-separated library-cell VT labels in one Tcl argument |
| `-variation_threshold` | None | Hide Variation strictly below this value, in current OpenSTA time units |
| `-sigma_threshold` | None | Hide dimensionless Sigma_ratio strictly below this value |
| `-max_violators` | All | Maximum visible cell rows |
| `-output_dir`, `-python`, `-script_dir` | Same as above | Output and backend configuration |

Filters affect only the text report. Full CSV rows and ranks remain intact.
HSFR uses the final signed, common-clock-corrected slack coefficients; the
displayed Sigma_ratio uses raw local arc sigma, as in V24. Capture-clock arcs can
have a protective sign. HSFR is an approximation, not the exact joint failure
probability or a guaranteed benefit from replacing a cell.

## Data model and boundaries

- Native support currently covers selected register-to-register flip-flop setup
  paths with enabled **normal POCV** and characterized nonzero cell-arc sigma.
  Hold, latch/time-borrowing, port paths and skew-normal mode are rejected.
- Each physical input/output pin and input/output transition pair shares one
  Gaussian source across paths. Different arcs are independent, matching V24.
- The exporter reads derated arc moments directly. Subtracting two cumulative
  arrival variances would not give the local arc variance.
- Launch clock, clock-to-Q, data and capture clock rows are exported. OpenSTA's
  actual CRPR common pin identifies the removed prefix.
- Nominal slack comes from `PathEnd::slack().mean()`, including OpenSTA's fixed
  constraint/edge/CRPR accounting, rather than a sigma-shifted corner slack.
- All fixed constraint and edge offsets, including fixed setup and uncertainty,
  are aggregated into the interchange's `clock uncertainty` budget. That line
  is a serialization field, not a report of just physical uncertainty.
- Setup-check sigma and net-delay sigma are not introduced into the V24 model.
  Setup is fixed as in the standalone scripts; statistical net delays are
  rejected. Design runs reject deterministic/fully cancelled zero-sigma paths
  explicitly because the standalone rare-tail engine does not support them.
- The intermediate `timing.rpt` is an **OpenSTA compatibility interchange**,
  not a PT measurement or an OpenSTA `report_checks` dump. Values are scaled to
  the current OpenSTA report time unit; `0.02` means 20 ps only if that unit is ns.
- Scope is the selected path collection, not automatic full-design coverage.
  The current interchange labels the group `OpenSTA`.
- Whitespace/parentheses in pin or library-cell names are rejected because the
  V24 text parser cannot encode them unambiguously.

## Outputs

The command returns the absolute output directory. It preserves input data and
algorithm fingerprints:

- `timing.rpt`: native moment interchange.
- `design/timing_V24_report.txt` and `design/timing_V24_summary.json`: design
  results, endpoint adjustments and independent tail validation.
- `bottleneck/report.txt`, `cells.csv`, `arc_contexts.csv`,
  `source_scores.csv`, `path_margins.csv`, `summary.json`: cell scores,
  provenance and visibility audit.
- `opensta_manifest.json`: input/backend SHA256, source and model limitations.

No command changes SDC, cells, delays or the input design. Existing nonempty
output directories are rejected. Backend/dependency errors propagate as Tcl
errors.

## Validation

```sh
python3 -m unittest discover -s tools/variation/tests -p test_v24.py -v
python3 tools/variation/tests/test_native.py build/sta
```

Tests cover a single Gaussian path, identical-source dominance, an independent
union reference, signed capture contributions, shared-clock cancellation,
CSV/rank preservation under filters, CLI outputs, no-overwrite behavior and
invalid inputs. Native smoke tests create a synthetic LVF library and a small
propagated-clock netlist, run both Tcl commands, and reject hold/scalar input.
These synthetic cases validate implementation behavior, not foundry or PS
accuracy across arbitrary designs.
