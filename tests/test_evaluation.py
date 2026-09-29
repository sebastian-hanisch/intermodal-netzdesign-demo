import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import imn_constants as C
from imn_evaluation import best_rule_threshold, build_network, co2_price_sweep, compare, cost_ratio_sweep, deadline_mult_sweep, qty_scale_sweep


def _net():
    return build_network(C.DEFAULT_NODES, C.DEFAULT_SHIPMENTS, C.DEFAULT_DEADLINE_BASE, C.DEFAULT_DEADLINE_SPREAD, C.DEFAULT_QTY_SCALE, C.DEFAULT_SEED)


def test_compare_savings_nonnegative():
    net = _net()
    c = compare(net, C.BASE_PARAMS)
    assert c.savings_vs_truck_pct >= -1e-6
    assert c.rule_gap_pct >= -1e-6


def test_cost_ratio_sweep_rail_share_decreases_with_higher_ratio():
    net = _net()
    rows = cost_ratio_sweep(net, C.BASE_PARAMS, C.RATIO_SWEEP)
    shares = [r["rail_share"] for r in rows]
    assert shares[0] >= shares[-1]  # niedrigstes Kostenverhältnis (günstigste Bahn) hat mindestens so viel Bahn-Anteil wie das höchste


def test_deadline_mult_sweep_tightest_has_zero_rail():
    net = _net()
    rows = deadline_mult_sweep(net, C.BASE_PARAMS, C.DEADLINE_MULT_SWEEP)
    assert rows[0]["rail_share"] == 0.0


def test_qty_scale_sweep_more_volume_never_reduces_rail_share_at_endpoints():
    rows = qty_scale_sweep(C.DEFAULT_NODES, C.DEFAULT_SHIPMENTS, C.DEFAULT_DEADLINE_BASE, C.DEFAULT_DEADLINE_SPREAD, C.DEFAULT_SEED, C.BASE_PARAMS, C.QTY_SCALE_SWEEP)
    assert rows[-1]["rail_share"] >= rows[0]["rail_share"]


def test_co2_price_sweep_higher_price_never_increases_co2():
    net = _net()
    rows = co2_price_sweep(net, C.BASE_PARAMS, C.DEFAULT_DEADLINE_MULT, C.CO2_PRICE_SWEEP)
    for a, b in zip(rows, rows[1:]):
        assert b["co2"] <= a["co2"] + 1e-6


def test_best_rule_threshold_is_at_least_as_good_as_any_single_threshold():
    net = _net()
    thr, best = best_rule_threshold(net, C.BASE_PARAMS, C.DEFAULT_DEADLINE_MULT, C.RULE_THRESHOLD_SWEEP)
    assert thr in C.RULE_THRESHOLD_SWEEP
    from imn_routes import candidate_routes, routes_by_shipment
    from imn_rules import solve_distance_rule
    legs, routes = candidate_routes(net, C.BASE_PARAMS, deadline_mult=C.DEFAULT_DEADLINE_MULT)
    by_s = routes_by_shipment(net, routes)
    for other_thr in C.RULE_THRESHOLD_SWEEP:
        other = solve_distance_rule(net, legs, routes, by_s, other_thr)
        assert best.objective <= other.objective + 1e-6
