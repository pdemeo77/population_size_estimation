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

RESULTS_PATH = os.path.join("results", "discrete_sparse_results.json")


def generate_sparse_ids(n_base: int, gap_rate: float, seed: int | None = None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    keep_mask = rng.uniform(size=n_base) > gap_rate
    ids = np.nonzero(keep_mask)[0] + 1  # IDs start at 1
    return ids


def summarize(estimates: List[float], n_true: int) -> Dict[str, float]:
    arr = np.asarray(estimates, dtype=float)
    valid = arr[np.isfinite(arr)]
    valid_pct = len(valid) / len(arr) * 100 if len(arr) else 0.0
    if len(valid) == 0:
        return {"median": np.nan, "rel_error": np.nan, "valid_pct": valid_pct}
    med = float(np.median(valid))
    rel_err = float(abs(med - n_true) / n_true * 100)
    return {"median": med, "rel_error": rel_err, "valid_pct": valid_pct}


def run_sparse_experiment(
    n_base: int = 100_000,
    gap_rate: float = 0.3,
    ratios: List[float] | None = None,
    R: int = 300,
    seed: int | None = 123,
):
    if ratios is None:
        ratios = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2]

    pop = generate_sparse_ids(n_base, gap_rate, seed)
    n_true = len(pop)
    print(f"Sparse population generated: base_n={n_base}, gap_rate={gap_rate}, n_true={n_true}")

    rng = np.random.default_rng(seed + 1 if seed is not None else None)

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

            estimates["rank"].append(rank_inversion_estimator_discrete(s1, m))
            estimates["spacing"].append(spacing_estimator_discrete(s1))
            estimates["max_obs"].append(max_observed_estimator(s1, m))
            estimates["german_tank"].append(german_tank_estimator(s1))
            estimates["cr"].append(capture_recapture_chapman(s1, s2))

        results[f"{ratio:.4f}"] = {k: summarize(v, n_true) for k, v in estimates.items()}
        print(f"ratio={ratio:.4f}, m={m}: done")

    payload = {
        "parameters": {
            "n_base": n_base,
            "gap_rate": gap_rate,
            "n_true": n_true,
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
    run_sparse_experiment()
