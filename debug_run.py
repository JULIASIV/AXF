from phonon_key.simulation import run_simulation

result = run_simulation("101100", bit_period_s=0.5)
print("samples", len(result.time_s))
print("duration", result.time_s[-1] if len(result.time_s) else None)
print("damage", result.damage[0] if len(result.damage) else None, result.damage[-1] if len(result.damage) else None)
print("decoded", repr(result.decoded_bits))
print("estimates", result.estimated_frequencies_hz)
