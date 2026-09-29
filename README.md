# Intermodales Netzdesign – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-intermodal-netzdesign-demo.streamlit.app/)**

Fall-Demo auf der Themenseite **Netzwerkdesign** für die Website "Sebastian Hanisch – Operations Research und
Machine Learning": für jede Teilstrecke eine Wahl zwischen **Lkw** (keine Fixkosten, teurer pro Einheit-km,
flexible Abfahrt) und **Bahn/Schiff** (günstiger pro Einheit-km, aber Fixkosten für die Verbindung und feste
Abfahrten mit Wartezeit) — gekoppelt mit der Fixkosten-Entscheidung, ob eine Bahn/Schiff-Verbindung überhaupt
eröffnet wird.

## Warum das ein eigenständiges Modell ist

Anders als `slow-steaming-demo` (ein Modus, stetige Geschwindigkeitswahl auf See) und `linehaul-demo`/
`fixkosten-netzdesign-demo` (ein Modus, nur die Entscheidung Hub-vs-Direkt): hier ist die **Moduswahl je
Teilstrecke** echt, und sie ist mit dem Fixkosten-Netzwerkdesign gekoppelt — eine Bahn/Schiff-Kante lohnt sich
nur, wenn genug Sendungen sie teilen, und ob sie zeitlich passt, hängt vom festen Fahrplan ab.

## Drei Kipppunkte, unterschiedlich geformt

**Kostenverhältnis Bahn/Lkw** (Gradient): der Bahn-Anteil fällt stetig, kein Sprung — verschiedene Relationen
kippen bei unterschiedlichen Kostenverhältnissen. **Zeitfenster-Multiplikator** (S-Kurve): bei sehr engen Fenstern
passt kein fester Bahn-Fahrplan, der Bahn-Anteil sättigt bei lockeren Fristen. **Sendungsvolumen** (scharfer
Schwellenwert): erst ab genug gebündeltem Volumen lohnt sich die Fixkosten-Investition in eine Bahn-Verbindung.
Ein vierter Regler (**CO2-Preis**) zeigt den Kosten-Emissions-Zielkonflikt als Pareto-Kurve.

## Ergebnis (Zahlen aus den Tests)

Jede hier genannte Zahl ist in `tests/test_claims.py` belegt: Standardnetz 6 Knoten, 8 Sendungen, Seed 1
(SplitMix64, ganzzahlig, plattformstabil), Kostenverhältnis Bahn/Lkw 0,5.

**Methodenvergleich.** Das exakte Design (MIP) kostet **9 162**, "immer Lkw" **9 900** — eine Ersparnis von
**7,5 %**, mit **82,0 %** der Einheit-km per Bahn/Schiff. Bei der besten gemessenen Distanzregel-Schwelle
(180 km) liegt die naive Regel nur **8,1 %** über dem Optimum — die Regel ist nicht dumm, sie trifft den
Haupteffekt schon grob.

**Die Regel reagiert aber stark auf ihre Schwelle.** Eine naiv niedrig gewählte Schwelle (20–30 km, "Bahn schon
ab kurzer Distanz") kostet **82,7 %** über dem Optimum — mehr als das Zehnfache des Werts bei der besten Schwelle.
Der Grund: eine falsch kalibrierte Regel eröffnet viele einzeln genutzte Bahn-Verbindungen, deren Fixkosten sich
nicht amortisieren, statt sich auf wenige, gut ausgelastete zu konzentrieren wie das MIP. Der Regler
"Distanzregel-Schwelle" in der App zeigt diese Empfindlichkeit direkt.

**Kostenverhältnis-Kipppunkt.** Bei Kostenverhältnis 0,3 (Bahn deutlich günstiger) wächst die Ersparnis auf
**21,7 %** (Bahn-Anteil 91,0 %); ab Verhältnis 0,7 lohnt sich Bahn/Schiff in diesem Netz gar nicht mehr.

**Zeitfenster-Kipppunkt.** Bei halbierten Fristen (Multiplikator 0,5) sinkt der Bahn-Anteil von 82,0 % auf
**54,8 %** — viele Bahn-Routen werden zeitlich unzulässig.

**CO2-Preis.** Bei diesem Netz braucht der Hebel einen deutlich höheren Preis als im Cent-Bereich, um sichtbar
zu wirken (die Fixkosten dominieren die kleinen CO2-Kostenunterschiede): erst ab rund 5 EUR/kg ändert sich etwas.
Bei 10 EUR/kg CO2-Preis steigt der Bahn-Anteil von 82,0 % auf **96,0 %**, die Emissionen sinken um **26,3 %**,
bei nur **6,3 %** Mehrkosten — ein echter, aber teurer erkaufter Pareto-Punkt.

## Was nicht funktioniert hat / Vorab-Hypothesen

- **"Die Ersparnis der Distanzregel liegt bei 2–5 %, wie in der Vorab-Messreihe" — bestätigt nur für die BESTE
  Schwelle.** Die Vorab-Messreihe (andere Instanz, andere Parameter) maß 2,2–5,0 % über Schwellen 50–200 km.
  Beim Nachbau mit dieser Instanz liegt die beste Schwelle bei 8,1 % (nah dran), aber eine mittelmäßig gewählte
  Schwelle kostet deutlich mehr (bis 82,7 %) — kein Widerspruch, aber ein wichtiger Zusatzfund: die
  Distanzregel-Ersparnis hängt stark von der Kalibrierung ab, nicht nur vom Modell selbst. Deshalb zeigt die App
  standardmäßig die BESTE gemessene Schwelle (fair gegenüber der Regel) UND lässt die Empfindlichkeit über den
  Schwellenregler explorierbar.
- **"CO2-Preis wirkt schon im Cent-Bereich, wie in der Vorab-Messreihe" — widerlegt für diese Parametrisierung.**
  Bei den hier gewählten Fixkosten (15 EUR/km je Bahn-Verbindung) ist der CO2-Hebel bei 0–2 EUR/kg wirkungslos;
  erst ab ~5 EUR/kg ändert sich etwas. Der Regler-Bereich wurde entsprechend auf 0–20 EUR/kg angepasst, statt die
  Vorab-Zahl ungeprüft zu übernehmen.

## Grenzen (was die Demo nicht zeigt)

Höchstens ein Umschlagpunkt je Sendung (wie `linehaul-demo`); Bahn-Fixkosten linear in der Distanz; mittlere
Wartezeit (Taktzeit/2) statt echtem Fahrplan mit Anschlüssen; nur eine naive Heuristik (Distanzregel) als
Vergleich, keine ausgefeiltere volumen- oder fristbewusste Regel.

## Dateien

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche: Methodenvergleich, Netzkarte, drei Kipppunkt-Sweeps, CO2-Pareto, 📐-Abschnitt |
| `imn_scenario.py` | Netz und Sendungen (SplitMix64) |
| `imn_routes.py` | Kandidatenrouten (direkt/Hub × Lkw/Bahn), Zeitfenster-Filter |
| `imn_formulation.py` | HiGHS-MIP: Routenwahl + Bahn-Design, gekoppelt; "Immer Lkw"-Variante |
| `imn_rules.py` | Naive Distanzregel |
| `imn_evaluation.py` | Methodenvergleich, die drei Kipppunkt-Sweeps, CO2-Pareto |
| `imn_visualization.py` | Netzkarte, Balken, Kipppunkt-Kurven, CO2-Pareto-Chart |
| `imn_presets.py`, `imn_constants.py` | Presets, Permalink, Regler-Grenzen |
| `tests/` | Szenario, Routen, Formulierung (gegen Brute-Force auf 2 Kleinstnetzen), Regeln, Auswertung, Presets, App, `test_claims.py` (jede README-Zahl) |

Lokal starten: `pip install -r requirements.txt`, dann `streamlit run app.py`; Tests: `pip install -r requirements-dev.txt`, dann `python -m pytest tests`.
