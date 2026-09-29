"""Naive Distanzregel: "Bahn/Schiff, wenn die Teilstrecke länger als X km ist, sonst Lkw" — dann je Sendung die
günstigste zulässige Route unter dieser Regel wählen (nicht die günstigste über alle Modi, die Regel legt den
Modus je Teilstrecke fest, nicht die Routenwahl selbst)."""

from dataclasses import dataclass

from imn_routes import RAIL, TRUCK


@dataclass(frozen=True)
class RuleSolution:
    objective: float
    fixed_cost: float
    variable_cost: float
    chosen: tuple
    open_legs: frozenset
    rail_share_unit_km: float


def _rule_mode(dist, threshold_km):
    return RAIL if dist >= threshold_km else TRUCK


def solve_distance_rule(net, legs, routes, by_shipment, threshold_km):
    """Unter allen Kandidatenrouten, deren Modus je Teilstrecke exakt der Regel entspricht, die billigste je
    Sendung (ohne Fixkosten - die werden erst am Ende für die tatsächlich genutzten Bahn-Kanten addiert)."""
    chosen = []
    for s in range(net.n_shipments):
        best = None
        for r_i in by_shipment[s]:
            route = routes[r_i]
            if all(m == _rule_mode(legs[li].dist, threshold_km) for li, m in route.legs):
                if best is None or route.cost < routes[best].cost:
                    best = r_i
        if best is None:
            # keine Route folgt der Regel UND ist zeitlich zulässig: billigste zulässige Route nehmen (Ausweichfall)
            best = min(by_shipment[s], key=lambda r_i: routes[r_i].cost)
        chosen.append(best)
    open_legs = frozenset(e for r_i in chosen for e in routes[r_i].uses_rail)
    fixed_cost = sum(legs[e].fixed_cost for e in open_legs)
    variable_cost = sum(routes[r_i].cost for r_i in chosen)

    def _unit_km(route):
        return sum(legs[li].dist for li, _m in route.legs)

    rail_km = sum(_unit_km(routes[r_i]) for r_i in chosen if routes[r_i].uses_rail)
    total_km = sum(_unit_km(routes[r_i]) for r_i in chosen)
    rail_share = rail_km / total_km if total_km else 0.0
    return RuleSolution(fixed_cost + variable_cost, fixed_cost, variable_cost, tuple(chosen), open_legs, rail_share)
