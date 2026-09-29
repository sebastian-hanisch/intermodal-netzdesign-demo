"""Plotly-Abbildungen: Netzkarte mit genutzten Kanten (grün = Bahn/Schiff, blau = Lkw, grau = ungenutzt), Balken
Methodenvergleich, die drei Kipppunkt-Kurven (Gradient/S-Kurve/Schwelle) und der CO2-Pareto-Chart."""

import plotly.graph_objects as go

import imn_constants as C
from imn_routes import RAIL


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.15), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(net, legs, routes, chosen, height=460):
    """Karte: Knoten, Kanten eingefärbt danach, ob eine gewählte Route sie per Bahn (grün), Lkw (blau) oder gar nicht (grau) nutzt."""
    used_rail, used_truck = set(), set()
    for r_i in chosen:
        route = routes[r_i]
        for li, mode in route.legs:
            (used_rail if mode == RAIL else used_truck).add(li)
    used_truck -= used_rail
    fig = go.Figure()
    groups = [("Bahn/Schiff genutzt", used_rail, C.COLORS["rail"], 3), ("Lkw genutzt", used_truck, C.COLORS["truck"], 2),
              ("ungenutzt", set(range(len(legs))) - used_rail - used_truck, "#d8d8d8", 1)]
    for label, idxs, color, width in groups:
        xs, ys = [], []
        for li in idxs:
            leg = legs[li]
            xs += [net.pos[leg.u][0], net.pos[leg.v][0], None]
            ys += [net.pos[leg.u][1], net.pos[leg.v][1], None]
        if xs:
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width), name=label, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[p[0] for p in net.pos], y=[p[1] for p in net.pos], mode="markers+text", text=list(net.names),
                             textposition="top center", marker=dict(size=16, color="#f0f0f0", line=dict(color="#333333", width=1)),
                             textfont=dict(size=9), showlegend=False))
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1, title="km")
    fig.update_yaxes(visible=False)
    return _base(fig, height)


def build_method_bars(mip, truck_only, rule, height=340):
    names = ["Immer Lkw", "Naive Distanzregel", "Exakt (MIP)"]
    costs = [truck_only.objective, rule.objective, mip.objective]
    colors = [C.COLORS["truck_only"], C.COLORS["rule"], C.COLORS["mip"]]
    fig = go.Figure(go.Bar(x=names, y=costs, marker=dict(color=colors),
                           text=[f"{v:,.0f}".replace(",", " ") for v in costs], textposition="outside"))
    fig.update_yaxes(title="Gesamtkosten (EUR)")
    return _base(fig, height)


def build_ratio_curve(rows, height=380):
    xs = [r["ratio"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[100 * r["rail_share"] for r in rows], mode="lines+markers", name="Bahn-Anteil [%]", line=dict(color=C.COLORS["rail"])))
    fig.add_trace(go.Scatter(x=xs, y=[r["savings_pct"] for r in rows], mode="lines+markers", name="Ersparnis ggü. „immer Lkw“ [%]", line=dict(color=C.COLORS["mip"]), yaxis="y2"))
    fig.update_xaxes(title="Kostenverhältnis Bahn/Lkw")
    fig.update_yaxes(title="Bahn-Anteil [%]", range=[-3, 103])
    fig.update_layout(yaxis2=dict(title="Ersparnis [%]", overlaying="y", side="right"))
    return _base(fig, height)


def build_deadline_curve(rows, height=340):
    xs = [r["mult"] for r in rows]
    fig = go.Figure(go.Scatter(x=xs, y=[100 * r["rail_share"] for r in rows], mode="lines+markers", line=dict(color=C.COLORS["rail"])))
    fig.update_xaxes(title="Zeitfenster-Multiplikator")
    fig.update_yaxes(title="Bahn-Anteil [%]", range=[-3, 103])
    return _base(fig, height)


def build_qty_curve(rows, height=340):
    xs = [r["scale"] for r in rows]
    fig = go.Figure(go.Scatter(x=xs, y=[100 * r["rail_share"] for r in rows], mode="lines+markers", line=dict(color=C.COLORS["rail"])))
    fig.update_xaxes(title="Sendungsvolumen [% der Standardmenge]")
    fig.update_yaxes(title="Bahn-Anteil [%]", range=[-3, 103])
    return _base(fig, height)


def build_co2_pareto(rows, height=380):
    xs = [r["co2"] for r in rows]
    ys = [r["cost"] for r in rows]
    fig = go.Figure(go.Scatter(x=xs, y=ys, mode="lines+markers+text", line=dict(color=C.COLORS["mip"]),
                               text=[f"{r['price']:.0f} EUR/kg" for r in rows], textposition="top center"))
    fig.update_xaxes(title="CO2-Emissionen [kg]", autorange="reversed")
    fig.update_yaxes(title="Kosten (ohne CO2-Preis-Aufschlag) [EUR]")
    return _base(fig, height)
