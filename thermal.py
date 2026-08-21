"""Synthetic thermal-pulse model.

The phrase CPU-load modulation is represented as a time-varying abstract load
trace.  This module intentionally does not busy-loop, spawn worker processes,
or alter the host machine's CPU utilization.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ThermalParameters:
    ambient_c: float = 22.0
    thermal_resistance_c_per_w: float = 0.30
    thermal_time_constant_s: float = 0.35
    reference_temperature_c: float = 22.0
    modulus_temp_coeff_per_c: float = -4.0e-4


def cpu_load_modulation(
    t: np.ndarray,
    bits: str,
    bit_period_s: float,
    low_load: float = 0.20,
    high_load: float = 0.90,
) -> np.ndarray:
    """Convert a public diagnostic bit string into a synthetic load waveform.

    This is a mathematical trace only.  It does not control the real CPU.
    """
    if not bits or any(bit not in "01" for bit in bits):
        raise ValueError("bits must be a non-empty binary string")
    if bit_period_s <= 0:
        raise ValueError("bit_period_s must be positive")
    indices = np.floor(np.asarray(t) / bit_period_s).astype(int)
    selected = np.minimum(indices, len(bits) - 1)
    values = np.fromiter((high_load if bits[i] == "1" else low_load for i in selected), dtype=float)
    return values


def thermal_response(
    t: np.ndarray,
    load: np.ndarray,
    params: ThermalParameters,
) -> np.ndarray:
    """Simulate first-order thermal response to the abstract load trace."""
    t = np.asarray(t, dtype=float)
    load = np.asarray(load, dtype=float)
    if t.ndim != 1 or load.shape != t.shape:
        raise ValueError("t and load must be one-dimensional arrays of equal shape")
    if len(t) == 0:
        return np.array([], dtype=float)

    power_w = np.clip(load, 0.0, 1.0) * 35.0
    temperature = np.empty_like(t)
    temperature[0] = params.ambient_c
    for idx in range(1, len(t)):
        dt = max(t[idx] - t[idx - 1], 0.0)
        target = params.ambient_c + params.thermal_resistance_c_per_w * power_w[idx]
        alpha = 1.0 - np.exp(-dt / params.thermal_time_constant_s)
        temperature[idx] = temperature[idx - 1] + alpha * (target - temperature[idx - 1])
    return temperature


def temperature_modulus_factor(
    temperature_c: np.ndarray,
    params: ThermalParameters,
) -> np.ndarray:
    """Return a linearized temperature-to-modulus factor around a reference."""
    delta = np.asarray(temperature_c) - params.reference_temperature_c
    return np.clip(1.0 + params.modulus_temp_coeff_per_c * delta, 0.85, 1.05)
