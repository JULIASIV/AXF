"""Physical cantilever and fatigue state models.

This module is intentionally a synthetic laboratory model.  It exposes no
hardware I/O and does not attempt to drive a real actuator or microphone.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class Beam:
    """Uniform, clamped-free rectangular beam parameters (SI units)."""

    length_m: float = 0.12
    width_m: float = 0.012
    thickness_m: float = 0.0015
    density_kg_m3: float = 7_850.0
    modulus_pa: float = 200e9
    damping_ratio: float = 0.006
    excitation_level: float = 0.004

    @property
    def area_m2(self) -> float:
        return self.width_m * self.thickness_m

    @property
    def second_moment_m4(self) -> float:
        return self.width_m * self.thickness_m**3 / 12.0

    @property
    def mass_kg(self) -> float:
        return self.density_kg_m3 * self.area_m2 * self.length_m

    def natural_frequency_hz(self, modulus_pa: float | None = None) -> float:
        """Return the first Euler–Bernoulli cantilever frequency.

        For a uniform clamped-free beam, beta_1 is approximately 1.875104.
        """
        e = self.modulus_pa if modulus_pa is None else modulus_pa
        beta_1 = 1.875104068711961
        return (beta_1**2 / (2.0 * np.pi * self.length_m**2)) * np.sqrt(
            e * self.second_moment_m4 / (self.density_kg_m3 * self.area_m2)
        )

    def ode_trace(
        self,
        duration_s: float,
        sample_rate_hz: float,
        modulus_pa: float | None = None,
        force_hz: float | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Integrate a damped, forced second-order modal ODE.

        The modal equation is x'' + 2*zeta*wn*x' + wn^2*x = F sin(wt).
        The forcing is normalized so that the output is a dimensionless
        displacement-like signal suitable for DSP demonstrations.
        """
        if duration_s <= 0 or sample_rate_hz <= 0:
            raise ValueError("duration_s and sample_rate_hz must be positive")
        e = self.modulus_pa if modulus_pa is None else modulus_pa
        wn = 2.0 * np.pi * self.natural_frequency_hz(e)
        drive_hz = self.natural_frequency_hz(e) if force_hz is None else force_hz
        drive_w = 2.0 * np.pi * drive_hz
        t_eval = np.arange(0.0, duration_s, 1.0 / sample_rate_hz)

        def rhs(t: float, y: np.ndarray) -> list[float]:
            x, xd = y
            xdd = (
                self.excitation_level * np.sin(drive_w * t)
                - 2.0 * self.damping_ratio * wn * xd
                - wn**2 * x
            )
            return [xd, xdd]

        solution = solve_ivp(
            rhs,
            (0.0, duration_s),
            y0=[0.0, 0.0],
            t_eval=t_eval,
            rtol=1e-6,
            atol=1e-9,
            method="RK45",
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        return solution.t, solution.y[0]


def modulus_from_damage(
    initial_modulus_pa: float,
    damage: float,
    maximum_loss: float = 0.20,
) -> float:
    """Map normalized damage to a bounded effective modulus.

    This is a deliberately simple surrogate for a distributed-damage model:
    E_eff = E_0 * (1 - maximum_loss * damage), with clipping to [0, 1].
    """
    if initial_modulus_pa <= 0:
        raise ValueError("initial_modulus_pa must be positive")
    damage = float(np.clip(damage, 0.0, 1.0))
    maximum_loss = float(np.clip(maximum_loss, 0.0, 0.99))
    return initial_modulus_pa * (1.0 - maximum_loss * damage)
