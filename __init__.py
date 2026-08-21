"""Benign fatigue/resonance telemetry laboratory framework."""

from .beam import Beam, modulus_from_damage
from .fatigue import ParisParameters, paris_crack_trajectory
from .simulation import SimulationResult, run_simulation

__all__ = [
    "Beam",
    "ParisParameters",
    "SimulationResult",
    "modulus_from_damage",
    "paris_crack_trajectory",
    "run_simulation",
]
