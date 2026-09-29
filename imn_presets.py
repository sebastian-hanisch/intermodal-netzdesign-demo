"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Button (nach dem in `linehaul-demo` etablierten Muster)."""

import random

import streamlit as st

import imn_constants as C

SETTING_SPECS = {
    "nodes_slider": {"url": "n", "caster": int, "default": C.DEFAULT_NODES, "lo": C.NODES_MIN, "hi": C.NODES_MAX},
    "shipments_slider": {"url": "sh", "caster": int, "default": C.DEFAULT_SHIPMENTS, "lo": C.SHIPMENTS_MIN, "hi": C.SHIPMENTS_MAX},
    "deadline_base_slider": {"url": "db", "caster": int, "default": C.DEFAULT_DEADLINE_BASE, "lo": C.DEADLINE_BASE_MIN, "hi": C.DEADLINE_BASE_MAX},
    "deadline_spread_slider": {"url": "ds", "caster": int, "default": C.DEFAULT_DEADLINE_SPREAD, "lo": C.DEADLINE_SPREAD_MIN, "hi": C.DEADLINE_SPREAD_MAX},
    "seed_input": {"url": "seed", "caster": int, "default": C.DEFAULT_SEED, "lo": 0, "hi": C.SEED_MAX},
    "ratio_slider": {"url": "r", "caster": float, "default": C.DEFAULT_RATIO, "lo": C.RATIO_MIN, "hi": C.RATIO_MAX},
    "deadline_mult_slider": {"url": "dm", "caster": float, "default": C.DEFAULT_DEADLINE_MULT, "lo": C.DEADLINE_MULT_MIN, "hi": C.DEADLINE_MULT_MAX},
    "qty_scale_slider": {"url": "q", "caster": int, "default": C.DEFAULT_QTY_SCALE, "lo": C.QTY_SCALE_MIN, "hi": C.QTY_SCALE_MAX},
    "co2_price_slider": {"url": "co2", "caster": float, "default": C.DEFAULT_CO2_PRICE, "lo": C.CO2_PRICE_MIN, "hi": C.CO2_PRICE_MAX},
    "rule_threshold_slider": {"url": "rt", "caster": float, "default": C.DEFAULT_RULE_THRESHOLD, "lo": C.RULE_THRESHOLD_MIN, "hi": C.RULE_THRESHOLD_MAX},
}


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec["lo"], spec["hi"]


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec["default"]


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec["url"] in qp:
            try:
                value = spec["caster"](qp[spec["url"]])
                value = max(spec["lo"], min(spec["hi"], value))
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    st.session_state["permalink_loaded"] = True


def sync_query_params(nodes, shipments, deadline_base, deadline_spread, seed, ratio, deadline_mult, qty_scale, co2_price, rule_threshold):
    try:
        st.query_params["n"] = str(int(nodes))
        st.query_params["sh"] = str(int(shipments))
        st.query_params["db"] = str(int(deadline_base))
        st.query_params["ds"] = str(int(deadline_spread))
        st.query_params["seed"] = str(int(seed))
        st.query_params["r"] = str(ratio)
        st.query_params["dm"] = str(deadline_mult)
        st.query_params["q"] = str(int(qty_scale))
        st.query_params["co2"] = str(co2_price)
        st.query_params["rt"] = str(rule_threshold)
    except Exception:
        pass


def apply_preset(name):
    p = C.PRESETS[name]
    st.session_state["nodes_slider"] = p["nodes"]
    st.session_state["shipments_slider"] = p["shipments"]
    st.session_state["deadline_base_slider"] = p["deadline_base"]
    st.session_state["deadline_spread_slider"] = p["deadline_spread"]
    st.session_state["seed_input"] = p["seed"]
    st.session_state["ratio_slider"] = p["ratio"]
    st.session_state["deadline_mult_slider"] = p["deadline_mult"]
    st.session_state["qty_scale_slider"] = p["qty_scale"]
    st.session_state["co2_price_slider"] = p["co2_price"]
    st.session_state["rule_threshold_slider"] = p["rule_threshold"]


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
