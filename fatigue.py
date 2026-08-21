"""Bounded Paris-law fatigue surrogate for a laboratory simulation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class ParisParameters:
    """Parameters for da/dN = C * (Delta K)^m.

    The values are illustrative, not a material qualification dataset.
    """

    c_m_per_cycle: float = 2.0e-10
    exponent_m: float = 3.0
    stress_range_pa: float = 150e6
    geometry_factor: float = 1.12
    initial_crack_m: float = 0.5e-3
    critical_crack_m: float = 3.0e-3
    cycle_rate_hz: float = 40.0

    def stress_intensity_range_mpa_sqrt_m(self, crack_m: float) -> float:
        crack_m = max(float(crack_m), 1e-12)
        # Paris coefficients are conventionally tabulated with Delta K in
        # MPa*sqrt(m), while the beam stresses are stored in pascals.
        stress_range_mpa = self.stress_range_pa / 1.0e6
        return self.geometry_factor * stress_range_mpa * np.sqrt(np.pi * crack_m)

    def crack_growth_rate_m_per_cycle(self, crack_m: float) -> float:
        delta_k = self.stress_intensity_range_mpa_sqrt_m(crack_m)
        return self.c_m_per_cycle * delta_k**self.exponent_m


def paris_crack_trajectory(
    duration_s: float,
    sample_rate_hz: float,
    params: ParisParameters,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Integrate crack length and return time, crack length, and normalized damage."""
    if duration_s <= 0 or sample_rate_hz <= 0:
        raise ValueError("duration_s and sample_rate_hz must be positive")
    if params.critical_crack_m <= params.initial_crack_m:
        raise ValueError("critical_crack_m must exceed initial_crack_m")

    t_eval = np.arange(0.0, duration_s, 1.0 / sample_rate_hz)

    def rhs(_t: float, y: np.ndarray) -> list[float]:
        a = float(np.clip(y[0], params.initial_crack_m, params.critical_crack_m))
        da_dt = params.cycle_rate_hz * params.crack_growth_rate_m_per_cycle(a)
        return [da_dt]

    def stop_at_critical(_t: float, y: np.ndarray) -> float:
        return params.critical_crack_m - y[0]

    stop_at_critical.terminal = True
    stop_at_critical.direction = -1

    sol = solve_ivp(
        rhs,
        (0.0, duration_s),
        y0=[params.initial_crack_m],
        t_eval=t_eval,
        events=stop_at_critical,
        rtol=1e-7,
        atol=1e-12,
        method="RK45",
    )
    if not sol.success:
        raise RuntimeError(sol.message)

    crack = np.asarray(sol.y[0], dtype=float)
    damage = np.clip(
        (crack - params.initial_crack_m)
        / (params.critical_crack_m - params.initial_crack_m),
        0.0,
        1.0,
    )
    return sol.t, crack, damage
