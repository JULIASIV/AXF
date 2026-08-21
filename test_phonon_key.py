import numpy as np

from phonon_key.beam import Beam, modulus_from_damage
from phonon_key.fatigue import ParisParameters, paris_crack_trajectory
from phonon_key.simulation import run_simulation


def test_frequency_decreases_with_modulus():
    beam = Beam()
    high = beam.natural_frequency_hz(beam.modulus_pa)
    low = beam.natural_frequency_hz(0.8 * beam.modulus_pa)
    assert low < high
    assert np.isfinite(high)


def test_modulus_mapping_is_bounded_and_monotone():
    values = [modulus_from_damage(200e9, x) for x in [0.0, 0.5, 1.0]]
    assert values[0] > values[1] > values[2]
    assert values[2] > 0


def test_paris_trajectory_grows_crack_and_damage():
    t, crack, damage = paris_crack_trajectory(4.0, 100.0, ParisParameters())
    assert len(t) == len(crack) == len(damage)
    assert crack[-1] >= crack[0]
    assert 0.0 <= damage[-1] <= 1.0


def test_end_to_end_public_pattern_is_deterministic():
    pattern = "101100"
    result = run_simulation(pattern, bit_period_s=0.5)
    assert result.public_test_pattern == pattern
    assert result.decoded_bits == pattern
    assert result.stream.shape == result.time_s.shape
