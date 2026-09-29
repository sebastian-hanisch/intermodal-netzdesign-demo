import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from imn_scenario import SplitMix64, distance, generate


def test_splitmix64_deterministic():
    a, b = SplitMix64(1), SplitMix64(1)
    assert [a.next() for _ in range(5)] == [b.next() for _ in range(5)]


def test_generate_reproducible():
    a = generate(6, 8, 20, 30, 100, 1)
    b = generate(6, 8, 20, 30, 100, 1)
    assert a == b


def test_generate_shapes():
    net = generate(6, 8, 20, 30, 100, 1)
    assert net.n == 6
    assert net.n_shipments == 8
    for s in net.shipments:
        assert s.origin != s.dest
        assert 0 <= s.origin < 6 and 0 <= s.dest < 6
        assert s.qty >= 1
        assert s.deadline >= 1.0


def test_distance_matches_manual():
    assert distance((0, 0), (3, 4)) == 5.0


def test_qty_scale_scales_quantities():
    base = generate(6, 8, 20, 30, 100, 1)
    scaled = generate(6, 8, 20, 30, 200, 1)
    for a, b in zip(base.shipments, scaled.shipments):
        assert b.qty >= a.qty
