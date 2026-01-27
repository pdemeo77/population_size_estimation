
import json
import os
from typing import Dict, List
import numpy as np

from discrete_estimators import (
    rank_inversion_estimator_discrete,
    spacing_estimator_discrete,
    max_observed_estimator,
    german_tank_estimator,
    capture_recapture_chapman,
)

RESULTS_PATH = os.path.join("results", "discrete_translation_results.json")

def summarize(estimates: List[float], n_true: int) -> Dict[str, float]:
    arr = np.asarray(estimates, dtype=float)
    valid = arr[np.isfinite(arr)]
    valid_pct = len(valid) / len(arr) * 100 if len(arr) else 0.0
    if len(valid) == 0:
        return {"median": np.nan, "rel_error": np.nan, "valid_pct": valid_pct}
    med = float(np.median(valid))
    rel_err = float(abs(med - n_true) / n_true * 100)
    return {"median": med, "rel_error": rel_err, "valid_pct": valid_pct}

def run_translation_experiment(
    n_true: int = 100_000,
    offset: int = 50_000,
    ratios: List[float] | None = None,
    R: int = 300,
    seed: int | None = 123,
):
    if ratios is None:
        ratios = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2]

    # Population: IDs from offset+1 to offset+n_true
    # e.g. 50,001 to 150,000. Count is still 100,000.
    pop = np.arange(1, n_true + 1) + offset
    print(f"Translation Population: N={n_true}, Offset={offset}, Range=[{pop[0]}, {pop[-1]}]")

    rng = np.random.default_rng(seed)

    results: Dict[str, Dict[str, Dict[str, float]]] = {}

    for ratio in ratios:
        m = int(ratio * n_true)
        estimates = {
            "rank": [],
            "spacing": [],
            "max_obs": [],
            "german_tank": [],
            "cr": [],
        }
        for r in range(R):
            s1 = rng.choice(pop, size=m, replace=False)
            s2 = rng.choice(pop, size=m, replace=False)

            # Note: Rank and German Tank assume 1-based indexing usually.
            # We pass the raw values to see how they fail (or succeed).
            estimates["rank"].append(rank_inversion_estimator_discrete(s1, m))
            estimates["spacing"].append(spacing_estimator_discrete(s1))
            estimates["max_obs"].append(max_observed_estimator(s1, m))
            estimates["german_tank"].append(german_tank_estimator(s1))
            estimates["cr"].append(capture_recapture_chapman(s1, s2))

        results[f"{ratio:.4f}"] = {k: summarize(v, n_true) for k, v in estimates.items()}
        print(f"ratio={ratio:.4f}, m={m}: done")

    payload = {
        "parameters": {
            "n_true": n_true,
            "offset": offset,
            "ratios": ratios,
            "R": R,
            "seed": seed,
        },
        "results": results,
    }

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\n✓ Saved to {RESULTS_PATH}")
    return payload

if __name__ == "__main__":
    run_translation_experiment()
