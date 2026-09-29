"""Jede Zahl im README (und in den Preset-Hilfetexten) ist hier belegt — aus dem echten Code neu berechnet."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dataclasses import replace

import imn_constants as C
from imn_evaluation import build_network, compare


def _net():
    return build_network(C.DEFAULT_NODES, C.DEFAULT_SHIPMENTS, C.DEFAULT_DEADLINE_BASE, C.DEFAULT_DEADLINE_SPREAD, 100, C.DEFAULT_SEED)


def test_standard_preset():
    net = _net()
    c = compare(net, C.BASE_PARAMS, rule_threshold_km=180)
    assert c.mip.objective == pytest.approx(9161.952806855075, abs=1e-6)
    assert c.truck_only.objective == pytest.approx(9899.62724207329, abs=1e-6)
    assert c.savings_vs_truck_pct == pytest.approx(7.451537489039053, abs=1e-6)
    assert c.rule_gap_pct == pytest.approx(8.051497871352032, abs=1e-6)
    assert c.mip.rail_share_unit_km == pytest.approx(0.8202911436422745, abs=1e-6)


def test_rule_threshold_sensitivity():
    net = _net()
    good = compare(net, C.BASE_PARAMS, rule_threshold_km=180)
    bad = compare(net, C.BASE_PARAMS, rule_threshold_km=20)
    assert good.rule_gap_pct == pytest.approx(8.051497871352032, abs=1e-6)
    assert bad.rule_gap_pct == pytest.approx(82.65775880998972, abs=1e-6)
    assert bad.rule_gap_pct > good.rule_gap_pct * 5   # deutlich empfindlicher als "moderat"


def test_guenstige_bahn_preset():
    net = _net()
    params = replace(C.BASE_PARAMS, rail_cost_per_km=0.3)
    c = compare(net, params, rule_threshold_km=180)
    assert c.savings_vs_truck_pct == pytest.approx(21.65113521927255, abs=1e-6)
    assert c.mip.rail_share_unit_km == pytest.approx(0.9095511760494768, abs=1e-6)


def test_enge_zeitfenster_preset():
    net = _net()
    c = compare(net, C.BASE_PARAMS, deadline_mult=0.5, rule_threshold_km=180)
    assert c.mip.rail_share_unit_km == pytest.approx(0.547856779816315, abs=1e-6)
    assert c.mip.objective == pytest.approx(9288.948334683626, abs=1e-6)
    assert c.truck_only.objective == pytest.approx(9899.62724207329, abs=1e-6)


def test_co2_preis_preset():
    net = _net()
    c0 = compare(net, C.BASE_PARAMS, co2_price=0.0, rule_threshold_km=180)
    c10 = compare(net, C.BASE_PARAMS, co2_price=10.0, rule_threshold_km=180)
    cost0 = c0.mip.fixed_cost + c0.mip.variable_cost
    cost10 = c10.mip.fixed_cost + c10.mip.variable_cost
    assert c0.mip.rail_share_unit_km == pytest.approx(0.8202911436422745, abs=1e-6)
    assert c10.mip.rail_share_unit_km == pytest.approx(0.9595637953639015, abs=1e-6)
    assert 100 * (cost10 - cost0) / cost0 == pytest.approx(6.279959858074485, abs=1e-6)
    assert 100 * (c0.mip.co2 - c10.mip.co2) / c0.mip.co2 == pytest.approx(26.262020249161182, abs=1e-6)
