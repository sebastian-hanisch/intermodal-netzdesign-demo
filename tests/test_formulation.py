import sys
from itertools import product
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from imn_formulation import solve, solve_truck_only
from imn_routes import Params, candidate_routes, routes_by_shipment
from imn_scenario import generate

PARAMS = Params(truck_cost_per_km=1.0, rail_cost_per_km=0.5, truck_speed=60, rail_speed=35, rail_headway=6, rail_fixed_per_km=10)


def _brute_force(net, legs, routes, by_shipment, co2_price=0.0):
    best = None
    for combo in product(*by_shipment):
        open_legs = set()
        for r_i in combo:
            open_legs |= set(routes[r_i].uses_rail)
        fixed = sum(legs[e].fixed_cost for e in open_legs)
        var = sum(routes[r_i].cost for r_i in combo)
        co2 = sum(routes[r_i].co2 for r_i in combo)
        total = fixed + var + co2_price * co2
        if best is None or total < best:
            best = total
    return best


def test_solve_matches_brute_force_tiny_network():
    net = generate(4, 3, 15, 20, 100, 7)
    legs, routes = candidate_routes(net, PARAMS)
    by_s = routes_by_shipment(net, routes)
    brute = _brute_force(net, legs, routes, by_s)
    sol = solve(net, legs, routes, by_s)
    assert sol.objective == pytest.approx(brute, abs=1e-6)


def test_solve_matches_brute_force_second_tiny_network():
    net = generate(5, 4, 12, 40, 100, 3)
    legs, routes = candidate_routes(net, PARAMS)
    by_s = routes_by_shipment(net, routes)
    brute = _brute_force(net, legs, routes, by_s)
    sol = solve(net, legs, routes, by_s)
    assert sol.objective == pytest.approx(brute, abs=1e-6)


def test_solve_with_co2_price_matches_brute_force():
    net = generate(4, 3, 15, 20, 100, 7)
    legs, routes = candidate_routes(net, PARAMS)
    by_s = routes_by_shipment(net, routes)
    brute = _brute_force(net, legs, routes, by_s, co2_price=5.0)
    sol = solve(net, legs, routes, by_s, co2_price=5.0)
    assert sol.objective == pytest.approx(brute, abs=1e-6)


def test_solution_open_legs_match_chosen_routes():
    net = generate(6, 8, 20, 30, 100, 1)
    legs, routes = candidate_routes(net, PARAMS)
    by_s = routes_by_shipment(net, routes)
    sol = solve(net, legs, routes, by_s)
    expected_open = set()
    for r in sol.chosen:
        expected_open |= set(routes[r].uses_rail)
    assert sol.open_legs == frozenset(expected_open)


def test_truck_only_never_uses_rail():
    net = generate(6, 8, 20, 30, 100, 1)
    legs, routes = candidate_routes(net, PARAMS)
    by_s = routes_by_shipment(net, routes)
    sol = solve_truck_only(net, legs, routes, by_s)
    assert sol.rail_share_unit_km == 0.0
    assert sol.open_legs == frozenset()


def test_truck_only_is_never_cheaper_than_full_mip():
    """Das volle MIP darf nie schlechter sein als die Lkw-only-Einschränkung, da deren Lösungsraum eine Teilmenge ist."""
    net = generate(6, 8, 20, 30, 100, 1)
    legs, routes = candidate_routes(net, PARAMS)
    by_s = routes_by_shipment(net, routes)
    full = solve(net, legs, routes, by_s)
    truck = solve_truck_only(net, legs, routes, by_s)
    assert full.objective <= truck.objective + 1e-6
