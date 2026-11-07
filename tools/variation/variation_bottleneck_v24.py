#!/usr/bin/env python3
"""V24 single-file export. Requires Python 3.7+, NumPy (default_rng), SciPy.
No project modules are imported. Full path slack model retained.
Clock option filters final report rows only; all cells are always calculated.
"""
from __future__ import annotations

from pathlib import Path as _variation_bottleneck_v24__Path

def _timing_report_parser_V24__row_arc_keys(rows):
    return {cur.point: f'{cur.instance}:{prev.pin}:{prev.transition}->{cur.pin}:{cur.transition}' for prev, cur in zip(rows, rows[1:]) if prev.instance == cur.instance}

import numpy as _generic_design_variation_pin_arc_ps_standalone_V24__np

def _generic_design_variation_pin_arc_ps_standalone_V24__linear_model(paths):
    keys = sorted({arc.key for p in paths for arc in p.data_arcs + p.capture_arcs})
    index = {key: i for i, key in enumerate(keys)}

    def segment(rows, common):
        co = _generic_design_variation_pin_arc_ps_standalone_V24__np.zeros(len(keys))
        mean = 0.0
        prefix = _generic_design_variation_pin_arc_ps_standalone_V24__np.zeros(len(keys))
        pm = 0.0
        seen = False
        rk = _timing_report_parser_V24__row_arc_keys(rows)
        for row in rows:
            mean += row.incr_mean
            key = rk.get(row.point)
            if key is not None:
                co[index[key]] += row.incr_sigma
            if row.point == common:
                prefix = co.copy()
                pm = mean
                seen = True
        return (mean, co, pm, prefix, seen)
    means = []
    rows = []
    audit = []
    for p in paths:
        dm, dc, dpm, dpc, ds = segment(p.data_rows, p.last_common_pin)
        cm, cc, cpm, cpc, cs = segment(p.capture_rows, p.last_common_pin)
        mean = p.capture_edge_time + cm + p.clock_uncertainty + p.library_setup_time - p.launch_edge_time - dm
        co = cc - dc
        if p.last_common_pin:
            if not (ds and cs):
                raise ValueError('Unmatched common point ' + p.last_common_pin)
            mean += p.launch_edge_time + dpm - cpm
            co += dpc - cpc
        else:
            mean += p.crpr
        report_mean = p.required_mean - p.arrival_mean
        audit.append({'path_id': p.path_id, 'nominal_reconstruction_delta_ns': mean - report_mean})
        means.append(report_mean)
        rows.append(co)
    return (_generic_design_variation_pin_arc_ps_standalone_V24__np.asarray(means), _generic_design_variation_pin_arc_ps_standalone_V24__np.asarray(rows), keys, audit)

import re as _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__re

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__split_blocks(text: str) -> list[str]:
    starts = [m.start() for m in _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__re.finditer('(?m)^\\s{2}Startpoint:', text)]
    if not starts:
        raise ValueError('δ�ҵ� Startpoint:����������� report_timing �ı���')
    return [text[a:b] for a, b in zip(starts, starts[1:] + [len(text)])]

import re as _variation_bottleneck_v9__re

_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__FLOAT = '[-+]?\\d+(?:\\.\\d+)?(?:[eE][-+]?\\d+)?'

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__numbers(text: str) -> list[float]:
    return [float(x) for x in _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__re.findall(_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__FLOAT, text)]

_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__CELL_ROW_RE = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__re.compile(f'^\\s*(?P<point>.+?/(?P<pin>[^/\\s]+))\\s+\\((?P<cell>[^()]*)\\)(?P<tail>.*)$')

def _variation_bottleneck_v9__corner_contexts(text):
    """Read current PT -variation Incr Mean / Sensit / Corner / Value schema.

    Only actual cell-arc output points are consumed by analyze(). Clock endpoint
    rows with only Path columns may be shorter and are not corner-delay arcs.
    """
    if not _variation_bottleneck_v9__re.search('\\bMean\\s+Sensit\\s+Corner\\s+Value\\b', text):
        raise ValueError('Expected PT Incr Mean/Sensit/Corner/Value columns')
    result = {}
    for i, block in enumerate(_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__split_blocks(text), 1):
        section = 'data'
        for line in block.splitlines():
            if line.strip().startswith('data arrival time'):
                section = 'capture'
                continue
            match = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__CELL_ROW_RE.match(line.rstrip())
            if not match or '(net)' in line:
                continue
            values = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__numbers(match.group('tail').split('&', 1)[0])
            if len(values) >= 7:
                result[i - 1, section, match.group('point').strip()] = dict(nominal=values[2], sensit=values[3], corner=values[4], value=values[5])
    return result

from dataclasses import dataclass as _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__dataclass

@_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__dataclass
class _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__Arc:
    key: str
    section: str
    instance: str
    input_pin: str
    output_pin: str
    mean: float
    sigma: float

@_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__dataclass
class _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__PinRow:
    point: str
    instance: str
    pin: str
    cell: str
    incr_mean: float
    incr_sigma: float

@_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__dataclass
class _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__TimingRow:
    """A cell-point row in report order; input rows represent fixed net delay."""
    point: str
    instance: str
    pin: str
    cell: str
    incr_mean: float
    incr_sigma: float
    is_input: bool

@_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__dataclass
class _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__PathData:
    path_id: str
    startpoint: str
    endpoint: str
    path_group: str
    arrival_mean: float
    required_mean: float
    crpr: float
    clock_uncertainty: float
    library_setup_time: float
    data_arcs: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__Arc]
    capture_arcs: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__Arc]
    input_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__PinRow]
    data_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__TimingRow]
    capture_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__TimingRow]
    launch_edge_time: float
    capture_edge_time: float
    last_common_pin: str

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__parse_timing_row(line: str) -> _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__TimingRow | None:
    """Parse a cell row and retain every cell point for cumulative timing."""
    m = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__CELL_ROW_RE.match(line.rstrip())
    if not m or '(net)' in line or line.lstrip().startswith('clock '):
        return None
    values = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__numbers(m.group('tail').split('&', 1)[0])
    if len(values) < 4:
        return None
    point = m.group('point').strip()
    instance, pin = point.rsplit('/', 1)
    return _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__TimingRow(point=point, instance=instance, pin=pin, cell=m.group('cell').strip(), incr_mean=values[2], incr_sigma=values[3], is_input=pin not in {'Y', 'Z', 'ZN', 'Q', 'QN', 'QB', 'O', 'CO'})

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__parse_pin_row(line: str) -> _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__PinRow | None:
    """���� cell point �У�ȡ cell �� Incr ����ĵ� 3/4 �����֡�"""
    m = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__CELL_ROW_RE.match(line.rstrip())
    if not m:
        return None
    if '(net)' in line or line.lstrip().startswith('clock '):
        return None
    tail = m.group('tail')
    before_amp = tail.split('&', 1)[0]
    values = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__numbers(before_amp)
    if len(values) < 4:
        return None
    point = m.group('point').strip()
    instance, pin = point.rsplit('/', 1)
    return _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__PinRow(point=point, instance=instance, pin=pin, cell=m.group('cell').strip(), incr_mean=values[2], incr_sigma=values[3])

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__summary_value(line: str) -> float | None:
    values = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__numbers(line)
    return values[0] if values else None

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__edge_value(line: str) -> float | None:
    """Read the first numeric value after the clock point descriptor."""
    close = line.find(')')
    values = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__numbers(line[close + 1:] if close >= 0 else line)
    return values[-3] if len(values) >= 3 else values[0] if values else None

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__header(block: str, name: str) -> str:
    m = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__re.search(f'(?m)^\\s{{2}}{_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__re.escape(name)}:\\s*(.+)$', block)
    return m.group(1).strip() if m else ''

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__parse_block(block: str, index: int) -> _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__PathData:
    data_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__PinRow] = []
    capture_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__PinRow] = []
    input_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__PinRow] = []
    data_timing_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__TimingRow] = []
    capture_timing_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__TimingRow] = []
    section = 'data'
    arrival_mean = None
    required_mean = None
    crpr = uncertainty = setup = 0.0
    launch_edge_time = 0.0
    capture_edge_time = 0.0
    launch_edge_seen = False
    capture_edge_seen = False
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith('data arrival time'):
            if arrival_mean is None:
                arrival_mean = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__summary_value(stripped)
                section = 'capture'
            continue
        if stripped.startswith('data required time') and required_mean is None:
            required_mean = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__summary_value(stripped)
            continue
        if stripped.startswith('clock reconvergence pessimism'):
            vals = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__numbers(stripped)
            if vals:
                crpr = vals[0]
            continue
        if stripped.startswith('clock uncertainty'):
            vals = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__numbers(stripped)
            if vals:
                uncertainty = vals[0]
            continue
        if stripped.startswith('library setup time'):
            vals = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__numbers(stripped)
            if len(vals) >= 2:
                setup = vals[1]
            elif vals:
                setup = vals[0]
            continue
        if stripped.startswith('clock ') and 'edge)' in stripped:
            value = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__edge_value(line)
            if value is not None:
                if section == 'data' and (not launch_edge_seen):
                    launch_edge_time = value
                    launch_edge_seen = True
                elif section == 'capture' and (not capture_edge_seen):
                    capture_edge_time = value
                    capture_edge_seen = True
        timing_row = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__parse_timing_row(line)
        if timing_row is not None:
            if section == 'data':
                data_timing_rows.append(timing_row)
            else:
                capture_timing_rows.append(timing_row)
        row = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__parse_pin_row(line)
        if row is None:
            continue
        if section == 'data':
            data_rows.append(row)
        else:
            capture_rows.append(row)
    if arrival_mean is None or required_mean is None:
        raise ValueError(f'path{index}: δ�ҵ� data arrival/required time �����С�')

    def pair(rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__PinRow], section_name: str) -> list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__Arc]:
        arcs: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__Arc] = []
        active_rows = rows
        for prev, cur in zip(active_rows, active_rows[1:]):
            if prev.instance != cur.instance:
                continue
            input_rows.append(prev)
            arcs.append(_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__Arc(key=f'{cur.instance}:{prev.pin}->{cur.pin}', section=section_name, instance=cur.instance, input_pin=prev.pin, output_pin=cur.pin, mean=cur.incr_mean, sigma=cur.incr_sigma))
        return arcs
    data_arcs = pair(data_rows, 'data')
    capture_arcs = pair(capture_rows, 'capture')
    if not data_arcs:
        raise ValueError(f'path{index}: û��ʶ�� data pin-to-pin arc��')
    return _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__PathData(path_id=f'path{index}', startpoint=_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__header(block, 'Startpoint'), endpoint=_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__header(block, 'Endpoint'), path_group=_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__header(block, 'Path Group'), arrival_mean=arrival_mean, required_mean=required_mean, crpr=crpr, clock_uncertainty=uncertainty, library_setup_time=setup, data_arcs=data_arcs, capture_arcs=capture_arcs, input_rows=input_rows, data_rows=data_timing_rows, capture_rows=capture_timing_rows, launch_edge_time=launch_edge_time, capture_edge_time=capture_edge_time, last_common_pin=_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__header(block, 'Last common pin'))

import re as _timing_report_parser_V24__re

def _timing_report_parser_V24__parse_block(block, index):
    p = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__parse_block(block, index)
    annotated = {'data': [], 'capture': []}
    sec = 'data'
    for line in block.splitlines():
        if line.strip().startswith('data arrival time') and sec == 'data':
            sec = 'capture'
            continue
        r = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__parse_timing_row(line)
        if r is not None:
            m = _timing_report_parser_V24__re.search('\\s([rf])(?:\\s+[-+0-9.eE]+)?\\s*$', line)
            annotated[sec].append((r.point, m[1] if m else '?'))
    for sec, rows in [('data', p.data_rows), ('capture', p.capture_rows)]:
        assert len(rows) == len(annotated[sec])
        for row, (point, edge) in zip(rows, annotated[sec]):
            assert row.point == point
            row.transition = edge
        arcs = []
        for prev, cur in zip(rows, rows[1:]):
            if prev.instance == cur.instance:
                key = f'{cur.instance}:{prev.pin}:{prev.transition}->{cur.pin}:{cur.transition}'
                arcs.append(_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__Arc(key, sec, cur.instance, prev.pin, cur.pin, cur.incr_mean, cur.incr_sigma))
        if sec == 'data':
            p.data_arcs = arcs
        else:
            p.capture_arcs = arcs
    return p

from pathlib import Path as _hsfr_tail_models_v16__Path

def _hsfr_tail_models_v16__annotate_margins(contexts, input_file):
    paths = [_timing_report_parser_V24__parse_block(b, i) for i, b in enumerate(_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__split_blocks(_hsfr_tail_models_v16__Path(input_file).read_text()), 1)]
    means = [p.required_mean - p.arrival_mean for p in paths]
    audit = {}
    for c in contexts:
        i = int(c['path_index'])
        r = float(c['single_path_sigma_ratio_est']) if c.get('single_path_sigma_ratio_est') is not None else 0.0
        sigma = float(c['delay_sigma_1']) / r if r else 0.0
        c['path_nominal_slack'] = means[i]
        c['path_analytic_sigma'] = sigma
        c['unclamped_standardized_margin'] = means[i] / sigma if sigma else None
        c['hsfr_reference_margin'] = max(3.0, means[i] / sigma) if sigma else 3.0
        c['path_group'] = paths[i].path_group
        audit[i] = dict(path_id=paths[i].path_id, endpoint=paths[i].endpoint, path_group=paths[i].path_group, slack_mean=means[i], slack_sigma=sigma, reference_margin=c['hsfr_reference_margin'])
    return list(audit.values())

from collections import defaultdict as _hsfr_tail_models_v16__defaultdict

from scipy.special import ndtr as _hsfr_tail_models__ndtr

_hsfr_tail_models__TAIL_START = 4.0

_hsfr_tail_models__TAIL_END = 7.0

_hsfr_tail_models__TAIL_MASS = float(_hsfr_tail_models__ndtr(-_hsfr_tail_models__TAIL_START) - _hsfr_tail_models__ndtr(-_hsfr_tail_models__TAIL_END))

import math as _hsfr_tail_models_v16__math

from functools import lru_cache as _hsfr_tail_models_v16__lru_cache

from scipy.integrate import quad as _hsfr_tail_models_v16__quad

from scipy.special import ndtr as _hsfr_tail_models_v16__ndtr

@_hsfr_tail_models_v16__lru_cache(maxsize=65536)
def _hsfr_tail_models_v16__marginal(r, margin):
    r = float(r)
    margin = float(margin)
    if not _hsfr_tail_models_v16__math.isfinite(r) or not -1 <= r <= 1:
        raise ValueError('r outside conditional residual model')
    if r == -1:
        upper = min(_hsfr_tail_models__TAIL_END, -margin)
        if upper <= _hsfr_tail_models__TAIL_START:
            return 0.0
        return float(_hsfr_tail_models_v16__ndtr(-_hsfr_tail_models__TAIL_START) - _hsfr_tail_models_v16__ndtr(-upper))
    if r == 1:
        return max(0.0, float(_hsfr_tail_models_v16__ndtr(-max(_hsfr_tail_models__TAIL_START, margin)) - _hsfr_tail_models_v16__ndtr(-_hsfr_tail_models__TAIL_END)))
    residual = _hsfr_tail_models_v16__math.sqrt(1 - r * r)
    return float(_hsfr_tail_models_v16__quad(lambda z: _hsfr_tail_models_v16__math.exp(-z * z / 2) / _hsfr_tail_models_v16__math.sqrt(2 * _hsfr_tail_models_v16__math.pi) * float(_hsfr_tail_models_v16__ndtr((r * z - margin) / residual)), _hsfr_tail_models__TAIL_START, _hsfr_tail_models__TAIL_END, epsabs=1e-16, epsrel=1e-11)[0])

def _hsfr_tail_models_v16__estimate_cells(contexts, version=16):
    groups = _hsfr_tail_models_v16__defaultdict(list)
    seen = set()
    for c in contexts:
        sig = (c['path_id'], c['section'], c['arc_key'])
        if sig in seen:
            raise ValueError('duplicate context')
        seen.add(sig)
        if c.get('single_path_sigma_ratio_est') is None or float(c['delay_sigma_1']) == 0:
            continue
        groups[c['cell'], c['arc_key']].append(c)
    cells = {}
    sources = []
    for (cell, arc), cs in sorted(groups.items()):
        ps = [_hsfr_tail_models_v16__marginal(float(c['hsfr_conditional_coefficient']), float(c['hsfr_reference_margin'])) / _hsfr_tail_models__TAIL_MASS for c in cs]
        score = _hsfr_tail_models_v16__math.inf if any((p >= 1 for p in ps)) else -_hsfr_tail_models_v16__math.fsum((_hsfr_tail_models_v16__math.log1p(-p) for p in ps))
        h = _hsfr_tail_models__TAIL_MASS * -_hsfr_tail_models_v16__math.expm1(-score)
        sources.append(dict(cell=cell, arc_key=arc, HSFR_est=h, log_survival_score=score if _hsfr_tail_models_v16__math.isfinite(score) else None, path_context_count=len(cs), margin_min=min((c['hsfr_reference_margin'] for c in cs)), margin_max=max((c['hsfr_reference_margin'] for c in cs)), tail_cap=_hsfr_tail_models__TAIL_MASS))
        candidate = (h, score)
        if cell not in cells or candidate > cells[cell]['ordering']:
            cells[cell] = dict(HSFR_est=h, hsfr_source_arc=arc, hsfr_context_count=len(cs), ordering=candidate)
    for r in cells.values():
        r.pop('ordering')
    return (cells, sources)

from collections import defaultdict as _bottleneck_sigma_ratio_v13__defaultdict

from functools import lru_cache as _bottleneck_sigma_ratio_v13__lru_cache

from scipy.special import ndtr as _bottleneck_sigma_ratio_v13__ndtr

_bottleneck_sigma_ratio_v13__TAIL_START = 4.0

_bottleneck_sigma_ratio_v13__TAIL_END = 7.0

_bottleneck_sigma_ratio_v13__TAIL_MASS = float(_bottleneck_sigma_ratio_v13__ndtr(-_bottleneck_sigma_ratio_v13__TAIL_START) - _bottleneck_sigma_ratio_v13__ndtr(-_bottleneck_sigma_ratio_v13__TAIL_END))

import math as _bottleneck_sigma_ratio_v13__math

from scipy.integrate import quad as _bottleneck_sigma_ratio_v13__quad

_bottleneck_sigma_ratio_v13__REFERENCE_MARGIN = 3.0

@_bottleneck_sigma_ratio_v13__lru_cache(maxsize=32768)
def _bottleneck_sigma_ratio_v13__conditional_failure(r):
    r = float(r)
    if not _bottleneck_sigma_ratio_v13__math.isfinite(r) or r < 0:
        raise ValueError('Invalid context ratio')
    if r >= 1:
        return float((_bottleneck_sigma_ratio_v13__ndtr(-max(_bottleneck_sigma_ratio_v13__TAIL_START, _bottleneck_sigma_ratio_v13__REFERENCE_MARGIN / r)) - _bottleneck_sigma_ratio_v13__ndtr(-_bottleneck_sigma_ratio_v13__TAIL_END)) / _bottleneck_sigma_ratio_v13__TAIL_MASS)
    residual = _bottleneck_sigma_ratio_v13__math.sqrt(max(1 - r * r, 1e-30))
    value = _bottleneck_sigma_ratio_v13__quad(lambda z: _bottleneck_sigma_ratio_v13__math.exp(-0.5 * z * z) / _bottleneck_sigma_ratio_v13__math.sqrt(2 * _bottleneck_sigma_ratio_v13__math.pi) * float(_bottleneck_sigma_ratio_v13__ndtr((r * z - _bottleneck_sigma_ratio_v13__REFERENCE_MARGIN) / residual)), _bottleneck_sigma_ratio_v13__TAIL_START, _bottleneck_sigma_ratio_v13__TAIL_END, epsabs=1e-16, epsrel=1e-10)[0] / _bottleneck_sigma_ratio_v13__TAIL_MASS
    return max(0.0, min(float(value), 1.0))

def _bottleneck_sigma_ratio_v13__select_contexts(contexts, power=None):
    groups = _bottleneck_sigma_ratio_v13__defaultdict(lambda: _bottleneck_sigma_ratio_v13__defaultdict(list))
    for c in contexts:
        if c.get('single_path_sigma_ratio_est') is not None:
            groups[c['cell']][c['arc_key']].append(c)
    selected = {}
    scores = []
    for cell, arcs in sorted(groups.items()):
        ranks = {}
        for arc, cs in sorted(arcs.items()):
            seen = set()
            terms = []
            for c in cs:
                sig = (c['path_id'], c['section'], c['arc_key'])
                if sig in seen:
                    raise ValueError('Duplicate context ' + str(sig))
                seen.add(sig)
                p = _bottleneck_sigma_ratio_v13__conditional_failure(float(c['single_path_sigma_ratio_est']))
                terms.append(-_bottleneck_sigma_ratio_v13__math.log1p(-min(p, 1 - 1e-15)))
            rank = _bottleneck_sigma_ratio_v13__math.fsum(terms)
            ranks[arc] = rank
            scores.append(dict(cell=cell, arc_key=arc, score=rank, context_count=len(cs), normalized_union_failure=-_bottleneck_sigma_ratio_v13__math.expm1(-rank), minimum_context_ratio=min((float(c['single_path_sigma_ratio_est']) for c in cs)), max_context_ratio=max((float(c['single_path_sigma_ratio_est']) for c in cs)), source_tail_saturated_at_1e_minus7=_bottleneck_sigma_ratio_v13__math.exp(-rank) <= 1e-07))
        arc = min(arcs, key=lambda k: (-ranks[k], k))
        c = min(arcs[arc], key=lambda c: (-float(c['single_path_sigma_ratio_est']), int(c['path_index']), c['section']))
        selected[cell] = (c, ranks[arc])
    return (selected, scores)

import re as _variation_bottleneck_v24__re

import hashlib as _variation_bottleneck_v8__hashlib

from pathlib import Path as _variation_bottleneck_v8__Path

def _variation_bottleneck_v8__sha(path):
    return _variation_bottleneck_v8__hashlib.sha256(_variation_bottleneck_v8__Path(path).read_bytes()).hexdigest()

import numpy as _variation_bottleneck_v24__np

def _bottleneck_v24_launch_boundary(path):
    """Find the launching sequential instance in pre-arrival report rows."""
    name = path.startpoint.split(' (', 1)[0].strip()
    for i, row in enumerate(path.data_rows):
        if row.instance == name or row.point == name:
            return i, row.instance
    sequential = any(word in path.startpoint.lower() for word in ('flip-flop', 'latch', 'edge-triggered'))
    return (None, None) if sequential else (0, None)


def _bottleneck_v24_path_role(path, section, arc, boundary):
    if section == 'capture':
        return 'capture_clock'
    first, launch_instance = boundary
    if first is None:
        return 'unknown_launch_region'
    if arc.instance == launch_instance:
        return 'clock_to_q' if arc.output_pin.upper() in {'Q', 'QN', 'QB'} else 'launch_sequential'
    # The parser defines an arc only for adjacent pins on the same instance.
    for i, (prev, cur) in enumerate(zip(path.data_rows, path.data_rows[1:])):
        key = f'{cur.instance}:{prev.pin}:{prev.transition}->{cur.pin}:{cur.transition}'
        if prev.instance == cur.instance and key == arc.key:
            return 'launch_clock' if i + 1 < first else 'data'
    raise ValueError('Cannot locate arc occurrence: ' + arc.key)


def _bottleneck_v24_terminal_registers(path, block):
    pins = {}
    points = {}
    for line in block.splitlines():
        match = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__CELL_ROW_RE.match(line.rstrip())
        if not match or '(net)' in line:
            continue
        point = match.group('point').strip()
        instance, pin = point.rsplit('/', 1)
        pins.setdefault(instance, set()).add(pin.upper())
        points[point] = instance
    protected = set()
    for header in (path.startpoint, path.endpoint):
        name = header.split(' (', 1)[0].strip()
        instance = name if name in pins else points.get(name)
        if instance is None:
            continue
        sequential = any(word in header.lower() for word in ('flip-flop', 'latch', 'edge-triggered'))
        if sequential or pins[instance].intersection({'CK', 'CP', 'CLK', 'CKN', 'CLKN', 'CKP'}):
            protected.add(instance)
    return protected


def _bottleneck_v24_normalize_vt(value):
    if value is None:
        return []
    values = [value] if isinstance(value, str) else value
    tags = set()
    for item in values:
        for tag in _variation_bottleneck_v24__re.split(r'[,;\s]+', str(item).upper()):
            if not tag:
                continue
            if not _variation_bottleneck_v24__re.fullmatch(r'[A-Z][A-Z0-9]*', tag):
                raise ValueError('Invalid VT label: ' + tag)
            tags.add(tag)
    return sorted(tags)


def _bottleneck_v24_vt_matches(lib_cell, excluded):
    if not excluded:
        return False
    # Longest labels first: requesting LVT must not also match ULVT/SLVT.
    known = {'ULVT', 'SLVT', 'ELVT', 'LLVT', 'LVT', 'SVT', 'RVT', 'HVT', 'UHVT'}
    labels = sorted(known.union(excluded), key=lambda tag: (-len(tag), tag))
    found = _variation_bottleneck_v24__re.findall('|'.join(map(_variation_bottleneck_v24__re.escape, labels)), str(lib_cell).upper())
    return bool(set(found).intersection(excluded))


def _variation_bottleneck_v24__predict(input_file, clock_paths="include"):
    if clock_paths not in {"include", "exclude"}:
        raise ValueError("clock_paths must be include or exclude")
    text = _variation_bottleneck_v24__Path(input_file).read_text()
    if _variation_bottleneck_v24__re.search('^\\s*Path Type:\\s*(min|hold)\\b', text, _variation_bottleneck_v24__re.M | _variation_bottleneck_v24__re.I):
        raise ValueError('V24 HSFR validation is for setup/max reports only')
    paths = [_timing_report_parser_V24__parse_block(b, i) for i, b in enumerate(_generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__split_blocks(text), 1)]
    if not paths:
        raise ValueError('No timing paths')
    means, a, keys, audit = _generic_design_variation_pin_arc_ps_standalone_V24__linear_model(paths)
    metadata = _variation_bottleneck_v9__corner_contexts(text)
    contexts = []
    clock_cells = set()
    protected_registers = set()
    raw_blocks = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__split_blocks(text)
    for i, p in enumerate(paths):
        sd = float(_variation_bottleneck_v24__np.linalg.norm(a[i]))
        boundary = _bottleneck_v24_launch_boundary(p)
        protected_registers.update(_bottleneck_v24_terminal_registers(p, raw_blocks[i]))
        if clock_paths == "exclude" and boundary[0] is None:
            raise ValueError(p.path_id + ": cannot locate launching sequential pin; cannot safely exclude clock paths")
        # Clock membership reads raw pin rows too: capture register clock-pin
        # lines can contain only Path columns and be absent from parsed arc rows.
        capture = False
        launch_seen = boundary[1] is None
        for line in raw_blocks[i].splitlines():
            if line.strip().startswith('data arrival time'):
                capture = True
            match = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V24_pt2026_compat__CELL_ROW_RE.match(line.rstrip())
            if not match or '(net)' in line:
                continue
            point = match.group('point').strip()
            instance = point.rsplit('/', 1)[0]
            if capture:
                clock_cells.add(instance)
            elif not launch_seen:
                clock_cells.add(instance)
                if instance == boundary[1]:
                    launch_seen = True
        for section, arcs, rs in [('data', p.data_arcs, p.data_rows), ('capture', p.capture_arcs, p.capture_rows)]:
            points = {r.point: r for r in rs}
            for ar in arcs:
                pin = ar.instance + '/' + ar.output_pin
                row = points[pin]
                md = metadata[i, section, pin]
                role = _bottleneck_v24_path_role(p, section, ar, boundary)
                eligible = True  # every occurrence participates in calculation in both modes
                contexts.append(dict(path_id=p.path_id, path_index=i, endpoint=p.endpoint, section=section, path_role=role, included_in_bottleneck=eligible, cell=ar.instance, lib_cell=row.cell, arc_key=ar.key, output_pin=pin, output_edge=row.transition, input_pin=ar.input_pin, delay_mean=ar.mean, delay_sigma_1=abs(ar.sigma), delay_sensitivity=ar.sigma, single_path_sigma_ratio_est=abs(ar.sigma) / sd if sd else None, variation_est=abs(md['corner'] - md['nominal'])))
    # Display Sigma_ratio stays based on raw arc sigma. HSFR must instead
    # use the SAME signed coefficients as the final CRPR-corrected slack model.
    coefficient_index = {key: j for j, key in enumerate(keys)}
    for c in contexts:
        i = int(c['path_index'])
        sd = float(_variation_bottleneck_v24__np.linalg.norm(a[i]))
        coefficient = float(a[i, coefficient_index[c['arc_key']]])
        risk_coefficient = -coefficient / sd if sd else 0.0
        if not _bottleneck_report_format__math.isfinite(risk_coefficient) or abs(risk_coefficient) > 1 + 1e-12:
            raise ValueError('Invalid normalized final slack coefficient: ' + c['path_id'] + ' ' + c['arc_key'])
        c['slack_coefficient_after_crpr'] = coefficient
        c['hsfr_conditional_coefficient'] = max(-1.0, min(1.0, risk_coefficient))
    margins = _hsfr_tail_models_v16__annotate_margins(contexts, input_file)
    active = contexts  # report visibility must never change HSFR or selector input
    estimates, sources = _hsfr_tail_models_v16__estimate_cells(active)
    selected, _ = _bottleneck_sigma_ratio_v13__select_contexts(active)
    rows = []
    for cell, (c, score) in selected.items():
        r = dict(c)
        r.update(estimates.get(cell, dict(HSFR_est=0)), sigma_ratio_est=c['single_path_sigma_ratio_est'], yield_delta_ppm=None, paired_se_ppm=None)
        rows.append(r)
    rows.sort(key=lambda r: (-r['HSFR_est'], r['cell']))
    for i, r in enumerate(rows, 1):
        r['rank'] = i
        r['on_clock_path'] = r['cell'] in clock_cells
        r['protected_terminal_register'] = r['cell'] in protected_registers
    summary = dict(version='V24', samples='analytic integral (no MC)', seed='N/A', path_count=len(paths), input=str(_variation_bottleneck_v24__Path(input_file).resolve()), input_sha256=_variation_bottleneck_v8__sha(input_file), tail_cap=_hsfr_tail_models__TAIL_MASS, native_formula_claim=False, parsing_audit=audit, sigma_ratio_selection='V13 selector; may differ from HSFR source', limitations=['Case-derived formula; unresolved aggregation errors on large path sets.', 'Independent residual survival approximation; not exact correlated design failure probability.'])
    role_counts = {}
    for c in contexts:
        role_counts[c['path_role']] = role_counts.get(c['path_role'], 0) + 1
    hidden = [r['cell'] for r in rows if clock_paths == 'exclude' and r['on_clock_path'] and not r['protected_terminal_register']]
    summary.update(clock_paths=clock_paths, clock_filter_scope='final report.txt cell rows only; all calculations and CSV rows retained',
                   path_role_counts=role_counts, total_arc_contexts=len(contexts), included_arc_contexts=len(contexts),
                   excluded_arc_contexts=0, calculated_cells=len(rows), reported_cells=len(rows)-len(hidden),
                   hidden_report_cells=hidden, clock_path_cells=sorted(clock_cells), clock_to_q_calculated=True, protected_terminal_registers=sorted(protected_registers),
                   classification='hide clock-path cells as a whole, except startpoint/endpoint registers; all cells calculated')
    return (summary, contexts, rows, sources, margins)

import time as _variation_bottleneck_v24__time

import re as _variation_bottleneck_v7__re

from pathlib import Path as _variation_bottleneck_v7__Path

import math as _variation_bottleneck_v7__math

def _variation_bottleneck_v7__read_ps_reference(file):
    """Read five-column native PS text; HSFR is normalized to probability units."""
    text = _variation_bottleneck_v7__Path(file).read_text(encoding='utf-8', errors='replace')
    number = '[-+]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:[eE][-+]?\\d+)?'
    pattern = _variation_bottleneck_v7__re.compile('^\\s*(\\S+)\\s+(\\S+)\\s+(' + number + ')\\s+(' + number + ')\\s+(' + number + ')\\s*$')
    if not _variation_bottleneck_v7__re.search('\\bCell\\s+Lib_cell\\s+Variation\\s+Sigma_ratio\\s+HSFR\\b', text):
        raise ValueError('PS reference must contain the native Cell/Lib_cell/Variation/Sigma_ratio/HSFR header')
    units = _variation_bottleneck_v7__re.search('\\(\\s*[xX\\u00d7]\\s*(1(?:\\.0+)?[eE][-+]?\\d+)\\s*\\)', text)
    scale = float(units.group(1)) if units else 1.0
    result = {}
    for line in text.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        cell, lib, var, ratio, hsfr = match.groups()
        values = [float(var), float(ratio), float(hsfr)]
        if not all((_variation_bottleneck_v7__math.isfinite(x) and x >= 0 for x in values)):
            raise ValueError('Invalid native PS field values at ' + cell)
        row = dict(lib_cell=lib, variation=values[0], sigma_ratio=values[1], hsfr=values[2] * scale)
        if cell in result and result[cell] != row:
            raise ValueError('Conflicting duplicate PS rows at ' + cell)
        result[cell] = row
    if not result:
        raise ValueError('No native five-column PS cell rows parsed; use a text -nosplit report, not a screenshot')
    return result

import csv as _variation_bottleneck_v8__csv

def _variation_bottleneck_v8__write_csv(path, rows):
    if not rows:
        return
    with _variation_bottleneck_v8__Path(path).open('w', encoding='utf-8-sig', newline='') as f:
        w = _variation_bottleneck_v8__csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

import json as _variation_bottleneck_v24__json

import math as _bottleneck_report_format__math

def _bottleneck_report_format__format_v9_report(summary, rows, top=20):
    shown = rows[:top]

    def number(value, digits):
        if value is None or value == '':
            return 'N/A'
        value = float(value)
        return f'{value:.{digits}f}' if _bottleneck_report_format__math.isfinite(value) else 'N/A'
    headings = ['Cell', 'Lib_cell', 'Variation', 'Sigma_ratio', 'HSFR', 'Rank']
    body = []
    for r in shown:
        hsfr = r.get('HSFR_est')
        body.append([str(r['cell']), str(r.get('lib_cell') or 'N/A'), number(r['variation_est'], 9), number(r.get('sigma_ratio_est'), 9), number(float(hsfr) * 1000 if hsfr is not None and hsfr != '' else None, 9), str(r['rank'])])
    widths = [max(len(headings[i]), max((len(row[i]) for row in body), default=0)) for i in range(len(headings))]
    widths[0] = max(widths[0], 24)
    widths[1] = max(widths[1], 16)

    def rowtext(row):
        return '   ' + '  '.join((value.ljust(widths[i]) if i < 2 else value.rjust(widths[i]) for i, value in enumerate(row)))
    rule = '   ' + '-' * (len(rowtext(headings)) - 3)
    units = ['', '', '(time unit)', '', '(x 1e-3)', '']
    widths[:] = [max(w, len(units[i])) for i, w in enumerate(widths)]
    rule = '   ' + '-' * (len(rowtext(headings)) - 3)
    lines = ['****************************************', 'Report : variation bottleneck (Python V9)', '\t-nosplit', f'\t-max_violators {top}', 'Version: V9 (PS-style layout)', '****************************************', '', f"   Num of Samples: {summary['samples']}", f"   Num of Paths  : {summary['path_count']}", f"   Seed          : {summary['seed']}", '   Rank by       : HSFR_est (descending)', '', rowtext(headings), rowtext(units), rule]
    lines.extend((rowtext(row) for row in body))
    lines.extend([rule, f'   Displayed cells: {len(shown)}', '', '   Column definitions:', '   Variation       : Model estimate, abs(Incr Corner - Incr Mean); input time unit.', '   Sigma_ratio     : Model estimate using restricted, same-edge pin slack proxy.', '   HSFR            : HSFR_est; unavailable values shown as N/A, not zero.', '   Rank            : Existing rank by signed ordinary-yield removal gain.', '   PS reference values are separate in ps_comparison.csv.', '   Full calculated fields and arc provenance are retained in cells.csv / arc_contexts.csv.', ''])
    return '\n'.join(lines)

def _variation_bottleneck_v24__run(input_file, out, ps_report=None, clock_paths="include", exclude_VT=None, variation_threshold=None, sigma_threshold=None):
    out = _variation_bottleneck_v24__Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Refusing nonempty output directory')
    excluded_vt = _bottleneck_v24_normalize_vt(exclude_VT)
    if variation_threshold is not None:
        variation_threshold = float(variation_threshold)
        if not _bottleneck_report_format__math.isfinite(variation_threshold) or variation_threshold < 0:
            raise ValueError('variation_threshold must be finite and nonnegative, in input report time units')
    if sigma_threshold is not None:
        sigma_threshold = float(sigma_threshold)
        if not _bottleneck_report_format__math.isfinite(sigma_threshold) or sigma_threshold < 0:
            raise ValueError('sigma_threshold must be finite and nonnegative; Sigma_ratio is dimensionless')
    start = _variation_bottleneck_v24__time.monotonic()
    summary, contexts, rows, sources, margins = _variation_bottleneck_v24__predict(input_file, clock_paths=clock_paths)
    reference = _variation_bottleneck_v7__read_ps_reference(ps_report) if ps_report else {}
    by = {r['cell']: r for r in rows}
    comparison = []
    for cell, ref in reference.items():
        r = by.get(cell)
        h = r['HSFR_est'] if r else None
        comparison.append(dict(cell=cell, model_HSFR=h, ps_HSFR=ref['hsfr'], relative_error=h / ref['hsfr'] - 1 if h is not None and ref['hsfr'] else None, absolute_error=h - ref['hsfr'] if h is not None else None, model_sigma_ratio=r['sigma_ratio_est'] if r else None, ps_sigma_ratio=ref['sigma_ratio']))
    errors = [abs(c['relative_error']) * 100 for c in comparison if c['relative_error'] is not None]
    summary.update(runtime_seconds=_variation_bottleneck_v24__time.monotonic() - start, ps_reference=str(ps_report) if ps_report else None, ps_reference_sha256=_variation_bottleneck_v8__sha(ps_report) if ps_report else None, reference_use='comparison only', metrics=dict(cells=len(comparison), missing_cells=sum((c['model_HSFR'] is None for c in comparison)), median_relative_error_pct=float(_variation_bottleneck_v24__np.median(errors)) if errors else None, max_relative_error_pct=max(errors) if errors else None))
    hidden_clock = {r['cell'] for r in rows if clock_paths == 'exclude' and r['on_clock_path'] and not r['protected_terminal_register']}
    hidden_vt = {r['cell'] for r in rows if _bottleneck_v24_vt_matches(r.get('lib_cell', ''), excluded_vt)}
    hidden_variation = {r["cell"] for r in rows if variation_threshold is not None and float(r["variation_est"]) < variation_threshold}
    hidden_sigma = {r["cell"] for r in rows if sigma_threshold is not None and r.get("sigma_ratio_est") is not None and float(r["sigma_ratio_est"]) < sigma_threshold}
    hidden = hidden_clock.union(hidden_vt, hidden_variation, hidden_sigma)
    display_rows = [r for r in rows if r['cell'] not in hidden]
    summary.update(sigma_threshold=sigma_threshold, hidden_by_sigma=sorted(hidden_sigma), variation_threshold=variation_threshold, hidden_by_variation=sorted(hidden_variation), exclude_VT=excluded_vt, hidden_by_clock=sorted(hidden_clock), hidden_by_VT=sorted(hidden_vt),
                   hidden_report_cells=sorted(hidden), reported_cells=len(display_rows),
                   report_filter_scope='report.txt only; all cells calculated and complete CSV retained')
    summary.update(hsfr_coefficient_basis='negative final signed slack coefficient / path sigma, after common-clock correction', display_sigma_ratio_basis='raw arc sigma / path sigma; unchanged', zero_effect_contexts=sum(c['hsfr_conditional_coefficient'] == 0 for c in contexts))
    out.mkdir(parents=True, exist_ok=True)
    for name, data in [('cells', rows), ('arc_contexts', contexts), ('source_scores', sources), ('path_margins', margins), ('ps_comparison', comparison)]:
        _variation_bottleneck_v8__write_csv(out / (name + '.csv'), data)
    (out / 'summary.json').write_text(_variation_bottleneck_v24__json.dumps(summary, indent=2) + '\n')
    report = _bottleneck_report_format__format_v9_report(summary, display_rows, len(display_rows)).replace('V9', 'V24').replace('Yield_delta_ppm (descending)', 'HSFR_est (descending)')
    report = report.replace('restricted, same-edge pin slack proxy.', 'V13-selected path analytic slack sigma.')
    report = report.replace('Existing rank by signed ordinary-yield removal gain.', 'Descending analytic HSFR estimate.')
    report += '\nClock paths: ' + clock_paths + '; hidden report cells: ' + str(len(summary['hidden_report_cells'])) + '\n'
    report += 'All cells calculated; all CSV rows retained. Clock-path filtering affects report.txt only.\n'
    report += 'Clock exclude preserves startpoint/endpoint registers; other clock-path cells are hidden as whole instances.\n'
    report += 'Excluded VT labels: ' + (', '.join(excluded_vt) if excluded_vt else 'none') + '; hidden by VT: ' + str(len(hidden_vt)) + '\n'
    report += 'VT filtering uses Lib_cell labels and also applies to terminal registers. Rank retains the full-calculation rank.\n'
    report += 'Variation threshold (input time unit): ' + (str(variation_threshold) if variation_threshold is not None else 'none') + '; hide strictly below; hidden by variation: ' + str(len(hidden_variation)) + '\n'
    report += 'Sigma_ratio threshold (dimensionless): ' + (str(sigma_threshold) if sigma_threshold is not None else 'none') + '; hide strictly below; hidden by Sigma_ratio: ' + str(len(hidden_sigma)) + '\n'
    report += '\nHSFR: analytic V24 hypothesis; ordinary yield/SE not calculated.\nSigma_ratio: retained V13 context selector. Native data comparison-only.\n'
    (out / 'report.txt').write_text(report)
    return summary

if __name__ == '__main__':
    import argparse, json
    ap = argparse.ArgumentParser(description='Standalone Variation Bottleneck V24 with report-only cell-level clock-path filtering')
    ap.add_argument('input')
    ap.add_argument('--output_dir', required=True)
    ap.add_argument('--ps_report')
    ap.add_argument('--clock_paths', choices=('include', 'exclude'), default='include',
                    help='include: print all calculated cells (default); exclude: hide clock-path cells except startpoint/endpoint registers from report.txt only; all calculation/CSV data retained.')
    ap.add_argument('--exclude_VT', nargs='+', default=None, help='VT labels to hide in report.txt by Lib_cell name, e.g. ULVT or ULVT LVT; case-insensitive. Calculations/CSV unchanged.')
    ap.add_argument('--variation_threshold', type=float, default=None, help='Hide report.txt rows with Variation strictly below this nonnegative threshold, in input report time units; calculations/CSV unchanged.')
    ap.add_argument('--sigma_threshold', type=float, default=None, help='Hide report.txt rows with dimensionless Sigma_ratio strictly below this nonnegative threshold; calculations/CSV unchanged.')
    args = ap.parse_args()
    print(json.dumps(_variation_bottleneck_v24__run(args.input, args.output_dir, args.ps_report, clock_paths=args.clock_paths, exclude_VT=args.exclude_VT, variation_threshold=args.variation_threshold, sigma_threshold=args.sigma_threshold), indent=2))
