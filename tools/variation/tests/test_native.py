#!/usr/bin/env python3
"""Native OpenSTA integration smoke: characterized LVF, CRPR and Tcl interface."""
import json
import math
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

STA = Path(sys.argv[1]).resolve()
SOURCE = Path(__file__).resolve().parents[3]
SCRIPTS = SOURCE / "tools/variation"

# Synthetic validation library; not foundry characterization.
TABLE = '(scalar) { values ("0.1"); }'
SIGMA = '(scalar) { values ("0.01"); }'
SLEW = '(scalar) { values ("0.02"); }'
def timing(related, kind, sense="positive_unate"):
    return (f'timing () {{ related_pin : "{related}"; timing_type : {kind}; '
            f'timing_sense : {sense}; cell_rise {TABLE} cell_fall {TABLE} '
            f'rise_transition {SLEW} fall_transition {SLEW} '
            f'ocv_std_dev_cell_rise {SIGMA} ocv_std_dev_cell_fall {SIGMA} }}')

LIB = ('library (v24_test) { delay_model : table_lookup; time_unit : "1ns"; '
       'voltage_unit : "1V"; current_unit : "1mA"; pulling_resistance_unit : "1kohm"; '
       'capacitive_load_unit (1,pf); nom_voltage : 1; nom_temperature : 25; nom_process : 1; '
       'cell (BUF_SVT) { area : 1; pin (A) { direction : input; capacitance : 0.001; } '
       'pin (Y) { direction : output; function : "A"; ' + timing("A", "combinational") + '} } '
       'cell (FF_SVT) { area : 2; ff (IQ,IQN) { next_state : "D"; clocked_on : "CK"; } '
       'pin (D) { direction : input; capacitance : 0.001; '
       'timing () { related_pin : "CK"; timing_type : setup_rising; '
       'rise_constraint (scalar) { values ("0.03"); } fall_constraint (scalar) { values ("0.03"); } } '
       'timing () { related_pin : "CK"; timing_type : hold_rising; '
       'rise_constraint (scalar) { values ("0.01"); } fall_constraint (scalar) { values ("0.01"); } } } '
       'pin (CK) { direction : input; clock : true; capacitance : 0.001; } '
       'pin (Q) { direction : output; function : "IQ"; '
       + timing("CK", "rising_edge", "non_unate") + '} } }')
NET = """module v24_test(input clk, input d, output q2, output q3);
wire c, c1, c2, c3, q1, n2, n3;
BUF_SVT common_clk(.A(clk),.Y(c));
BUF_SVT launch_clk(.A(c),.Y(c1));
BUF_SVT capture2_clk(.A(c),.Y(c2));
BUF_SVT capture3_clk(.A(c),.Y(c3));
FF_SVT r1(.D(d),.CK(c1),.Q(q1));
BUF_SVT data2(.A(q1),.Y(n2));
BUF_SVT data3(.A(q1),.Y(n3));
FF_SVT r2(.D(n2),.CK(c2),.Q(q2));
FF_SVT r3(.D(n3),.CK(c3),.Q(q3));
endmodule
"""


def quote(path):
    return "{" + str(path).replace("\\", "/") + "}"


with tempfile.TemporaryDirectory(prefix="opensta v24 native ") as tmp:
    root = Path(tmp)
    (root / "test.lib").write_text(LIB)
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
set paths [find_timing_paths -from [get_pins r1/CK] -to [get_pins {{r2/D r3/D}}] -path_delay max -group_path_count 10 -endpoint_count 2]
if {{[llength $paths] == 0}} {{ error "No native test paths" }}
report_design_variation $paths -samples 2000 -tail_samples 2000 -sigma_limit 3 -seed 7 -bottlenecks 2 -python {quote(sys.executable)} -output_dir {quote(root / 'design run')}
report_variation_bottleneck $paths -clock_paths exclude -exclude_VT ULVT -sigma_threshold 0.0 -max_violators 2 -python {quote(sys.executable)} -script_dir {quote(SCRIPTS)} -output_dir {quote(root / 'bottleneck run')}
if {{![catch {{report_design_variation $paths -samples 1}}]}} {{ error "sample validation missing" }}
if {{![catch {{report_design_variation $paths -sigma_limit Inf}}]}} {{ error "sigma validation missing" }}
if {{![catch {{report_variation_bottleneck $paths -clock_paths invalid}}]}} {{ error "clock validation missing" }}
if {{![catch {{report_variation_bottleneck $paths -sigma_threshold Inf}}]}} {{ error "threshold validation missing" }}
if {{![catch {{report_variation_bottleneck $paths -python {quote(sys.executable)} -script_dir {quote(SCRIPTS)} -output_dir {quote(root / 'bottleneck run')}}}]}} {{ error "overwrite protection missing" }}
set hold [find_timing_paths -from [get_pins r1/CK] -to [get_pins r2/D] -path_delay min -endpoint_count 1]
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
