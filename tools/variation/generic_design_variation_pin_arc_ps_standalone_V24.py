#!/usr/bin/env python3
"""V24 single-file export. Requires Python 3.7+, NumPy (default_rng), SciPy.
No project modules are imported. GPD uses the ordinary MC WNS bank (N);
ALOE uses separate conditional sample banks (M). Linear path model unchanged.
"""
from __future__ import annotations

def _timing_report_parser_V18__row_arc_keys(rows):
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
        rk = _timing_report_parser_V18__row_arc_keys(rows)
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

def _generic_design_variation_pin_arc_ps_standalone_V24__reduce_dominated(means, coefficients):
    """Same coefficient vector => the smallest mean dominates the union exactly."""
    means = _generic_design_variation_pin_arc_ps_standalone_V24__np.asarray(means, dtype=float)
    a = _generic_design_variation_pin_arc_ps_standalone_V24__np.asarray(coefficients, dtype=float)
    groups = {}
    for i, row in enumerate(a):
        key = tuple(row)
        if key not in groups or means[i] < means[groups[key]]:
            groups[key] = i
    indices = sorted(groups.values(), key=lambda i: (tuple(a[i]), means[i]))
    return (means[indices], a[indices])

from scipy.special import log_ndtr as _generic_design_variation_pin_arc_ps_standalone_V24__log_ndtr

import numpy as _scipy_special_compat__np

from scipy.special import ndtri as _scipy_special_compat__ndtri

from scipy.special import log_ndtr as _scipy_special_compat__log_ndtr

def _scipy_special_compat___ndtri_exp_fallback(y):
    """Solve log(Phi(x))=y without exponentiating extremely small tails."""
    values = _scipy_special_compat__np.asarray(y, dtype=float)
    out = _scipy_special_compat__np.full(values.shape, _scipy_special_compat__np.nan, dtype=float)
    out[_scipy_special_compat__np.isneginf(values)] = -_scipy_special_compat__np.inf
    out[values == 0] = _scipy_special_compat__np.inf
    left = _scipy_special_compat__np.isfinite(values) & (values < -_scipy_special_compat__np.log(2.0))
    ordinary = left & (values >= _scipy_special_compat__np.log(_scipy_special_compat__np.finfo(float).tiny))
    out[ordinary] = _scipy_special_compat__ndtri(_scipy_special_compat__np.exp(values[ordinary]))
    right = _scipy_special_compat__np.isfinite(values) & (values >= -_scipy_special_compat__np.log(2.0)) & (values < 0)
    out[right] = -_scipy_special_compat__ndtri(-_scipy_special_compat__np.expm1(values[right]))
    extreme = left & ~ordinary
    if _scipy_special_compat__np.any(extreme):
        target = values[extreme]
        x = -_scipy_special_compat__np.sqrt(-target) * _scipy_special_compat__np.sqrt(2.0)
        for _ in range(12):
            logcdf = _scipy_special_compat__log_ndtr(x)
            derivative = _scipy_special_compat__np.exp(-0.5 * x * x - 0.5 * _scipy_special_compat__np.log(2 * _scipy_special_compat__np.pi) - logcdf)
            step = (logcdf - target) / derivative
            x -= step
            if _scipy_special_compat__np.all(_scipy_special_compat__np.abs(step) <= 4 * _scipy_special_compat__np.finfo(float).eps * _scipy_special_compat__np.maximum(1.0, _scipy_special_compat__np.abs(x))):
                break
        out[extreme] = x
    return out.item() if out.ndim == 0 else out

_scipy_special_compat__ndtri_exp = _scipy_special_compat___ndtri_exp_fallback

from scipy.special import ndtr as _generic_design_variation_pin_arc_ps_standalone_V24__ndtr

from scipy.optimize import brentq as _generic_design_variation_pin_arc_ps_standalone_V24__brentq

import math as _generic_design_variation_pin_arc_ps_standalone_V24__math

class _generic_design_variation_pin_arc_ps_standalone_V24___BaseGaussianUnion:
    """Conditional-mixture (union-event) IS with exact likelihood weights.

    Choose event i with p_i/sum(p_i); sample the joint Gaussian conditional on
    that event. Each sample's likelihood weight is sum(p_i)/number_of_hits.
    This is an unbiased estimate at fixed thresholds; samples are shared during
    root finding. No empirical quantile or fitted PS correction is used.
    """

    def __init__(self, means, coefficients, samples=316000, seed=20260908):
        self.means, self.a = _generic_design_variation_pin_arc_ps_standalone_V24__reduce_dominated(means, coefficients)
        self.sd = _generic_design_variation_pin_arc_ps_standalone_V24__np.linalg.norm(self.a, axis=1)
        if _generic_design_variation_pin_arc_ps_standalone_V24__np.any(self.sd <= 0):
            raise ValueError('Zero-variance paths need deterministic handling; not supported by this model.')
        self.n = int(samples)
        self.seed = int(seed)
        self.k = len(self.means)
        self.corr = self.a @ self.a.T / _generic_design_variation_pin_arc_ps_standalone_V24__np.outer(self.sd, self.sd)
        self.corr = _generic_design_variation_pin_arc_ps_standalone_V24__np.clip((self.corr + self.corr.T) * 0.5, -1, 1)
        _generic_design_variation_pin_arc_ps_standalone_V24__np.fill_diagonal(self.corr, 1.0)
        self.base = None
        if self.k > 1:
            eig, vec = _generic_design_variation_pin_arc_ps_standalone_V24__np.linalg.eigh(self.corr)
            if eig.min() < -1e-09:
                raise ValueError('Non-PSD correlation matrix')
            factor = vec * _generic_design_variation_pin_arc_ps_standalone_V24__np.sqrt(_generic_design_variation_pin_arc_ps_standalone_V24__np.maximum(eig, 0))[None, :]
            rng = _generic_design_variation_pin_arc_ps_standalone_V24__np.random.default_rng(seed)
            self.base = rng.standard_normal((self.n, self.k)) @ factor.T
            self.choose = rng.random(self.n)
            self.tail_u = _generic_design_variation_pin_arc_ps_standalone_V24__np.maximum(rng.random(self.n), _generic_design_variation_pin_arc_ps_standalone_V24__np.finfo(float).tiny)

    def failure(self, threshold=0.0):
        t = (float(threshold) - self.means) / self.sd
        logp = _generic_design_variation_pin_arc_ps_standalone_V24__log_ndtr(t)
        p = _generic_design_variation_pin_arc_ps_standalone_V24__np.exp(logp)
        if self.k == 1:
            return {'probability': float(p[0]), 'standard_error': 0.0, 'method': 'analytic_normal', 'events': 1}
        total = float(p.sum())
        if total == 0:
            return {'probability': 0.0, 'standard_error': 0.0, 'method': 'conditional_union_is', 'events': self.k}
        cdf = _generic_design_variation_pin_arc_ps_standalone_V24__np.cumsum(p / total)
        cdf[-1] = 1.0
        j = _generic_design_variation_pin_arc_ps_standalone_V24__np.searchsorted(cdf, self.choose, side='right')
        conditional = _scipy_special_compat__ndtri_exp(logp[j] + _generic_design_variation_pin_arc_ps_standalone_V24__np.log(self.tail_u))
        delta = conditional - self.base[_generic_design_variation_pin_arc_ps_standalone_V24__np.arange(self.n), j]
        y = self.base + delta[:, None] * self.corr[j, :]
        hits = _generic_design_variation_pin_arc_ps_standalone_V24__np.count_nonzero(y <= t[None, :] + 1e-12, axis=1)
        if _generic_design_variation_pin_arc_ps_standalone_V24__np.any(hits < 1):
            raise ArithmeticError('Conditional proposal missed its selected event')
        weight = total / hits
        return {'probability': float(weight.mean()), 'standard_error': float(weight.std(ddof=1) / _generic_design_variation_pin_arc_ps_standalone_V24__math.sqrt(self.n)), 'method': 'conditional_union_is', 'events': self.k}

    def quantile(self, target_sigma):
        alpha = float(_generic_design_variation_pin_arc_ps_standalone_V24__ndtr(-target_sigma))
        if self.k == 1:
            q = float(self.means[0] - target_sigma * self.sd[0])
        else:
            lo = float(_generic_design_variation_pin_arc_ps_standalone_V24__np.min(self.means - (target_sigma + 5) * self.sd))
            hi = float(_generic_design_variation_pin_arc_ps_standalone_V24__np.min(self.means))

            def residual(q):
                return _generic_design_variation_pin_arc_ps_standalone_V24__math.log(max(self.failure(q)['probability'], 1e-300)) - _generic_design_variation_pin_arc_ps_standalone_V24__math.log(alpha)
            q = float(_generic_design_variation_pin_arc_ps_standalone_V24__brentq(residual, lo, hi, xtol=1e-10, rtol=1e-12))
        return (q, self.failure(q))

from scipy.stats import genpareto as _generic_design_variation_pin_arc_ps_standalone_V24__genpareto

class _generic_design_variation_pin_arc_ps_standalone_V24___ExperimentalGaussianUnion(_generic_design_variation_pin_arc_ps_standalone_V24___BaseGaussianUnion):

    def set_gpd_wns(self, values):
        """Supply ordinary MC WNS values for this exact path collection."""
        values = _generic_design_variation_pin_arc_ps_standalone_V24__np.asarray(values, dtype=float)
        if values.ndim != 1 or len(values) < 2 or not _generic_design_variation_pin_arc_ps_standalone_V24__np.all(_generic_design_variation_pin_arc_ps_standalone_V24__np.isfinite(values)):
            raise ValueError('GPD requires a finite one-dimensional ordinary MC WNS bank')
        self.gpd_wns = values

    def quantile(self, target_sigma):
        if self.k == 1:
            return super().quantile(target_sigma)
        if not hasattr(self, 'gpd_wns'):
            raise ValueError('No ordinary MC WNS supplied; use ALOE root finding')
        values = self.gpd_wns
        tail_fraction = 0.01
        threshold = float(_generic_design_variation_pin_arc_ps_standalone_V24__np.quantile(values, tail_fraction))
        excess = threshold - values[values < threshold]
        if len(excess) < 20:
            raise ValueError('Fewer than 20 MC tail observations; use ALOE root finding')
        shape, loc, scale = _generic_design_variation_pin_arc_ps_standalone_V24__genpareto.fit(excess, floc=0.0)
        alpha = float(_generic_design_variation_pin_arc_ps_standalone_V24__ndtr(-target_sigma))
        effective_fraction = float(len(excess) / len(values))
        depth = float(_generic_design_variation_pin_arc_ps_standalone_V24__genpareto.isf(alpha / effective_fraction, shape, loc=0.0, scale=scale))
        q = threshold - depth
        if not _generic_design_variation_pin_arc_ps_standalone_V24__math.isfinite(q):
            raise ArithmeticError('Invalid GPD extrapolation')
        check = self.failure(q)
        check.update(estimator='experimental_POT_GPD_fixed_1pct', shape=float(shape), scale=float(scale), threshold=threshold, fit_tail_samples=len(excess), fit_base_samples=len(values), fit_source='ordinary_mc_wns', fit_tail_fraction=tail_fraction, requested_failure_probability=alpha)
        return (float(q), check)

class _generic_design_variation_pin_arc_ps_standalone_V24__GaussianUnion(_generic_design_variation_pin_arc_ps_standalone_V24___ExperimentalGaussianUnion):

    def quantile(self, target_sigma):
        if self.k == 1:
            q, result = _generic_design_variation_pin_arc_ps_standalone_V24___BaseGaussianUnion.quantile(self, target_sigma)
            result['tail_policy'] = 'analytic_single_path'
            return (q, result)
        alpha = float(_generic_design_variation_pin_arc_ps_standalone_V24__ndtr(-target_sigma))
        candidate = {}
        accept = False
        try:
            q, estimate = _generic_design_variation_pin_arc_ps_standalone_V24___ExperimentalGaussianUnion.quantile(self, target_sigma)
            hold = _generic_design_variation_pin_arc_ps_standalone_V24___BaseGaussianUnion(self.means, self.a, self.n, self.seed + 7100001).failure(q)
            rel = abs(hold['probability'] / alpha - 1.0)
            se = _generic_design_variation_pin_arc_ps_standalone_V24__math.hypot(hold['standard_error'], estimate['standard_error'])
            accept = rel <= 0.005 and abs(hold['probability'] - alpha) <= max(5 * se, alpha * 1e-06)
            candidate = {'quantile': q, 'estimate': estimate, 'independent_validation': hold, 'relative_failure_error': rel, 'accepted': accept}
        except (ArithmeticError, ValueError, RuntimeError) as exc:
            candidate = {'accepted': False, 'error': str(exc)}
        if accept:
            result = dict(estimate)  # Snapshot: avoid candidate.estimate referring back to result.
            result['tail_policy'] = 'independently_validated_POT_GPD'
        else:
            q, result = _generic_design_variation_pin_arc_ps_standalone_V24___BaseGaussianUnion.quantile(self, target_sigma)
            result['tail_policy'] = 'validated_model_fallback_conditional_IS'
        result['experimental_candidate'] = candidate
        return (q, result)

from pathlib import Path as _generic_design_variation_pin_arc_ps_standalone_V24__Path

from dataclasses import dataclass as _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__dataclass

@_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__dataclass
class _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__Arc:
    key: str
    section: str
    instance: str
    input_pin: str
    output_pin: str
    mean: float
    sigma: float

@_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__dataclass
class _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__PinRow:
    point: str
    instance: str
    pin: str
    cell: str
    incr_mean: float
    incr_sigma: float

@_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__dataclass
class _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__TimingRow:
    """A cell-point row in report order; input rows represent fixed net delay."""
    point: str
    instance: str
    pin: str
    cell: str
    incr_mean: float
    incr_sigma: float
    is_input: bool

@_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__dataclass
class _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__PathData:
    path_id: str
    startpoint: str
    endpoint: str
    path_group: str
    arrival_mean: float
    required_mean: float
    crpr: float
    clock_uncertainty: float
    library_setup_time: float
    data_arcs: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__Arc]
    capture_arcs: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__Arc]
    input_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__PinRow]
    data_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__TimingRow]
    capture_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__TimingRow]
    launch_edge_time: float
    capture_edge_time: float
    last_common_pin: str

_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__FLOAT = '[-+]?\\d+(?:\\.\\d+)?(?:[eE][-+]?\\d+)?'

import re as _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__re

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__numbers(text: str) -> list[float]:
    return [float(x) for x in _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__re.findall(_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__FLOAT, text)]

_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__CELL_ROW_RE = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__re.compile(f'^\\s*(?P<point>.+?/(?P<pin>[^/\\s]+))\\s+\\((?P<cell>[^()]*)\\)(?P<tail>.*)$')

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__parse_timing_row(line: str) -> _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__TimingRow | None:
    """Parse a cell row and retain every cell point for cumulative timing."""
    m = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__CELL_ROW_RE.match(line.rstrip())
    if not m or '(net)' in line or line.lstrip().startswith('clock '):
        return None
    values = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__numbers(m.group('tail').split('&', 1)[0])
    if len(values) < 4:
        return None
    point = m.group('point').strip()
    instance, pin = point.rsplit('/', 1)
    return _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__TimingRow(point=point, instance=instance, pin=pin, cell=m.group('cell').strip(), incr_mean=values[2], incr_sigma=values[3], is_input=pin not in {'Y', 'Z', 'ZN', 'Q', 'QN', 'QB', 'O', 'CO'})

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__parse_pin_row(line: str) -> _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__PinRow | None:
    """���� cell point �У�ȡ cell �� Incr ����ĵ� 3/4 �����֡�"""
    m = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__CELL_ROW_RE.match(line.rstrip())
    if not m:
        return None
    if '(net)' in line or line.lstrip().startswith('clock '):
        return None
    tail = m.group('tail')
    before_amp = tail.split('&', 1)[0]
    values = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__numbers(before_amp)
    if len(values) < 4:
        return None
    point = m.group('point').strip()
    instance, pin = point.rsplit('/', 1)
    return _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__PinRow(point=point, instance=instance, pin=pin, cell=m.group('cell').strip(), incr_mean=values[2], incr_sigma=values[3])

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__summary_value(line: str) -> float | None:
    values = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__numbers(line)
    return values[0] if values else None

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__edge_value(line: str) -> float | None:
    """Read the first numeric value after the clock point descriptor."""
    close = line.find(')')
    values = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__numbers(line[close + 1:] if close >= 0 else line)
    return values[-3] if len(values) >= 3 else values[0] if values else None

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__header(block: str, name: str) -> str:
    m = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__re.search(f'(?m)^\\s{{2}}{_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__re.escape(name)}:\\s*(.+)$', block)
    return m.group(1).strip() if m else ''

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__parse_block(block: str, index: int) -> _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__PathData:
    data_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__PinRow] = []
    capture_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__PinRow] = []
    input_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__PinRow] = []
    data_timing_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__TimingRow] = []
    capture_timing_rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__TimingRow] = []
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
                arrival_mean = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__summary_value(stripped)
                section = 'capture'
            continue
        if stripped.startswith('data required time') and required_mean is None:
            required_mean = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__summary_value(stripped)
            continue
        if stripped.startswith('clock reconvergence pessimism'):
            vals = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__numbers(stripped)
            if vals:
                crpr = vals[0]
            continue
        if stripped.startswith('clock uncertainty'):
            vals = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__numbers(stripped)
            if vals:
                uncertainty = vals[0]
            continue
        if stripped.startswith('library setup time'):
            vals = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__numbers(stripped)
            if len(vals) >= 2:
                setup = vals[1]
            elif vals:
                setup = vals[0]
            continue
        if stripped.startswith('clock ') and 'edge)' in stripped:
            value = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__edge_value(line)
            if value is not None:
                if section == 'data' and (not launch_edge_seen):
                    launch_edge_time = value
                    launch_edge_seen = True
                elif section == 'capture' and (not capture_edge_seen):
                    capture_edge_time = value
                    capture_edge_seen = True
        timing_row = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__parse_timing_row(line)
        if timing_row is not None:
            if section == 'data':
                data_timing_rows.append(timing_row)
            else:
                capture_timing_rows.append(timing_row)
        row = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__parse_pin_row(line)
        if row is None:
            continue
        if section == 'data':
            data_rows.append(row)
        else:
            capture_rows.append(row)
    if arrival_mean is None or required_mean is None:
        raise ValueError(f'path{index}: δ�ҵ� data arrival/required time �����С�')

    def pair(rows: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__PinRow], section_name: str) -> list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__Arc]:
        arcs: list[_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__Arc] = []
        active_rows = rows
        for prev, cur in zip(active_rows, active_rows[1:]):
            if prev.instance != cur.instance:
                continue
            input_rows.append(prev)
            arcs.append(_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__Arc(key=f'{cur.instance}:{prev.pin}->{cur.pin}', section=section_name, instance=cur.instance, input_pin=prev.pin, output_pin=cur.pin, mean=cur.incr_mean, sigma=cur.incr_sigma))
        return arcs
    data_arcs = pair(data_rows, 'data')
    capture_arcs = pair(capture_rows, 'capture')
    if not data_arcs:
        raise ValueError(f'path{index}: û��ʶ�� data pin-to-pin arc��')
    return _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__PathData(path_id=f'path{index}', startpoint=_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__header(block, 'Startpoint'), endpoint=_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__header(block, 'Endpoint'), path_group=_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__header(block, 'Path Group'), arrival_mean=arrival_mean, required_mean=required_mean, crpr=crpr, clock_uncertainty=uncertainty, library_setup_time=setup, data_arcs=data_arcs, capture_arcs=capture_arcs, input_rows=input_rows, data_rows=data_timing_rows, capture_rows=capture_timing_rows, launch_edge_time=launch_edge_time, capture_edge_time=capture_edge_time, last_common_pin=_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__header(block, 'Last common pin'))

import re as _timing_report_parser_V18__re

def _timing_report_parser_V18__parse_block(block, index):
    p = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__parse_block(block, index)
    annotated = {'data': [], 'capture': []}
    sec = 'data'
    for line in block.splitlines():
        if line.strip().startswith('data arrival time') and sec == 'data':
            sec = 'capture'
            continue
        r = _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__parse_timing_row(line)
        if r is not None:
            m = _timing_report_parser_V18__re.search('\\s([rf])(?:\\s+[-+0-9.eE]+)?\\s*$', line)
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
                arcs.append(_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__Arc(key, sec, cur.instance, prev.pin, cur.pin, cur.incr_mean, cur.incr_sigma))
        if sec == 'data':
            p.data_arcs = arcs
        else:
            p.capture_arcs = arcs
    return p

from scipy.special import ndtri as _generic_design_variation_pin_arc_ps_standalone_V24__ndtri

def _generic_design_variation_pin_arc_ps_standalone_V24__eq_from_failure(failure):
    # PrimeShield reports Equivalent sigma no lower than -6 sigma.
    # Preserve +infinity for a numerically zero failure probability.
    if failure <= 0:
        return _generic_design_variation_pin_arc_ps_standalone_V24__math.inf
    if failure >= 1:
        return -6.0
    return max(-6.0, float(-_generic_design_variation_pin_arc_ps_standalone_V24__ndtri(failure)))

import json as _generic_design_variation_pin_arc_ps_standalone_V24__json

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__split_blocks(text: str) -> list[str]:
    starts = [m.start() for m in _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__re.finditer('(?m)^\\s{2}Startpoint:', text)]
    if not starts:
        raise ValueError('δ�ҵ� Startpoint:����������� report_timing �ı���')
    return [text[a:b] for a, b in zip(starts, starts[1:] + [len(text)])]

def _generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__endpoint_name(value: str) -> str:
    return value.split(' (', 1)[0].strip()

import hashlib as _generic_design_variation_pin_arc_ps_standalone_V24__hashlib

def _generic_design_variation_pin_arc_ps_standalone_V24__run(args):
    text = _generic_design_variation_pin_arc_ps_standalone_V24__Path(args.input).read_text()
    paths = [_timing_report_parser_V18__parse_block(b, i) for i, b in enumerate(_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__split_blocks(text), 1)]
    m, a, keys, audit = _generic_design_variation_pin_arc_ps_standalone_V24__linear_model(paths)
    rng = _generic_design_variation_pin_arc_ps_standalone_V24__np.random.default_rng(args.seed)
    z = rng.standard_normal((len(keys), args.samples))
    unique_a, inverse = _generic_design_variation_pin_arc_ps_standalone_V24__np.unique(a, axis=0, return_inverse=True)
    centered = unique_a @ z
    del z
    mc_design = _generic_design_variation_pin_arc_ps_standalone_V24__np.full(args.samples, _generic_design_variation_pin_arc_ps_standalone_V24__np.inf)
    for i in range(len(paths)):
        _generic_design_variation_pin_arc_ps_standalone_V24__np.minimum(mc_design, centered[inverse[i]] + m[i], out=mc_design)
    original_p = float(_generic_design_variation_pin_arc_ps_standalone_V24__np.mean(mc_design >= 0))
    design_model = _generic_design_variation_pin_arc_ps_standalone_V24__GaussianUnion(m, a, args.tail_samples, args.seed + 1000003)
    design_model.set_gpd_wns(mc_design)
    design_q, design_tail = design_model.quantile(args.sigma)
    design_hold = _generic_design_variation_pin_arc_ps_standalone_V24__GaussianUnion(m, a, args.tail_samples, args.seed + 2000003).failure(design_q)
    groups = {}
    for i, p in enumerate(paths):
        groups.setdefault(_generic_design_variation_pin_arc_ps_standalone_skip_zero_V16_pt2026_compat__endpoint_name(p.endpoint), []).append(i)
    shifts = _generic_design_variation_pin_arc_ps_standalone_V24__np.zeros(len(paths))
    endpoints = {}
    cache = {}
    adjusted_mc_min = _generic_design_variation_pin_arc_ps_standalone_V24__np.full(args.samples, _generic_design_variation_pin_arc_ps_standalone_V24__np.inf)
    target_failure = float(_generic_design_variation_pin_arc_ps_standalone_V24__ndtr(-args.sigma))
    target_rate = 1.0 - target_failure
    for endpoint, indices in groups.items():
        em, ea = _generic_design_variation_pin_arc_ps_standalone_V24__reduce_dominated(m[indices], a[indices])
        signature = tuple(_generic_design_variation_pin_arc_ps_standalone_V24__np.column_stack((em, ea)).ravel())
        values = _generic_design_variation_pin_arc_ps_standalone_V24__np.full(args.samples, _generic_design_variation_pin_arc_ps_standalone_V24__np.inf)
        for i in indices:
            _generic_design_variation_pin_arc_ps_standalone_V24__np.minimum(values, centered[inverse[i]] + m[i], out=values)
        if signature not in cache:
            mod = _generic_design_variation_pin_arc_ps_standalone_V24__GaussianUnion(em, ea, args.tail_samples, args.seed + 3000003)
            mod.set_gpd_wns(values)
            q, tail = mod.quantile(args.sigma)
            shift = max(0.0, -q)
            validate = _generic_design_variation_pin_arc_ps_standalone_V24__GaussianUnion(em + shift, ea, args.tail_samples, args.seed + 4000003).failure(0.0)
            cache[signature] = (q, tail, shift, validate)
        q, tail, shift, validate = cache[signature]
        shifts[indices] = shift
        empirical = float(_generic_design_variation_pin_arc_ps_standalone_V24__np.mean(values >= 0))
        adjusted_mc = float(_generic_design_variation_pin_arc_ps_standalone_V24__np.mean(values + shift >= 0))
        _generic_design_variation_pin_arc_ps_standalone_V24__np.minimum(adjusted_mc_min, values + shift, out=adjusted_mc_min)
        repaired = shift > 0
        failure = target_failure if repaired else validate['probability']
        endpoints[endpoint] = {'success_rate': empirical, 'equivalent_sigma': _generic_design_variation_pin_arc_ps_standalone_V24__eq_from_failure(1.0 - empirical), 'target_quantile': q, 'target_sigma_slack': -shift, 'right_shift_to_target': shift, 'adjusted_success_rate': 1.0 - failure, 'adjusted_equivalent_sigma': args.sigma if repaired else _generic_design_variation_pin_arc_ps_standalone_V24__eq_from_failure(failure), 'adjusted_value_basis': 'model_target_after_tail_solved_shift' if repaired else 'model_probability_no_shift', 'adjusted_success_rate_mc': adjusted_mc, 'tail_failure_validation': validate, 'validation_adjusted_sigma': _generic_design_variation_pin_arc_ps_standalone_V24__eq_from_failure(validate['probability']), 'target_quantile_is': tail}
    del centered
    adj_model = _generic_design_variation_pin_arc_ps_standalone_V24__GaussianUnion(m + shifts, a, args.tail_samples, args.seed + 5000003)
    adj = adj_model.failure(0.0)
    adj_hold = _generic_design_variation_pin_arc_ps_standalone_V24__GaussianUnion(m + shifts, a, args.tail_samples, args.seed + 6000003).failure(0.0)
    adjusted_mc = float(_generic_design_variation_pin_arc_ps_standalone_V24__np.mean(adjusted_mc_min >= 0))
    summary = {'version': 'V24', 'tail_guard': 'independent failure probability check; reject unstable extrapolation', 'implementation': 'exact coefficient reuse; bounded path-sample memory', 'gpd_fit_source': 'ordinary_mc_wns', 'gpd_base_samples': args.samples, 'gpd_tail_fraction': 0.01, 'samples': args.samples, 'tail_samples_per_query': args.tail_samples, 'target_sigma': args.sigma, 'target_failure_probability': target_failure, 'seed': args.seed, 'path_count': len(paths), 'endpoint_count': len(groups), 'arc_count': len(keys), 'unique_gaussian_paths': design_model.k, 'model': 'unbounded linear Gaussian; physical input/output-edge-aware pin-to-pin shared sources; text-report moments; fixed setup mean', 'endpoint_adjustments': endpoints, 'original_design': {'success_rate': original_p, 'equivalent_sigma': _generic_design_variation_pin_arc_ps_standalone_V24__eq_from_failure(1.0 - original_p), 'mean_slack': float(mc_design.mean()), 'sigma_slack': float(mc_design.std(ddof=1))}, 'adjusted_design': {'success_rate': 1.0 - adj['probability'], 'failure_probability': adj['probability'], 'equivalent_sigma': _generic_design_variation_pin_arc_ps_standalone_V24__eq_from_failure(adj['probability']), 'failure_probability_standard_error': adj['standard_error'], 'holdout_validation': adj_hold, 'success_rate_mc': adjusted_mc}, 'design_slack': design_q, 'design_slack_tail_estimate': design_tail, 'design_slack_holdout_validation': design_hold, 'total_row_slack': sum((r['target_sigma_slack'] for r in endpoints.values())), 'violation_num': sum((r['right_shift_to_target'] > 0 for r in endpoints.values())), 'parsing_audit': audit, 'input_sha256': _generic_design_variation_pin_arc_ps_standalone_V24__hashlib.sha256(_generic_design_variation_pin_arc_ps_standalone_V24__Path(args.input).read_bytes()).hexdigest(), 'notes': ['Endpoint adjusted columns denote the solved model target, not finite empirical success counts.', 'Total adjusted columns estimated from correlated rare-event union, not endpoint product.', 'Independent validation banks provided for tail/model checks; no PS report used.', 'GPD uses the worst 1% of N ordinary MC WNS values; M controls ALOE sample banks only.', 'Equivalent sigma is floored at -6 sigma to match the PrimeShield report lower bound.', 'No claim of exact PS internal model reconstruction.']}
    out = _generic_design_variation_pin_arc_ps_standalone_V24__Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stem = _generic_design_variation_pin_arc_ps_standalone_V24__Path(args.input).stem + '_V24'
    (out / (stem + '_summary.json')).write_text(_generic_design_variation_pin_arc_ps_standalone_V24__json.dumps(summary, indent=2, ensure_ascii=False))
    width = max(8, max(map(len, endpoints)))
    lines = [f'V24 Num of MC Samples: {args.samples}', f'Tail conditional-IS samples per query: {args.tail_samples}', f'Target Sigma: {args.sigma:.9f}', f"{'Endpoint':<{width}} Success_rate  Equivalent_sigma Slack(ns) Adjusted_success_rate Adjusted_Eq_sigma"]
    for ep, r in endpoints.items():
        lines.append(f"{ep:<{width}} {r['success_rate']:.9f} {r['equivalent_sigma']:.9f} {r['target_sigma_slack']:.9f} {r['adjusted_success_rate']:.12f} {r['adjusted_equivalent_sigma']:.9f}")
    lines.append(f"{'Total':<{width}} {original_p:.9f} {summary['original_design']['equivalent_sigma']:.9f} {summary['total_row_slack']:.9f} {1 - adj['probability']:.12f} {_generic_design_variation_pin_arc_ps_standalone_V24__eq_from_failure(adj['probability']):.9f}")
    lines += [f'Design Slack = {design_q:.9f} ns', f"Violation Num. = {summary['violation_num']}", f"Adjusted joint failure probability = {adj['probability']:.12e} +/- {adj['standard_error']:.3e} (1 SE)", f'Endpoint adjusted columns: target-based model result; see JSON for independent validation and empirical MC.', f'Total adjusted columns: conditional-union importance sampling estimate.']
    (out / (stem + '_report.txt')).write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return summary

import argparse as _generic_design_variation_pin_arc_ps_standalone_V24__argparse

def _generic_design_variation_pin_arc_ps_standalone_V24__main():
    ap = _generic_design_variation_pin_arc_ps_standalone_V24__argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input')
    ap.add_argument('--samples', type=int, default=316000)
    ap.add_argument('--tail-samples', type=int, default=None)
    ap.add_argument('--sigma', type=float, default=6.0)
    ap.add_argument('--seed', type=int, default=20260908)
    ap.add_argument('--workers', type=int, default=1, help='Compatibility option; NumPy/BLAS controls actual threads.')
    ap.add_argument('--output_dir', required=True)
    args = ap.parse_args()
    args.tail_samples = args.tail_samples or args.samples
    if args.samples < 2 or args.tail_samples < 2 or (not 0 < args.sigma <= 8):
        ap.error('samples >= 2 and 0 < sigma <= 8 required')
    _generic_design_variation_pin_arc_ps_standalone_V24__run(args)

if __name__ == '__main__':
    _generic_design_variation_pin_arc_ps_standalone_V24__main()
