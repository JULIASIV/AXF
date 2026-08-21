"""End-to-end benign Phonon-Key laboratory simulation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .beam import Beam, modulus_from_damage
from .fatigue import ParisParameters, paris_crack_trajectory
from .signal import DSPParameters, decode_bits_from_fft, synthesize_stream
from .thermal import ThermalParameters, cpu_load_modulation, temperature_modulus_factor, thermal_response


@dataclass
class SimulationResult:
    time_s: np.ndarray
    crack_m: np.ndarray
    damage: np.ndarray
    thermal_load: np.ndarray
    temperature_c: np.ndarray
    effective_modulus_pa: np.ndarray
    fatigue_frequency_hz: np.ndarray
    stream: np.ndarray
    decoded_bits: str
    estimated_frequencies_hz: np.ndarray
    bit_period_s: float
    public_test_pattern: str


def run_simulation(
    public_test_pattern: str = "1011001110010110",
    bit_period_s: float = 1.0,
    beam: Beam | None = None,
    paris: ParisParameters | None = None,
    thermal: ThermalParameters | None = None,
    dsp: DSPParameters | None = None,
) -> SimulationResult:
    """Run a deterministic, hardware-free telemetry demonstration."""
    beam = beam or Beam()
    paris = paris or ParisParameters()
    thermal = thermal or ThermalParameters()
    dsp = dsp or DSPParameters()
    if not public_test_pattern or any(bit not in "01" for bit in public_test_pattern):
        raise ValueError("public_test_pattern must be a non-empty binary string")

    duration_s = len(public_test_pattern) * bit_period_s
    time_s, crack_m, damage = paris_crack_trajectory(
        duration_s=duration_s,
        sample_rate_hz=dsp.sample_rate_hz,
        params=paris,
    )
    load = cpu_load_modulation(time_s, public_test_pattern, bit_period_s)
    temperature_c = thermal_response(time_s, load, thermal)
    temp_factor = temperature_modulus_factor(temperature_c, thermal)
    fatigue_modulus = np.array(
        [modulus_from_damage(beam.modulus_pa, value, maximum_loss=0.20) for value in damage]
    )
    effective_modulus_pa = fatigue_modulus * temp_factor
    fatigue_frequency_hz = np.array(
        [beam.natural_frequency_hz(value) for value in effective_modulus_pa]
    )

    # Integrate one ODE trace using the mean effective modulus to ensure the
    # ODE solver is part of the pipeline.  The time-varying stream below is a
    # synthetic sensor observation around the same physical resonance.
    mean_modulus = float(np.mean(effective_modulus_pa))
    _, _ode_displacement = beam.ode_trace(
        duration_s=duration_s,
        sample_rate_hz=dsp.sample_rate_hz,
        modulus_pa=mean_modulus,
        force_hz=float(np.mean(fatigue_frequency_hz)),
    )

    stream = synthesize_stream(
        time_s,
        fatigue_frequency_hz,
        public_test_pattern,
        bit_period_s,
        dsp,
    )
    decoded_bits, estimates, _threshold = decode_bits_from_fft(
        time_s,
        stream,
        fatigue_frequency_hz,
        public_test_pattern,
        bit_period_s,
        dsp,
    )
    return SimulationResult(
        time_s=time_s,
        crack_m=crack_m,
        damage=damage,
        thermal_load=load,
        temperature_c=temperature_c,
        effective_modulus_pa=effective_modulus_pa,
        fatigue_frequency_hz=fatigue_frequency_hz,
        stream=stream,
        decoded_bits=decoded_bits,
        estimated_frequencies_hz=estimates,
        bit_period_s=bit_period_s,
        public_test_pattern=public_test_pattern,
    )
