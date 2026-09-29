import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from imn_formulation import solve
from imn_routes import Params, TRUCK, candidate_routes, routes_by_shipment
from imn_rules import solve_distance_rule
from imn_scenario import generate

PARAMS = Params(truck_cost_per_km=1.0, rail_cost_per_km=0.5, truck_speed=60, rail_speed=40, rail_headway=8, rail_fixed_per_km=15)


def test_distance_rule_never_beats_the_optimum():
    net = generate(6, 8, 20, 30, 100, 1)
    legs, routes = candidate_routes(net, PARAMS)
    by_s = routes_by_shipment(net, routes)
    sol = solve(net, legs, routes, by_s)
    for thr in (20, 100, 250):
        rule = solve_distance_rule(net, legs, routes, by_s, thr)
        assert rule.objective >= sol.objective - 1e-6


def test_distance_rule_with_huge_threshold_uses_only_truck():
    net = generate(6, 8, 20, 30, 100, 1)
    legs, routes = candidate_routes(net, PARAMS)
    by_s = routes_by_shipment(net, routes)
    rule = solve_distance_rule(net, legs, routes, by_s, 10_000)
    assert rule.rail_share_unit_km == 0.0


def test_distance_rule_picks_cheapest_route_among_those_following_the_rule():
    net = generate(6, 8, 20, 30, 100, 1)
    legs, routes = candidate_routes(net, PARAMS)
    by_s = routes_by_shipment(net, routes)
    threshold = 100
    rule = solve_distance_rule(net, legs, routes, by_s, threshold)
    for s_i, r_i in enumerate(rule.chosen):
        following = [routes[cand] for cand in by_s[s_i]
                     if all((legs[li].dist >= threshold) == (m != TRUCK) for li, m in routes[cand].legs)]
        if following:
            assert routes[r_i].cost == pytest.approx(min(r.cost for r in following))
