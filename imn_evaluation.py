"""Der Methodenvergleich (Immer Lkw / Naive Distanzregel / Exakt) und die drei Kipppunkt-Sweeps
(Kostenverhältnis, Zeitfenster-Enge, Sendungsvolumen) plus der CO2-Preis-Pareto-Abschnitt."""

from dataclasses import dataclass, replace

from imn_formulation import solve, solve_truck_only
from imn_routes import build_legs, candidate_routes, routes_by_shipment
from imn_rules import solve_distance_rule
from imn_scenario import generate


@dataclass(frozen=True)
class Comparison:
    net: object
    legs: tuple
    routes: tuple
    mip: object
    truck_only: object
    rule: object
    rule_threshold: float

    @property
    def savings_vs_truck_pct(self):
        return 100.0 * (self.truck_only.objective - self.mip.objective) / self.truck_only.objective

    @property
    def rule_gap_pct(self):
        return 100.0 * (self.rule.objective - self.mip.objective) / self.mip.objective


def build_network(n_nodes, n_shipments, deadline_base, deadline_spread_pct, qty_scale_pct, seed):
    return generate(n_nodes, n_shipments, deadline_base, deadline_spread_pct, qty_scale_pct, seed)


def compare(net, params, deadline_mult=1.0, rule_threshold_km=100.0, co2_price=0.0):
    legs, routes = candidate_routes(net, params, deadline_mult=deadline_mult)
    by_s = routes_by_shipment(net, routes)
    mip = solve(net, legs, routes, by_s, co2_price=co2_price)
    truck = solve_truck_only(net, legs, routes, by_s)
    rule = solve_distance_rule(net, legs, routes, by_s, rule_threshold_km)
    return Comparison(net, legs, routes, mip, truck, rule, rule_threshold_km)


def best_rule_threshold(net, params, deadline_mult, thresholds):
    """Der Schwellenwert, der die Naive-Distanzregel am günstigsten macht (fairste Darstellung: der Regel ihre beste Chance geben)."""
    legs, routes = candidate_routes(net, params, deadline_mult=deadline_mult)
    by_s = routes_by_shipment(net, routes)
    best = None
    for thr in thresholds:
        r = solve_distance_rule(net, legs, routes, by_s, thr)
        if best is None or r.objective < best[1].objective:
            best = (thr, r)
    return best


def cost_ratio_sweep(net, base_params, ratios):
    rows = []
    for ratio in ratios:
        p = replace(base_params, rail_cost_per_km=ratio * base_params.truck_cost_per_km)
        legs, routes = candidate_routes(net, p)
        by_s = routes_by_shipment(net, routes)
        mip = solve(net, legs, routes, by_s)
        truck = solve_truck_only(net, legs, routes, by_s)
        savings = 100.0 * (truck.objective - mip.objective) / truck.objective
        rows.append({"ratio": ratio, "rail_share": mip.rail_share_unit_km, "savings_pct": savings})
    return rows


def deadline_mult_sweep(net, params, mults):
    rows = []
    for mult in mults:
        legs, routes = candidate_routes(net, params, deadline_mult=mult)
        by_s = routes_by_shipment(net, routes)
        mip = solve(net, legs, routes, by_s)
        rows.append({"mult": mult, "rail_share": mip.rail_share_unit_km, "cost": mip.objective})
    return rows


def qty_scale_sweep(n_nodes, n_shipments, deadline_base, deadline_spread_pct, seed, params, scales):
    rows = []
    for scale in scales:
        net = generate(n_nodes, n_shipments, deadline_base, deadline_spread_pct, scale, seed)
        legs, routes = candidate_routes(net, params)
        by_s = routes_by_shipment(net, routes)
        mip = solve(net, legs, routes, by_s)
        rows.append({"scale": scale, "rail_share": mip.rail_share_unit_km, "cost": mip.objective})
    return rows


def co2_price_sweep(net, params, deadline_mult, prices):
    legs, routes = candidate_routes(net, params, deadline_mult=deadline_mult)
    by_s = routes_by_shipment(net, routes)
    rows = []
    for price in prices:
        mip = solve(net, legs, routes, by_s, co2_price=price)
        rows.append({"price": price, "rail_share": mip.rail_share_unit_km, "cost": mip.fixed_cost + mip.variable_cost, "co2": mip.co2})
    return rows
