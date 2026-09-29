"""Szenario: ein kleines Distributionsnetz (Depots/Terminals auf einer Karte) mit Sendungen, die von einem
Ursprung zu einem Ziel müssen, mit Menge und Frist. Grundlage für die Routenwahl in `imn_routes.py`.

Ganzzahlig, eigener Zufallsgenerator (SplitMix64 auf Python-Ints) statt `numpy.random`: numpy garantiert keine
über Versionen stabilen Zufallsströme, die CI installiert aber wöchentlich die neueste Version (Konvention der
zuletzt gebauten Fall-Demos, `dc-standort-demo`/`netzdesign-unsicherheit-demo`)."""

from dataclasses import dataclass

_MASK = (1 << 64) - 1
MAP_W = 200          # Kartenbreite in km


class SplitMix64:
    def __init__(self, seed):
        self.state = seed & _MASK

    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & _MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def below(self, n):
        return self.next() % n


@dataclass(frozen=True)
class Shipment:
    origin: int
    dest: int
    qty: int          # Einheiten (z.B. Paletten)
    deadline: float    # Stunden ab Abfahrt


@dataclass(frozen=True)
class Network:
    names: tuple
    pos: tuple                # ((x, y) in km, ...)
    shipments: tuple          # Shipment, ...

    @property
    def n(self):
        return len(self.names)

    @property
    def n_shipments(self):
        return len(self.shipments)


def _names(n):
    return tuple(f"Knoten {i + 1}" for i in range(n))


def distance(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def generate(n_nodes, n_shipments, deadline_base, deadline_spread_pct, qty_scale_pct, seed):
    """Knoten gleichverteilt auf einer Karte `MAP_W` x `MAP_W` km. Sendungen: zufälliges Ursprung-Ziel-Paar
    (verschieden), Menge 5..20 skaliert mit `qty_scale_pct`, Frist `deadline_base` Stunden skaliert mit einem
    Faktor 1 +- `deadline_spread_pct`/100 (mindestens 1 Stunde)."""
    rng = SplitMix64(seed)
    pos = tuple((rng.below(MAP_W), rng.below(MAP_W)) for _ in range(n_nodes))
    shipments = []
    for _ in range(n_shipments):
        o = rng.below(n_nodes)
        d = (o + 1 + rng.below(n_nodes - 1)) % n_nodes
        qty = max(1, (5 + rng.below(16)) * qty_scale_pct // 100)
        spread = rng.below(2 * deadline_spread_pct + 1) - deadline_spread_pct
        deadline = max(1.0, deadline_base * (100 + spread) / 100)
        shipments.append(Shipment(o, d, qty, deadline))
    return Network(_names(n_nodes), pos, tuple(shipments))
