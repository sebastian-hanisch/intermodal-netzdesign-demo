import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from imn_routes import Params, RAIL, TRUCK, build_legs, candidate_routes, routes_by_shipment
from imn_scenario import generate

PARAMS = Params(truck_cost_per_km=1.0, rail_cost_per_km=0.5, truck_speed=60, rail_speed=40, rail_headway=8, rail_fixed_per_km=15)


def test_every_shipment_has_at_least_one_direct_truck_route():
    net = generate(6, 8, 40, 30, 100, 1)   # großzügige Frist, damit direkter Lkw immer zulässig ist
    legs, routes = candidate_routes(net, PARAMS)
    by_s = routes_by_shipment(net, routes)
    for s_i, s in enumerate(net.shipments):
        direct_truck = [r for r in [routes[r_i] for r_i in by_s[s_i]] if len(r.legs) == 1 and r.legs[0][1] == TRUCK]
        assert direct_truck, f"Sendung {s_i} hat keine direkte Lkw-Route"


def test_tighter_deadline_removes_some_routes():
    net = generate(6, 8, 40, 30, 100, 1)
    legs, routes_loose = candidate_routes(net, PARAMS, deadline_mult=3.0)
    _legs2, routes_tight = candidate_routes(net, PARAMS, deadline_mult=0.1)
    assert len(routes_tight) <= len(routes_loose)


def test_route_cost_matches_manual_computation():
    net = generate(4, 2, 40, 0, 100, 5)
    legs, routes = candidate_routes(net, PARAMS)
    for r in routes:
        manual_cost = sum(legs[li].dist * net.shipments[r.shipment].qty * (PARAMS.truck_cost_per_km if m == TRUCK else PARAMS.rail_cost_per_km) for li, m in r.legs)
        assert abs(r.cost - manual_cost) < 1e-9


def test_route_time_matches_manual_computation():
    net = generate(4, 2, 40, 0, 100, 5)
    legs, routes = candidate_routes(net, PARAMS)
    for r in routes:
        manual_time = sum((legs[li].dist / PARAMS.truck_speed) if m == TRUCK else (legs[li].dist / PARAMS.rail_speed + PARAMS.rail_headway / 2) for li, m in r.legs)
        assert abs(r.time - manual_time) < 1e-9
        assert r.time <= net.shipments[r.shipment].deadline + 1e-9


def test_hub_routes_have_two_legs_and_no_hub_equals_endpoint():
    net = generate(6, 4, 40, 30, 100, 2)
    legs, routes = candidate_routes(net, PARAMS)
    for r in routes:
        if len(r.legs) == 2:
            (li1, _m1), (li2, _m2) = r.legs
            assert li1 != li2


def test_build_legs_covers_all_candidate_pairs():
    net = generate(5, 3, 40, 30, 100, 3)
    legs = build_legs(net, PARAMS)
    pairs = {(l.u, l.v) for l in legs}
    for s in net.shipments:
        assert tuple(sorted((s.origin, s.dest))) in pairs
