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
    generate_discrete_population,
)

RESULTS_PATH = os.path.join("results", "discrete_pooling_results.json")


def aggregate(values: List[float], method: str = "median", trim_pct: float = 0.1) -> float:
    """Aggregate pooled estimates; supports median and trimmed mean."""
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan")
    if method == "median":
        return float(np.median(arr))
    if method == "trimmed_mean":
        if arr.size == 1:
            return float(arr[0])
        trim = int(arr.size * trim_pct)
        arr_sorted = np.sort(arr)
        trimmed = arr_sorted[trim: arr_sorted.size - trim] if trim > 0 else arr_sorted
        return float(trimmed.mean()) if trimmed.size else float(np.mean(arr_sorted))
    raise ValueError(f"Unknown aggregation method: {method}")


def rel_error(val: float, n_true: int) -> float:
    if not np.isfinite(val):
        return float("nan")
    return abs(val - n_true) / n_true * 100


def summarize(estimates: List[float], n_true: int) -> Dict[str, float]:
    arr = np.asarray(estimates, dtype=float)
    valid = arr[np.isfinite(arr)]
    valid_pct = len(valid) / len(arr) * 100 if len(arr) else 0.0
    if len(valid) == 0:
        return {"median": np.nan, "rel_error": np.nan, "valid_pct": valid_pct}
    med = float(np.median(valid))
    rel_err = float(abs(med - n_true) / n_true * 100)
    return {"median": med, "rel_error": rel_err, "valid_pct": valid_pct}


def summarize_errors(errors: List[float]) -> Dict[str, float]:
    arr = np.asarray(errors, dtype=float)
    valid = arr[np.isfinite(arr)]
    valid_pct = len(valid) / len(arr) * 100 if len(arr) else 0.0
    if len(valid) == 0:
        return {"median": np.nan, "valid_pct": valid_pct}
    return {"median": float(np.median(valid)), "valid_pct": valid_pct}


def run_pooling_config(
    n_true: int,
    m_base: int,
    k: int,
    R: int,
    seed: int | None,
    pooled_aggregator: str,
    trim_pct: float,
):
    rng = np.random.default_rng(seed)
    pop = generate_discrete_population(n_true)
    m_single = m_base * k

    estimators = ["rank", "spacing", "max_obs", "german_tank", "cr"]
    results: Dict[str, Dict[str, Dict[str, float]]] = {"single": {}, "pooled": {}}
    pooled_errors: Dict[str, List[float]] = {name: [] for name in estimators}
    worst_errors: Dict[str, List[float]] = {name: [] for name in estimators}
    best_errors: Dict[str, List[float]] = {name: [] for name in estimators}

    for name in estimators:
        results["single"][name] = []
        results["pooled"][name] = []

    for _ in range(R):
        # Single large sample
        s_single_1 = rng.choice(pop, size=m_single, replace=False)
        s_single_2 = rng.choice(pop, size=m_single, replace=False)

        results["single"]["rank"].append(rank_inversion_estimator_discrete(s_single_1, m_single))
        results["single"]["spacing"].append(spacing_estimator_discrete(s_single_1))
        results["single"]["max_obs"].append(max_observed_estimator(s_single_1, m_single))
        results["single"]["german_tank"].append(german_tank_estimator(s_single_1))
        results["single"]["cr"].append(capture_recapture_chapman(s_single_1, s_single_2))

        # Pooled K subsamples of size m_base
        pooled_estimates = {k: [] for k in estimators}
        for _ in range(k):
            s1 = rng.choice(pop, size=m_base, replace=False)
            s2 = rng.choice(pop, size=m_base, replace=False)
            pooled_estimates["rank"].append(rank_inversion_estimator_discrete(s1, m_base))
            pooled_estimates["spacing"].append(spacing_estimator_discrete(s1))
            pooled_estimates["max_obs"].append(max_observed_estimator(s1, m_base))
            pooled_estimates["german_tank"].append(german_tank_estimator(s1))
            pooled_estimates["cr"].append(capture_recapture_chapman(s1, s2))
        for name in estimators:
            agg_val = aggregate(pooled_estimates[name], method=pooled_aggregator, trim_pct=trim_pct)
            results["pooled"][name].append(agg_val)
            sub_errors = [rel_error(x, n_true) for x in pooled_estimates[name] if np.isfinite(x)]
            if sub_errors:
                worst_errors[name].append(max(sub_errors))
                best_errors[name].append(min(sub_errors))
            else:
                worst_errors[name].append(float("nan"))
                best_errors[name].append(float("nan"))
            pooled_errors[name].append(rel_error(agg_val, n_true))

    summary = {
        "single": {name: summarize(vals, n_true) for name, vals in results["single"].items()},
        "pooled": {name: summarize(vals, n_true) for name, vals in results["pooled"].items()},
        "pooled_errors": {name: summarize_errors(vals) for name, vals in pooled_errors.items()},
        "worst_sub_errors": {name: summarize_errors(vals) for name, vals in worst_errors.items()},
        "best_sub_errors": {name: summarize_errors(vals) for name, vals in best_errors.items()},
        "improvement_vs_worst": {
            name: {
                "median_diff": float(np.nanmedian(worst_errors[name]) - np.nanmedian(pooled_errors[name]))
                if np.isfinite(np.nanmedian(worst_errors[name])) and np.isfinite(np.nanmedian(pooled_errors[name]))
                else np.nan,
                "median_ratio": float(np.nanmedian(pooled_errors[name]) / np.nanmedian(worst_errors[name]))
                if np.isfinite(np.nanmedian(worst_errors[name])) and np.nanmedian(worst_errors[name]) != 0 and np.isfinite(np.nanmedian(pooled_errors[name]))
                else np.nan,
            }
            for name in estimators
        },
        "parameters": {
            "n_true": n_true,
            "m_base": m_base,
            "k": k,
            "m_single": m_single,
            "R": R,
            "seed": seed,
            "pooled_aggregator": pooled_aggregator,
            "trim_pct": trim_pct,
        },
    }
    return summary


def run_all():
    configs = {
        "median_k20_m500": {
            "n_true": 100_000,
            "m_base": 500,
            "k": 20,
            "R": 200,
            "seed": 123,
            "pooled_aggregator": "median",
            "trim_pct": 0.1,
        },
        "trimmedmean_k20_m500": {
            "n_true": 100_000,
            "m_base": 500,
            "k": 20,
            "R": 200,
            "seed": 123,
            "pooled_aggregator": "trimmed_mean",
            "trim_pct": 0.1,
        },
        "trimmedmean_k5_m2000": {
            "n_true": 100_000,
            "m_base": 2000,
            "k": 5,
            "R": 200,
            "seed": 123,
            "pooled_aggregator": "trimmed_mean",
            "trim_pct": 0.1,
        },
        "trimmedmean_k8_m1250": {
            "n_true": 100_000,
            "m_base": 1250,
            "k": 8,
            "R": 200,
            "seed": 123,
            "pooled_aggregator": "trimmed_mean",
            "trim_pct": 0.1,
        },
        "trimmedmean_k10_m1000": {
            "n_true": 100_000,
            "m_base": 1000,
            "k": 10,
            "R": 200,
            "seed": 123,
            "pooled_aggregator": "trimmed_mean",
            "trim_pct": 0.1,
        },
    }

    all_results = {name: run_pooling_config(**params) for name, params in configs.items()}

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n✓ Saved to {RESULTS_PATH}")
    return all_results


if __name__ == "__main__":
    run_all()
