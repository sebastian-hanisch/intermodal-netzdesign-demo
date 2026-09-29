"""Kandidatenrouten je Sendung: direkt oder über einen Umschlagpunkt (höchstens ein Hop, wie `linehaul-demo`s
Vereinfachung), auf jeder Teilstrecke unabhängig Lkw oder Bahn/Schiff. Zeitfenster filtern unzulässige Routen
vorab (eine Route, die die Frist reißt, ist keine Kandidatin) — das ist reine Machbarkeit, keine Design-
Entscheidung, deshalb als Vorfilterung zulässig; OB eine Bahn-Teilstrecke überhaupt eröffnet wird, bleibt dagegen
eine echte MIP-Entscheidung (Kopplung in `imn_formulation.py`)."""

from dataclasses import dataclass

from imn_scenario import distance

TRUCK, RAIL = "truck", "rail"
MODES = (TRUCK, RAIL)


@dataclass(frozen=True)
class Params:
    truck_cost_per_km: float      # pro Einheit und km
    rail_cost_per_km: float       # pro Einheit und km (rail_cost_per_km / truck_cost_per_km = "Kostenverhältnis")
    truck_speed: float            # km/h
    rail_speed: float             # km/h
    rail_headway: float           # Stunden zwischen zwei festen Abfahrten (mittlere Wartezeit = headway/2)
    rail_fixed_per_km: float      # Fixkosten je km einer eröffneten Bahn/Schiff-Verbindung
    co2_per_unit_km_truck: float = 0.09    # kg CO2 je Einheit-km (Standardwerte, siehe README)
    co2_per_unit_km_rail: float = 0.03


@dataclass(frozen=True)
class Leg:
    u: int
    v: int
    dist: float
    fixed_cost: float


def build_legs(net, params):
    """Eine potenzielle Bahn/Schiff-Verbindung je ungeordnetem Knotenpaar, das auf mindestens einer Kandidatenroute vorkommt."""
    pairs = set()
    for s in net.shipments:
        pairs.add(tuple(sorted((s.origin, s.dest))))
    for s in net.shipments:
        for h in range(net.n):
            if h in (s.origin, s.dest):
                continue
            pairs.add(tuple(sorted((s.origin, h))))
            pairs.add(tuple(sorted((h, s.dest))))
    legs = []
    for u, v in sorted(pairs):
        d = distance(net.pos[u], net.pos[v])
        legs.append(Leg(u, v, d, params.rail_fixed_per_km * d))
    return tuple(legs)


def _leg_index(legs):
    return {(leg.u, leg.v): i for i, leg in enumerate(legs)}


def _leg_time(dist, mode, params):
    if mode == TRUCK:
        return dist / params.truck_speed
    return dist / params.rail_speed + params.rail_headway / 2


def _leg_cost(dist, mode, qty, params):
    rate = params.truck_cost_per_km if mode == TRUCK else params.rail_cost_per_km
    return dist * qty * rate


def _leg_co2(dist, mode, qty, params):
    rate = params.co2_per_unit_km_truck if mode == TRUCK else params.co2_per_unit_km_rail
    return dist * qty * rate


@dataclass(frozen=True)
class RouteCandidate:
    shipment: int
    legs: tuple            # ((leg_index, mode), ...) - 1 oder 2 Einträge
    time: float
    cost: float
    co2: float
    uses_rail: tuple       # leg_index-Tupel, auf denen diese Route Bahn/Schiff nutzt


def candidate_routes(net, params, legs=None, deadline_mult=1.0):
    """Alle zeitlich zulässigen Kandidatenrouten je Sendung. `deadline_mult` skaliert die Frist (Regler
    "Zeitfenster-Enge"), ohne das Netz neu zu erzeugen."""
    legs = legs if legs is not None else build_legs(net, params)
    idx = _leg_index(legs)
    out = []
    for s_i, s in enumerate(net.shipments):
        deadline = s.deadline * deadline_mult
        # direkt
        for mode in MODES:
            li = idx[tuple(sorted((s.origin, s.dest)))]
            d = legs[li].dist
            t = _leg_time(d, mode, params)
            if t <= deadline:
                out.append(RouteCandidate(s_i, ((li, mode),), t, _leg_cost(d, mode, s.qty, params),
                                          _leg_co2(d, mode, s.qty, params), (li,) if mode == RAIL else ()))
        # über einen Hub
        for h in range(net.n):
            if h in (s.origin, s.dest):
                continue
            li1 = idx[tuple(sorted((s.origin, h)))]
            li2 = idx[tuple(sorted((h, s.dest)))]
            d1, d2 = legs[li1].dist, legs[li2].dist
            for m1 in MODES:
                for m2 in MODES:
                    t = _leg_time(d1, m1, params) + _leg_time(d2, m2, params)
                    if t <= deadline:
                        rail = tuple(li for li, m in ((li1, m1), (li2, m2)) if m == RAIL)
                        out.append(RouteCandidate(
                            s_i, ((li1, m1), (li2, m2)), t,
                            _leg_cost(d1, m1, s.qty, params) + _leg_cost(d2, m2, s.qty, params),
                            _leg_co2(d1, m1, s.qty, params) + _leg_co2(d2, m2, s.qty, params), rail))
    return legs, out


def routes_by_shipment(net, routes):
    by_s = [[] for _ in range(net.n_shipments)]
    for r_i, r in enumerate(routes):
        by_s[r.shipment].append(r_i)
    return by_s
