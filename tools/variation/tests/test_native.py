#!/usr/bin/env python3
"""Native OpenSTA integration smoke: characterized LVF, CRPR and Tcl interface."""
import json
import math
from pathlib import Path
import runpy
import re
import subprocess
import sys
import tempfile

STA = Path(sys.argv[1]).resolve()
SOURCE = Path(__file__).resolve().parents[3]
SCRIPTS = SOURCE / "tools/variation"

NET = """module v24_test(clk, d, q2, q3);
input clk, d;
output q2, q3;
wire c, c1, c2, c3, q1, n2, n3;
BUF_X1 common_clk(.A(clk),.Z(c));
BUF_X1 launch_clk(.A(c),.Z(c1));
BUF_X1 capture2_clk(.A(c),.Z(c2));
BUF_X1 capture3_clk(.A(c),.Z(c3));
DFF_X1 r1(.D(d),.CK(c1),.Q(q1));
BUF_X1 data2(.A(q1),.Z(n2));
BUF_X1 data3(.A(q1),.Z(n3));
DFF_X1 r2(.D(n2),.CK(c2),.Q(q2));
DFF_X1 r3(.D(n3),.CK(c3),.Q(q3));
endmodule
"""


def quote(path):
    return "{" + str(path).replace("\\", "/") + "}"


# The existing sta startup include_file path is not list-quoted. Keep the
# startup script path simple; command output paths below still contain spaces.
with tempfile.TemporaryDirectory(prefix="opensta_v24_native_") as tmp:
    root = Path(tmp)
    # Keep the regression-tested Nangate cell/sequential definitions and add
    # synthetic constant sigma tables. These are not foundry LVF measurements.
    reference = (SOURCE / "test/nangate45/Nangate45_typ.lib").read_text()
    sigma = '\n ocv_sigma_cell_rise (scalar) { values ("0.01"); }\n ocv_sigma_cell_fall (scalar) { values ("0.01"); }\n'
    library, count = re.subn(r'timing\s*\([^)]*\)\s*\{', lambda m: m[0] + sigma, reference)
    assert count > 0, "No timing groups in native test reference library"
    (root / "test.lib").write_text(library)
    (root / "test.v").write_text(NET)
    tcl = f"""
read_liberty {quote(root / 'test.lib')}
read_verilog {quote(root / 'test.v')}
link_design v24_test
set sta_pocv_mode normal
set sta_pocv_quantile 6.0
create_clock -name clk -period 1.0 [get_ports clk]
set_propagated_clock [get_clocks clk]
set_timing_derate -early 0.95
set_timing_derate -late 1.05
set paths [find_timing_paths -to [get_pins {{r2/D r3/D}}] -path_delay max -group_path_count 10 -endpoint_path_count 2]
if {{[llength $paths] == 0}} {{ report_checks -path_delay max -format full_clock_expanded; error "No native test paths" }}
report_design_variation $paths -samples 2000 -tail_samples 2000 -sigma_limit 3 -seed 7 -bottlenecks 2 -python {quote(sys.executable)} -output_dir {quote(root / 'design run')}
report_variation_bottleneck $paths -clock_paths exclude -exclude_VT ULVT -sigma_threshold 0.0 -max_violators 2 -python {quote(sys.executable)} -script_dir {quote(SCRIPTS)} -output_dir {quote(root / 'bottleneck run')}
if {{![catch {{report_design_variation $paths -samples 1}}]}} {{ error "sample validation missing" }}
if {{![catch {{report_design_variation $paths -sigma_limit Inf}}]}} {{ error "sigma validation missing" }}
if {{![catch {{report_variation_bottleneck $paths -clock_paths invalid}}]}} {{ error "clock validation missing" }}
if {{![catch {{report_variation_bottleneck $paths -sigma_threshold Inf}}]}} {{ error "threshold validation missing" }}
if {{![catch {{report_variation_bottleneck $paths -python {quote(sys.executable)} -script_dir {quote(SCRIPTS)} -output_dir {quote(root / 'bottleneck run')}}}]}} {{ error "overwrite protection missing" }}
set hold [find_timing_paths -to [get_pins r2/D] -path_delay min -endpoint_path_count 1]
if {{[llength $hold] == 0}} {{ error "No hold test path" }}
if {{![catch {{sta::write_design_variation_timing_cmd $hold {quote(root / 'hold.rpt')}}}]}} {{ error "hold path rejection missing" }}
set sta_pocv_mode scalar
if {{![catch {{sta::write_design_variation_timing_cmd $paths {quote(root / 'scalar.rpt')}}}]}} {{ error "scalar rejection missing" }}
"""
    # Source errors must produce a failing process status.
    (root / "run.tcl").write_text(
        "if {[catch {\n" + tcl + "\n} message]} {puts stderr $message; exit 1}\nexit 0\n")
    result = subprocess.run([str(STA), "-exit", str(root / "run.tcl")],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout)
    if result.returncode:
        raise SystemExit(result.returncode)
    for directory in ("design run", "bottleneck run"):
        manifest = json.loads((root / directory / "opensta_manifest.json").read_text())
        assert manifest["backend"] == "standalone V24, unmodified"
    d = runpy.run_path(str(SCRIPTS / "generic_design_variation_pin_arc_ps_standalone_V24.py"))
    text = (root / "design run/timing.rpt").read_text()
    blocks = d["_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__split_blocks"](text)
    paths = [d["_timing_report_parser_V18__parse_block"](b, i) for i, b in enumerate(blocks, 1)]
    means, a, keys, audit = d["_generic_design_variation_pin_arc_ps_standalone_V24__linear_model"](paths)
    import numpy as np
    assert np.all(np.linalg.norm(a, axis=1) > 0)
    shared = [j for j, key in enumerate(keys) if key.startswith("common_clk:")]
    assert shared, "shared clock arc absent from native export"
    assert np.all(a[:, shared] == 0), "shared clock sigma did not cancel"
    assert max(abs(row["nominal_reconstruction_delta_ns"]) for row in audit) < 1e-9
    summary = json.loads((root / "bottleneck run/bottleneck/summary.json").read_text())
    assert "common_clk" in summary["hidden_by_clock"]
    assert "r1" not in summary["hidden_by_clock"]
    assert summary["reported_cells"] <= 2
    assert not (root / "hold.rpt").exists()
    assert not (root / "scalar.rpt").exists()
    print("Native V24 setup/CRPR/interface smoke passed")
