import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import imn_constants as C
from imn_presets import SETTING_SPECS


def test_every_preset_has_all_keys():
    required = {"nodes", "shipments", "deadline_base", "deadline_spread", "seed", "ratio", "deadline_mult", "qty_scale", "co2_price", "rule_threshold"}
    for name, p in C.PRESETS.items():
        assert required.issubset(p.keys()), name


def test_preset_values_within_bounds():
    for name, p in C.PRESETS.items():
        assert C.NODES_MIN <= p["nodes"] <= C.NODES_MAX, name
        assert C.SHIPMENTS_MIN <= p["shipments"] <= C.SHIPMENTS_MAX, name
        assert C.RATIO_MIN <= p["ratio"] <= C.RATIO_MAX, name
        assert C.DEADLINE_MULT_MIN <= p["deadline_mult"] <= C.DEADLINE_MULT_MAX, name
        assert C.CO2_PRICE_MIN <= p["co2_price"] <= C.CO2_PRICE_MAX, name
        assert C.RULE_THRESHOLD_MIN <= p["rule_threshold"] <= C.RULE_THRESHOLD_MAX, name


def test_setting_specs_defaults_within_own_bounds():
    for key, spec in SETTING_SPECS.items():
        assert spec["lo"] <= spec["default"] <= spec["hi"], key
