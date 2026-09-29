"""Intermodales Netzdesign - interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Lkw oder Bahn/Schiff je Teilstrecke, gekoppelt mit der Fixkosten-Entscheidung, ob eine Bahn/Schiff-Verbindung
überhaupt eröffnet wird. Fall-Demo auf der Themenseite Netzwerkdesign. Siehe README für die Einordnung.

Lauffähig mit: streamlit run app.py
"""

from dataclasses import replace

import streamlit as st

import imn_constants as C
from imn_evaluation import best_rule_threshold, build_network, co2_price_sweep, compare, cost_ratio_sweep, deadline_mult_sweep, qty_scale_sweep
from imn_presets import apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sync_query_params
from imn_visualization import build_co2_pareto, build_deadline_curve, build_map, build_method_bars, build_qty_curve, build_ratio_curve

st.set_page_config(page_title="Intermodales Netzdesign – Sebastian Hanisch", layout="wide")


def _int(x):
    return f"{int(round(x)):,}".replace(",", " ")


def _pct(x, digits=1):
    return f"{x:.{digits}f} %".replace(".", ",")


@st.cache_resource(show_spinner=False, max_entries=32)
def _network(nodes, shipments, deadline_base, deadline_spread, qty_scale, seed):
    return build_network(nodes, shipments, deadline_base, deadline_spread, qty_scale, seed)


@st.cache_resource(show_spinner=False, max_entries=32)
def _compare(nodes, shipments, deadline_base, deadline_spread, qty_scale, seed, ratio, deadline_mult, co2_price, rule_threshold):
    net = _network(nodes, shipments, deadline_base, deadline_spread, qty_scale, seed)
    params = replace(C.BASE_PARAMS, rail_cost_per_km=ratio * C.BASE_PARAMS.truck_cost_per_km)
    return compare(net, params, deadline_mult=deadline_mult, rule_threshold_km=rule_threshold, co2_price=co2_price)


@st.cache_resource(show_spinner=False, max_entries=16)
def _sweeps(nodes, shipments, deadline_base, deadline_spread, qty_scale, seed, ratio, deadline_mult):
    net = _network(nodes, shipments, deadline_base, deadline_spread, qty_scale, seed)
    params = replace(C.BASE_PARAMS, rail_cost_per_km=ratio * C.BASE_PARAMS.truck_cost_per_km)
    ratio_rows = cost_ratio_sweep(net, C.BASE_PARAMS, C.RATIO_SWEEP)
    deadline_rows = deadline_mult_sweep(net, params, C.DEADLINE_MULT_SWEEP)
    qty_rows = qty_scale_sweep(nodes, shipments, deadline_base, deadline_spread, seed, params, C.QTY_SCALE_SWEEP)
    co2_rows = co2_price_sweep(net, params, deadline_mult, C.CO2_PRICE_SWEEP)
    return ratio_rows, deadline_rows, qty_rows, co2_rows


st.title("🚂 Intermodales Netzdesign")
st.markdown(
    """
Für jede Teilstrecke eine Wahl zwischen **Lkw** (keine Fixkosten, teurer pro Einheit-km, flexible Abfahrt) und
**Bahn/Schiff** (günstiger pro Einheit-km, aber Fixkosten für die Verbindung und feste Abfahrten mit Wartezeit) —
gekoppelt mit der Frage, ob eine Bahn/Schiff-Verbindung überhaupt eröffnet wird. Anders als `slow-steaming-demo`
(ein Modus, stetige Geschwindigkeitswahl) und `linehaul-demo`/`fixkosten-netzdesign-demo` (ein Modus, nur
Hub-vs-Direkt): hier ist die Moduswahl echt UND mit dem Fixkosten-Netzwerkdesign gekoppelt.
"""
)
st.caption(
    "Drei Regler zeigen drei unterschiedlich geformte Kipppunkte: das Kostenverhältnis Bahn/Lkw (ein Gradient), "
    "die Zeitfenster-Enge (eine S-Kurve) und das Sendungsvolumen (ein scharfer Schwellenwert). Ein vierter Regler "
    "(CO2-Preis) zeigt den Kosten-Emissions-Zielkonflikt."
)

st.caption("🎯 Schnellstart – ein Beispiel laden:")
names = list(C.PRESETS.keys())
for row in range(0, len(names), 4):
    preset_cols = st.columns(4)
    for col, name in zip(preset_cols, names[row:row + 4]):
        with col:
            st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name) or None)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Die drei Kipppunkt-Regler**")
    ratio = st.slider("Kostenverhältnis Bahn/Lkw", *bounds("ratio_slider"), key="ratio_slider", step=C.RATIO_STEP,
                      help="Bahn-Variable-Kosten ÷ Lkw-Variable-Kosten. Niedriger = Bahn/Schiff günstiger.")
    deadline_mult = st.slider("Zeitfenster-Multiplikator", *bounds("deadline_mult_slider"), key="deadline_mult_slider", step=C.DEADLINE_MULT_STEP,
                              help="Skaliert alle Lieferfristen. Kleiner = engere Fenster, Bahn wird durch feste Abfahrten unattraktiver.")
    qty_scale = st.slider("Sendungsvolumen [%]", *bounds("qty_scale_slider"), key="qty_scale_slider", step=C.QTY_SCALE_STEP,
                          help="Skaliert alle Sendungsmengen. Mehr Volumen bündelt sich besser über eine Bahn/Schiff-Verbindung.")
    st.markdown("**Zusatzregler**")
    co2_price = st.slider("CO2-Preis [EUR/kg]", *bounds("co2_price_slider"), key="co2_price_slider", step=C.CO2_PRICE_STEP)
    rule_threshold = st.slider("Distanzregel-Schwelle [km]", *bounds("rule_threshold_slider"), key="rule_threshold_slider", step=C.RULE_THRESHOLD_STEP,
                               help="„Bahn, wenn die Teilstrecke länger als X km ist“ — die naive Vergleichsregel. Voreingestellt auf die beste gemessene Schwelle; eine schlechter gewählte kann deutlich teurer sein (siehe Text unten).")
    st.markdown("---")
    st.markdown("**Netzstruktur**")
    nodes = st.slider("Knoten", *bounds("nodes_slider"), key="nodes_slider")
    shipments = st.slider("Sendungen", *bounds("shipments_slider"), key="shipments_slider")
    deadline_base = st.slider("Basis-Frist [h]", *bounds("deadline_base_slider"), key="deadline_base_slider")
    deadline_spread = st.slider("Streuung der Fristen [%]", *bounds("deadline_spread_slider"), key="deadline_spread_slider")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neues Netz generieren", width="stretch", on_click=randomize_seed)

sync_query_params(nodes, shipments, deadline_base, deadline_spread, seed, ratio, deadline_mult, qty_scale, co2_price, rule_threshold)

with st.spinner("Rechne..."):
    c = _compare(int(nodes), int(shipments), int(deadline_base), int(deadline_spread), int(qty_scale), int(seed),
                float(ratio), float(deadline_mult), float(co2_price), float(rule_threshold))

st.markdown(f"Das Netz hat **{c.net.n} Knoten** und **{c.net.n_shipments} Sendungen**. Bahn-Anteil im exakten Design: **{_pct(100 * c.mip.rail_share_unit_km)}** der Einheit-km.")

st.markdown("---")

st.markdown("## 🎯 Methodenvergleich")
c1, c2, c3 = st.columns(3)
c1.metric("Immer Lkw", _int(c.truck_only.objective))
c2.metric("Naive Distanzregel", _int(c.rule.objective), delta=f"{_pct(c.rule_gap_pct)} über dem Optimum", delta_color="inverse")
c3.metric("Exakt (MIP)", _int(c.mip.objective), delta=f"{_pct(c.savings_vs_truck_pct)} günstiger als „immer Lkw“", delta_color="off")
st.plotly_chart(build_method_bars(c.mip, c.truck_only, c.rule), width="stretch", key="method_bars")
if c.savings_vs_truck_pct > 0.5:
    st.success(f"✅ Das exakte Design spart {_pct(c.savings_vs_truck_pct)} gegenüber „immer Lkw“. Bei der aktuellen Distanzregel-Schwelle liegt die Regel {_pct(c.rule_gap_pct)} über dem Optimum — eine Distanzregel ist nicht dumm, trifft den Haupteffekt aber nur grob.")
else:
    st.info("Bei dieser Konfiguration lohnt sich Bahn/Schiff kaum oder gar nicht — alle drei Methoden landen nah beieinander.")
st.caption("Die Regel reagiert empfindlich auf ihre Schwelle: bei der besten gemessenen Schwelle (180 km, Standardwert des Reglers) liegt sie 8,1 % über dem Optimum, bei einer naiv niedrig gewählten Schwelle (20–30 km) bis zu 82,7 % — probieren Sie den Regler „Distanzregel-Schwelle“ links.")

st.plotly_chart(build_map(c.net, c.legs, c.routes, c.mip.chosen), width="stretch", key="map_chart")
st.caption("Grün: von einer gewählten Route per Bahn/Schiff genutzt. Blau: per Lkw genutzt. Grau: ungenutzt.")

st.markdown("---")

st.subheader("🔬 Die drei Kipppunkte")
st.caption("Sweeps bei sonst aktuellen Reglerwerten (dauert einige Sekunden).")
if st.button("Kipppunkte durchrechnen", key="sweep_start"):
    st.session_state["sweep_on"] = True
if st.session_state.get("sweep_on"):
    with st.spinner("Rechne Sweeps..."):
        ratio_rows, deadline_rows, qty_rows, co2_rows = _sweeps(int(nodes), int(shipments), int(deadline_base), int(deadline_spread), int(qty_scale), int(seed), float(ratio), float(deadline_mult))
    t1, t2, t3, t4 = st.tabs(["Kostenverhältnis (Gradient)", "Zeitfenster (S-Kurve)", "Sendungsvolumen (Schwelle)", "CO2-Preis (Pareto)"])
    with t1:
        st.plotly_chart(build_ratio_curve(ratio_rows), width="stretch", key="ratio_chart")
        st.caption("Der Bahn-Anteil fällt als echter Gradient, kein Sprung: mehrere Relationen kippen bei unterschiedlichen Kostenverhältnissen.")
    with t2:
        st.plotly_chart(build_deadline_curve(deadline_rows), width="stretch", key="deadline_chart")
        st.caption("Bei sehr engen Fenstern passt kein fester Bahn-Fahrplan; der Bahn-Anteil sättigt bei lockeren Fristen.")
    with t3:
        st.plotly_chart(build_qty_curve(qty_rows), width="stretch", key="qty_chart")
        st.caption("Ein scharfer Kippbereich statt Stetigkeit: erst ab genug gebündeltem Volumen lohnt sich die Fixkosten-Investition.")
    with t4:
        st.plotly_chart(build_co2_pareto(co2_rows), width="stretch", key="co2_chart")
        st.caption("Jeder Punkt ist ein CO2-Preis (beschriftet). Bei diesem Netz braucht der Hebel einen deutlich höheren Preis als im Cent-Bereich, um sichtbar zu wirken.")

st.markdown("---")

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist |
|---|---|
| **Höchstens ein Umschlagpunkt je Sendung** | Wie `linehaul-demo`: mehr als ein Umschlag pro Sendung ist unüblich in der Praxis, aber nicht abgebildet. |
| **Bahn-Fixkosten linear in der Distanz** | Reale Terminalanbindungen haben eigene, oft nicht-lineare Kostenstrukturen. |
| **Mittlere Wartezeit statt echtem Fahrplan** | Feste Abfahrten werden nur als Taktzeit/2 modelliert, kein echter Fahrplan mit Anschlüssen. |
| **Naive Distanzregel als einziger Heuristik-Vergleich** | Eine ausgefeiltere Regel (z. B. volumen- oder fristbewusst) wurde nicht gebaut. |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Modell.** Sendungen $S$, Kandidatenrouten $R_s$ je Sendung $s$ (direkt oder über einen Hub, je Teilstrecke Lkw
oder Bahn/Schiff, zeitlich zulässig gefiltert), potenzielle Bahn/Schiff-Verbindungen (Kanten) $E$ mit Fixkosten
$f_e$:
$$\min\sum_{e\in E} f_ey_e+\sum_{s\in S}\sum_{r\in R_s}c_rz_r\quad\text{u.d.N.}\quad\sum_{r\in R_s}z_r=1\ \forall s,\quad z_r\le y_e\ \text{falls } r \text{ Bahn auf } e\text{ nutzt},\quad y_e,z_r\in\{0,1\}.$$

Mit CO2-Preis $p$: $c_r$ wird um $p\cdot\text{co2}_r$ erweitert (Einheit-km mal Emissionsfaktor je Modus).

**"Immer Lkw"** löst dasselbe MIP mit $R_s$ auf reine Lkw-Routen eingeschränkt (keine Design-Variablen nötig).
**Naive Distanzregel**: Modus je Teilstrecke fest nach einer Distanzschwelle, dann je Sendung die billigste
Route, die dieser Regel folgt.

Implementiert in `imn_scenario.py` (Netz, Sendungen), `imn_routes.py` (Kandidatenrouten), `imn_formulation.py`
(HiGHS-MIP), `imn_rules.py` (Distanzregel), `imn_evaluation.py` (Methodenvergleich, Kipppunkt-Sweeps).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
