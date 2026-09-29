"""MIP: Routenwahl je Sendung (genau eine Kandidatenroute) + Öffnungsentscheidung je potenzieller Bahn/Schiff-
Verbindung, gekoppelt (eine Route, die Bahn auf einer geschlossenen Verbindung nutzt, ist unzulässig). Für die
"Immer Lkw"-Baseline wird einfach mit einer auf reine Lkw-Routen gefilterten Routenliste gelöst - identisches
Routing-MIP, nur ohne Bahn-Kandidaten und ohne Design-Variablen (strukturell fair: dieselbe Routing-Logik, nicht
künstlich benachteiligt)."""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


@dataclass(frozen=True)
class Solution:
    objective: float
    fixed_cost: float
    variable_cost: float
    co2: float
    chosen: tuple          # Routenindex je Sendung
    open_legs: frozenset    # Leg-Indizes mit eröffneter Bahn/Schiff-Verbindung
    rail_share_unit_km: float   # Anteil der Einheit-km, die per Bahn/Schiff zurückgelegt werden


def _unit_km(route, legs):
    total = 0.0
    for li, mode in route.legs:
        total += legs[li].dist
    return total


def solve(net, legs, routes, by_shipment, co2_price=0.0, time_limit=30.0):
    """Volles MIP: Routenwahl + Bahn-Design, optional mit CO2-Preis (EUR/kg) im Zielwert."""
    n_r, n_e = len(routes), len(legs)
    nv = n_r + n_e

    def y_col(e):
        return n_r + e

    cost = np.zeros(nv)
    for r_i, r in enumerate(routes):
        cost[r_i] = r.cost + co2_price * r.co2
    for e in range(n_e):
        cost[y_col(e)] = legs[e].fixed_cost

    rows, cols, vals, lo, hi = [], [], [], [], []
    row = 0
    for s in range(net.n_shipments):
        for r_i in by_shipment[s]:
            rows.append(row); cols.append(r_i); vals.append(1.0)
        lo.append(1.0); hi.append(1.0); row += 1
    for r_i, r in enumerate(routes):
        for e in r.uses_rail:
            rows.append(row); cols.append(r_i); vals.append(1.0)
            rows.append(row); cols.append(y_col(e)); vals.append(-1.0)
            lo.append(-np.inf); hi.append(0.0); row += 1

    a = coo_matrix((vals, (rows, cols)), shape=(row, nv)).tocsr()
    eq_rows = [k for k in range(row) if lo[k] == hi[k]]
    ub_rows = [k for k in range(row) if lo[k] != hi[k]]
    constraints = [LinearConstraint(a[eq_rows], np.array(lo)[eq_rows], np.array(hi)[eq_rows])]
    if ub_rows:
        constraints.append(LinearConstraint(a[ub_rows], -np.inf, np.array(hi)[ub_rows]))

    integrality = np.ones(nv)
    res = milp(cost, constraints=constraints, integrality=integrality, bounds=Bounds(0, 1),
               options={"time_limit": time_limit, "mip_rel_gap": 0.0})
    if res.status != 0 or res.x is None:
        raise RuntimeError(f"MIP nicht optimal gelöst: {getattr(res, 'message', res.status)}")
    x = res.x
    chosen = tuple(next(r_i for r_i in by_shipment[s] if x[r_i] > 0.5) for s in range(net.n_shipments))
    open_legs = frozenset(e for e in range(n_e) if x[y_col(e)] > 0.5)
    fixed_cost = float(sum(legs[e].fixed_cost for e in open_legs))
    variable_cost = float(sum(routes[r].cost for r in chosen))
    co2 = float(sum(routes[r].co2 for r in chosen))
    rail_km = sum(_unit_km(routes[r], legs) for r in chosen if routes[r].uses_rail)
    total_km = sum(_unit_km(routes[r], legs) for r in chosen)
    rail_share = rail_km / total_km if total_km else 0.0
    return Solution(fixed_cost + variable_cost + co2_price * co2, fixed_cost, variable_cost, co2, chosen, open_legs, rail_share)


def solve_truck_only(net, legs, routes, by_shipment, time_limit=30.0):
    """"Immer Lkw"-Baseline: nur reine Lkw-Routen zulässig, kein Bahn-Design."""
    truck_routes = [r for r in routes if not r.uses_rail]
    truck_by_shipment = [[] for _ in range(net.n_shipments)]
    index_map = {}
    for new_i, r in enumerate(truck_routes):
        index_map[new_i] = r
        truck_by_shipment[r.shipment].append(new_i)
    return solve(net, legs, truck_routes, truck_by_shipment, co2_price=0.0, time_limit=time_limit)
