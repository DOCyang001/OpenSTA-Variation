"""Analytic and interface checks for the OpenSTA V24 integration."""
import csv
import json
import math
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
D = runpy.run_path(str(BACKEND / "generic_design_variation_pin_arc_ps_standalone_V24.py"))
B = runpy.run_path(str(BACKEND / "variation_bottleneck_v24.py"))
sys.path.insert(0, str(BACKEND))
import opensta_variation as driver
import numpy as np
from scipy.special import ndtr
from scipy.optimize import brentq

MODEL = D["_generic_design_variation_pin_arc_ps_standalone_V24__GaussianUnion"]
PARSE = D["_timing_report_parser_V18__parse_block"]
LINEAR = D["_generic_design_variation_pin_arc_ps_standalone_V24__linear_model"]


def block(mean=0.2, sigma=0.05, capture_sigma=0.0, common=False):
    # Synthetic test fixture, time values in ns; not PT/PS measurements.
    clock = "  clk0/A (BUF_SVT) 0 0 0 0 0 0 0 r\n  clk0/Y (BUF_SVT) 0 0 0.01 0.02 0.13 0.13 0 r\n" if common else ""
    return ("  Startpoint: r1 (flip-flop)\n"
            "  Endpoint: r2/D (flip-flop)\n"
            "  Path Group: test\n  Path Type: max\n"
            + ("  Last common pin: clk0/Y\n" if common else "")
            + "  Point Fanout Cap Mean Sensit Corner Value Path\n"
            + clock
            + "  r1/CK (FF_SVT) 0 0 0 0 0 0 0 r\n"
            + f"  r1/Q (FF_SVT) 0 0 0.1 {sigma} {0.1+6*sigma} {0.1+6*sigma} 0 r\n"
            + "  r2/D (FF_SVT) 0 0 0 0 0 0 0 r\n"
            + f"  data arrival time {0.11 if common else 0.1}\n"
            + clock
            + "  cap/A (BUF_ULVT) 0 0 0 0 0 0 0 r\n"
            + f"  cap/Y (BUF_ULVT) 0 0 0 {capture_sigma} {6*capture_sigma} {6*capture_sigma} 0 r\n"
            + "  r2/CK (FF_SVT) 0 0 0 0 0 0 0 r\n"
            + f"  clock uncertainty {mean+0.1}\n"
            + f"  data required time {(0.11 if common else 0.1)+mean}\n")


class VariationTests(unittest.TestCase):
    def test_single_path_analytic_quantile(self):
        model = MODEL(np.array([0.2]), np.array([[-0.05]]), 2000, 7)
        model.set_gpd_wns(np.linspace(-0.05, 0.45, 2000))
        q, estimate = model.quantile(6)
        self.assertAlmostEqual(q, -0.1, places=12)
        self.assertAlmostEqual(estimate["probability"], float(ndtr(-6)), places=18)

    def test_identical_sources_reduce_exactly(self):
        model = MODEL(np.array([0.2, 0.3]), np.array([[-0.05], [-0.05]]), 2000, 7)
        self.assertEqual(model.k, 1)
        self.assertAlmostEqual(model.failure(0)["probability"], float(ndtr(-4)), places=15)

    def test_independent_union(self):
        model = MODEL(np.array([0.2, 0.2]), np.array([[0.05, 0], [0, 0.05]]), 30000, 7)
        result = model.failure(0)
        expected = 1 - (1 - float(ndtr(-4)))**2
        self.assertLess(abs(result["probability"] - expected),
                        6*result["standard_error"] + 2e-8)

    def test_signed_capture_and_common_clock(self):
        m, a, keys, audit = LINEAR([PARSE(block(capture_sigma=0.03, common=True), 1)])
        index = {key: j for j, key in enumerate(keys)}
        self.assertAlmostEqual(m[0], 0.2)
        self.assertAlmostEqual(a[0, index["clk0:A:r->Y:r"]], 0.0)
        self.assertAlmostEqual(a[0, index["r1:CK:r->Q:r"]], -0.05)
        self.assertAlmostEqual(a[0, index["cap:A:r->Y:r"]], 0.03)
        self.assertAlmostEqual(np.linalg.norm(a[0]), math.hypot(0.05, 0.03))
        self.assertAlmostEqual(audit[0]["nominal_reconstruction_delta_ns"], 0.0)

    def test_filters_preserve_all_calculations_and_ranks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "timing.rpt"
            src.write_text(block(capture_sigma=0.03, common=True))
            call = B["_variation_bottleneck_v24__run"]
            call(str(src), str(root / "all"))
            call(str(src), str(root / "filtered"), clock_paths="exclude",
                 exclude_VT="ULVT", variation_threshold=0.1, sigma_threshold=0.1)
            self.assertEqual((root / "all/cells.csv").read_bytes(),
                             (root / "filtered/cells.csv").read_bytes())
            summary = json.loads((root / "filtered/summary.json").read_text())
            self.assertIn("cap", summary["hidden_by_VT"])
            self.assertIn("clk0", summary["hidden_by_clock"])

    def test_driver_end_to_end_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="v24 spaces ") as tmp:
            root = Path(tmp)
            src = root / "timing.rpt"
            src.write_text(block(capture_sigma=0.03, common=True))
            args = ["--kind", "design", "--input", str(src),
                    "--output-dir", str(root / "out"),
                    "--samples", "2000", "--tail-samples", "2000", "--sigma", "3"]
            driver.main(args)
            summary = json.loads((root / "out/design/timing_V24_summary.json").read_text())
            self.assertAlmostEqual(summary["design_slack"], 0.2 - 3*math.hypot(0.05, 0.03), places=8)
            self.assertTrue((root / "out/opensta_manifest.json").is_file())
            with self.assertRaises(SystemExit):
                driver.main(args)

    def test_zero_sigma_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "zero.rpt"
            src.write_text(block(sigma=0))
            with self.assertRaisesRegex(ValueError, "nonzero slack sigma"):
                driver.main(["--kind", "design", "--input", str(src),
                             "--output-dir", str(root / "out")])
            self.assertFalse((root / "out").exists())

    def test_invalid_target(self):
        for value in ("nan", "inf", "0", "9"):
            with self.assertRaises(SystemExit):
                driver.main(["--kind", "design", "--input", "unused",
                             "--output-dir", "unused", "--sigma", value])


if __name__ == "__main__":
    unittest.main()
