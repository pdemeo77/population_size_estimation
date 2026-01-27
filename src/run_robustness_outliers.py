
import numpy as np
import matplotlib.pyplot as plt
import os
import json
from typing import List, Dict, Tuple
from discrete_estimators import (
    rank_inversion_estimator_discrete,
    spacing_estimator_discrete,
    german_tank_estimator,
    capture_recapture_chapman
)

RESULTS_DIR = "results"
FIGURES_DIR = "figures"
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

def generate_corrupted_population(n: int, p: float, q: float, seed: int = 123) -> np.ndarray:
    """
    Generates a population of N IDs and corrupts a fraction p by multiplying by (1+q).
    p/2 from the top IDs, p/2 from the rest.
    """
    rng = np.random.default_rng(seed)
    pop = np.arange(1, n + 1, dtype=float)
    
    n_corrupt = int(n * p)
    n_top = n_corrupt // 2
    n_rand = n_corrupt - n_top
    
    # Indices to corrupt
    top_indices = np.arange(n - n_top, n)
    remaining_indices = np.arange(0, n - n_top)
    rand_indices = rng.choice(remaining_indices, size=n_rand, replace=False)
    
    all_corrupt_idx = np.concatenate([top_indices, rand_indices])
    
    # Apply corruption: ID * (1 + q)
    pop[all_corrupt_idx] = np.round(pop[all_corrupt_idx] * (1 + q))
    
    return pop

def run_robustness_experiment():
    n_true = 100_000
    p_values = [0.01, 0.05, 0.10]
    q_values = [0.5, 10.0, 100.0]
    ratios = [0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.03, 0.05, 0.07, 0.1, 0.2, 0.4]
    R = 1000 # High resolution for scientific publication
    seed = 42
    
    all_results = {}

    for p in p_values:
        for q in q_values:
            config_key = f"p{p}_q{q}"
            print(f"\nRunning config: p={p}, q={q}")
            
            pop = generate_corrupted_population(n_true, p, q, seed=seed)
            rng = np.random.default_rng(seed)
            
            config_results = {r: {"rank": [], "spacing": [], "gt": [], "cr": []} for r in ratios}
            
            for ratio in ratios:
                m = int(ratio * n_true)
                for _ in range(R):
                    s1 = rng.choice(pop, size=m, replace=False)
                    s2 = rng.choice(pop, size=m, replace=False)
                    
                    config_results[ratio]["rank"].append(rank_inversion_estimator_discrete(s1, m))
                    config_results[ratio]["spacing"].append(spacing_estimator_discrete(s1))
                    config_results[ratio]["gt"].append(german_tank_estimator(s1))
                    config_results[ratio]["cr"].append(capture_recapture_chapman(s1, s2))
            
            # Summarize (Median Relative Error)
            summary = {}
            for ratio in ratios:
                summary[ratio] = {}
                for est in ["rank", "spacing", "gt", "cr"]:
                    vals = np.array(config_results[ratio][est])
                    vals = vals[np.isfinite(vals)]
                    if len(vals) > 0:
                        med = np.median(vals)
                        # Note: we use n_true as the target, even if pop has duplicates/gaps
                        rel_err = abs(med - n_true) / n_true * 100
                        summary[ratio][est] = rel_err
                    else:
                        summary[ratio][est] = np.nan
            
            all_results[config_key] = summary
            
            # Plotting
            plt.figure(figsize=(10, 6))
            x = ratios
            plt.plot(x, [summary[r]["rank"] for r in x], 'o-', label='Rank Inversion')
            plt.plot(x, [summary[r]["spacing"] for r in x], 's-', label='Spacing')
            plt.plot(x, [summary[r]["gt"] for r in x], 'x-', label='German Tank')
            plt.plot(x, [summary[r]["cr"] for r in x], 'd-', label='Capture-Recapture')
            
            plt.xscale('log')
            plt.yscale('log')
            plt.xlabel('Sample Ratio (m/n)')
            plt.ylabel('Median Relative Error (%)')
            plt.title(f'Robustness to Outliers: p={p*100}%, q={q}x')
            plt.grid(True, which="both", ls="-", alpha=0.5)
            plt.legend()
            
            plot_path = os.path.join(FIGURES_DIR, f"robustness_p{int(p*100)}_q{int(q)}.png")
            plt.savefig(plot_path)
            plt.close()
            print(f"Saved plot to {plot_path}")

    # Save JSON
    with open(os.path.join(RESULTS_DIR, "robustness_outliers_results.json"), "w") as f:
        json.dump(all_results, f, indent=2)

if __name__ == "__main__":
    run_robustness_experiment()
