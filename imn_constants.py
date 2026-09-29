"""Konstanten, Regler-Grenzen und feste Seed-Mengen der Demo "Intermodales Netzdesign"."""

from imn_routes import Params

# --- Regler Netzstruktur ---------------------------------------------------------------------------------------
NODES_MIN, NODES_MAX, DEFAULT_NODES = 5, 9, 6
SHIPMENTS_MIN, SHIPMENTS_MAX, DEFAULT_SHIPMENTS = 5, 14, 8
DEADLINE_BASE_MIN, DEADLINE_BASE_MAX, DEFAULT_DEADLINE_BASE = 8, 40, 20    # Stunden
DEADLINE_SPREAD_MIN, DEADLINE_SPREAD_MAX, DEFAULT_DEADLINE_SPREAD = 0, 60, 30   # Prozent
DEFAULT_SEED = 1
SEED_MAX = 2_000_000_000

# --- die drei Kern-Regler (Kipppunkte) + CO2-Zusatzregler ------------------------------------------------------
RATIO_MIN, RATIO_MAX, DEFAULT_RATIO, RATIO_STEP = 0.3, 1.0, 0.5, 0.05           # rail_cost_per_km / truck_cost_per_km
DEADLINE_MULT_MIN, DEADLINE_MULT_MAX, DEFAULT_DEADLINE_MULT, DEADLINE_MULT_STEP = 0.25, 3.0, 1.0, 0.25
QTY_SCALE_MIN, QTY_SCALE_MAX, DEFAULT_QTY_SCALE, QTY_SCALE_STEP = 50, 200, 100, 10   # Prozent
CO2_PRICE_MIN, CO2_PRICE_MAX, DEFAULT_CO2_PRICE, CO2_PRICE_STEP = 0.0, 20.0, 0.0, 1.0   # EUR/kg (gemessen: bei diesen Fixkosten wirkt der Hebel erst ab ~5 EUR/kg, nicht schon im Cent-Bereich)
RULE_THRESHOLD_MIN, RULE_THRESHOLD_MAX, DEFAULT_RULE_THRESHOLD, RULE_THRESHOLD_STEP = 20, 250, 180, 10   # km
# Gemessen: die Regel ist stark empfindlich auf die Schwelle (8,1 % bei der besten Schwelle 180 km, bis zu 82,7 %
# bei einer naiv "mittleren" Schwelle wie 20-30 km) - Default auf die beste Schwelle, damit die Standardansicht
# nicht zufaellig die Regel als Strohmann wirken laesst; der Regler zeigt die Empfindlichkeit selbst.

BASE_PARAMS = Params(truck_cost_per_km=1.0, rail_cost_per_km=DEFAULT_RATIO, truck_speed=60, rail_speed=40,
                      rail_headway=8, rail_fixed_per_km=15)

RATIO_SWEEP = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
DEADLINE_MULT_SWEEP = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0)
QTY_SCALE_SWEEP = (50, 75, 100, 125, 150, 175, 200)
CO2_PRICE_SWEEP = (0.0, 2.0, 5.0, 10.0, 15.0, 20.0)
RULE_THRESHOLD_SWEEP = tuple(range(20, 260, 10))

COLORS = {"truck": "#1f77b4", "rail": "#2ca02c", "mip": "#111111", "rule": "#d62728", "truck_only": "#9aa0a6"}

# --- Presets -----------------------------------------------------------------------------------------------------
_BASE = dict(nodes=DEFAULT_NODES, shipments=DEFAULT_SHIPMENTS, deadline_base=DEFAULT_DEADLINE_BASE,
             deadline_spread=DEFAULT_DEADLINE_SPREAD, seed=DEFAULT_SEED, ratio=DEFAULT_RATIO,
             deadline_mult=DEFAULT_DEADLINE_MULT, qty_scale=DEFAULT_QTY_SCALE, co2_price=DEFAULT_CO2_PRICE,
             rule_threshold=DEFAULT_RULE_THRESHOLD)
PRESETS = {
    "🗺️ Standardnetz": {**_BASE},
    "💰 Günstige Bahn": {**_BASE, "ratio": 0.3},
    "⏱️ Enge Zeitfenster": {**_BASE, "deadline_mult": 0.5},
    "🌱 CO2-Preis": {**_BASE, "co2_price": 10.0},
}
# Jede Zahl in diesen Texten ist in tests/test_claims.py belegt (aus dem echten Code neu berechnet).
PRESET_HELP = {
    "🗺️ Standardnetz": "6 Knoten, 8 Sendungen, Kostenverhältnis Bahn/Lkw 0,5: das exakte Design spart 7,5 % gegenüber „immer Lkw“ (Bahn-Anteil 82 % der Einheit-km). Die beste Naive-Distanzregel liegt noch 8,1 % über dem Optimum.",
    "💰 Günstige Bahn": "Kostenverhältnis 0,3 statt 0,5 (Bahn deutlich günstiger): die Ersparnis wächst auf 21,7 %, Bahn-Anteil 91 %.",
    "⏱️ Enge Zeitfenster": "Nur die Hälfte der Standardfristen: viele Bahn-Routen werden zeitlich unzulässig, Bahn-Anteil und Ersparnis sinken deutlich.",
    "🌱 CO2-Preis": "10 EUR/kg CO2 zusätzlich im Zielwert: Bahn-Anteil steigt von 82 % auf 96 %, Emissionen sinken um 26,3 % — bei nur 6,3 % Mehrkosten. Bei diesem Modell braucht der Hebel einen deutlich höheren Preis als im Cent-Bereich, um zu wirken.",
}
