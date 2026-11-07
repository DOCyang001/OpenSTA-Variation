#!/usr/bin/env python3
"""Run the unmodified V24 algorithms on OpenSTA's native moment interchange."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
DESIGN = "generic_design_variation_pin_arc_ps_standalone_V24.py"
BOTTLENECK = "variation_bottleneck_v24.py"


def load_backend(name):
    return runpy.run_path(str(HERE / name), run_name="opensta_v24_backend")


def finite_nonnegative(value):
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise argparse.ArgumentTypeError("expected a finite, nonnegative value")
    return value


def positive_count(value):
    count = int(value)
    if count < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return count


def run_bottleneck(module, input_file, output, args, limit=None):
    summary = module["_variation_bottleneck_v24__run"](
        str(input_file), str(output), clock_paths=args.clock_paths,
        exclude_VT=args.exclude_vt, variation_threshold=args.variation_threshold,
        sigma_threshold=args.sigma_threshold)
    rows = []
    if (output / "cells.csv").exists():
        with (output / "cells.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
    hidden = set(summary["hidden_report_cells"])
    visible = [row for row in rows if row["cell"] not in hidden]
    if limit is not None:
        visible = visible[:limit]
    # Retain every calculated CSV row and its original rank.
    report = module["_bottleneck_report_format__format_v9_report"](
        summary, visible, len(visible)).replace("V9", "V24")
    report = report.replace("restricted, same-edge pin slack proxy.",
                            "V13-selected path analytic slack sigma.")
    report = report.replace("Existing rank by signed ordinary-yield removal gain.",
                            "Descending analytic HSFR estimate.")
    report += "\nOpenSTA native normal-POCV moments; current OpenSTA time unit.\n"
    report += "All CSV rows retained. Visibility filters and limits affect report only.\n"
    report += "HSFR is the V24 approximation, not exact correlated failure probability.\n"
    (output / "report.txt").write_text(report, encoding="utf-8")
    summary["reported_cells"] = len(visible)
    summary["max_violators"] = limit
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                        encoding="utf-8")
    print(report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-dependencies", action="store_true")
    parser.add_argument("--kind", choices=("design", "bottleneck"))
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--samples", type=positive_count, default=1000)
    parser.add_argument("--tail-samples", type=positive_count)
    parser.add_argument("--sigma", type=float, default=6.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--bottlenecks", type=positive_count, default=10)
    parser.add_argument("--max-violators", type=positive_count)
    parser.add_argument("--clock-paths", choices=("include", "exclude"), default="include")
    parser.add_argument("--exclude-vt")
    parser.add_argument("--variation-threshold", type=finite_nonnegative)
    parser.add_argument("--sigma-threshold", type=finite_nonnegative)
    args = parser.parse_args(argv)
    # Import lazily so --help and validation remain usable without SciPy.
    if args.check_dependencies:
        load_backend(DESIGN)
        load_backend(BOTTLENECK)
        print("V24 dependencies available")
        return
    if args.kind is None or args.input is None or args.output_dir is None:
        parser.error("--kind, --input and --output-dir are required")
    if not math.isfinite(args.sigma) or not 0 < args.sigma <= 8:
        parser.error("--sigma must be finite and in (0, 8]")
    if args.samples < 2 or (args.tail_samples is not None and args.tail_samples < 2):
        parser.error("ordinary and tail samples must be >= 2")
    if args.seed < 0:
        parser.error("--seed must be nonnegative")
    input_file = args.input.resolve()
    output = args.output_dir.resolve()
    design_dir, bottleneck_dir = output / "design", output / "bottleneck"
    destinations = [bottleneck_dir]
    if args.kind == "design":
        destinations.append(design_dir)
    if any(path.exists() for path in destinations):
        parser.error("refusing to overwrite existing analysis outputs")
    design = load_backend(DESIGN)
    text = input_file.read_text(encoding="utf-8")
    blocks = design["_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__split_blocks"](text)
    paths = [design["_timing_report_parser_V18__parse_block"](block, i)
             for i, block in enumerate(blocks, 1)]
    means, coefficients, _, audit = design["_generic_design_variation_pin_arc_ps_standalone_V24__linear_model"](paths)
    import numpy as np
    if not np.all(np.isfinite(means)) or not np.all(np.isfinite(coefficients)):
        raise ValueError("non-finite native linear model")
    if args.kind == "design" and np.any(np.linalg.norm(coefficients, axis=1) <= 0):
        raise ValueError("V24 design analysis requires nonzero slack sigma on every path; deterministic or fully cancelled paths need separate handling")
    # Reconstructing fixed timing budgets must not silently alter nominal slack.
    tolerance = max(float(np.max(np.abs(means))), 1.0) * 1e-10
    if any(abs(row["nominal_reconstruction_delta_ns"]) > tolerance for row in audit):
        raise ValueError("native nominal slack reconstruction failed")
    output.mkdir(parents=True, exist_ok=True)
    if args.kind == "design":
        args.output_dir = str(design_dir)
        args.input = str(input_file)
        args.tail_samples = args.tail_samples or args.samples
        args.workers = 1
        design["_generic_design_variation_pin_arc_ps_standalone_V24__run"](args)
        reports = list(design_dir.glob("*_V24_report.txt"))
        if len(reports) != 1:
            raise RuntimeError("expected one V24 design report")
        print(reports[0].read_text(encoding="utf-8"))
    bottleneck = load_backend(BOTTLENECK)
    run_bottleneck(bottleneck, input_file, bottleneck_dir, args,
                   args.bottlenecks if args.kind == "design" else args.max_violators)
    manifest = {
        "source": "OpenSTA native graph and setup PathEnd moments",
        "backend": "standalone V24, unmodified",
        "input_sha256": hashlib.sha256(input_file.read_bytes()).hexdigest(),
        "time_unit": "current OpenSTA report time unit",
        "setup_sigma": "fixed, as in standalone V24",
        "net_delay_sigma": "unsupported; rejected by native exporter",
        "model": "shared physical pin/transition Gaussian cell-arc sources",
        "kind": args.kind,
        "backend_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                           for name in (DESIGN, BOTTLENECK)},
        "limitations": ["Selected register-to-register setup paths only",
                        "Fixed net/constraint/check delays",
                        "HSFR uses the V24 residual survival approximation",
                        "Independent tail validation is reported, not a proof of accuracy"]
    }
    (output / "opensta_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Outputs: " + str(output))


if __name__ == "__main__":
    main()
