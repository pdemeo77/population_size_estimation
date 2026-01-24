"""
Stimatori della Dimensione della Popolazione - VERSIONE DISCRETA
Modificato per lavorare con popolazioni finite discrete dove gli individui sono distinguibili.
"""

import numpy as np
import scipy.stats as stats
import argparse
import json
import os
from datetime import datetime
from typing import Tuple, List, Optional

# Struttura delle cartelle
RESULTS_DIR = "results"
FIGURES_DIR = "figures"

# Assicura che le cartelle esistano
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# -----------------------------
# 1. STIMATORI PER POPOLAZIONI DISCRETE
# -----------------------------

def rank_inversion_estimator_discrete(
    sample_ranks: np.ndarray,
    m: int,
    trim_frac: float = 0.25
) -> float:
    """
    Stimatore basato sull'inversione di rango per popolazioni discrete.
    
    Argomenti:
        sample_ranks: Ranghi degli individui campionati (da 1 a N)
        m: Dimensione del campione
        trim_frac: Frazione da troncare ad ogni estremità
    
    Teoria: Per il rango r in un campione di dimensione m da una popolazione N,
    E[r] ≈ (r/(m+1)) * (N+1), quindi N ≈ r*(m+1)/posizione_rango - 1
    """
    if len(sample_ranks) == 0:
        return np.nan
    
    sorted_ranks = np.sort(sample_ranks)
    n_use = len(sorted_ranks)
    low = int(np.floor(trim_frac * n_use))
    high = int(np.ceil((1 - trim_frac) * n_use))
    
    if high <= low:
        low, high = 0, n_use
    
    estimates = []
    for i in range(low, high):
        rank = sorted_ranks[i]
        position = i + 1  # Posizione nel campione ordinato (1-indexed)
        # Posizione attesa: posizione/(m+1) ≈ rango/(N+1)
        n_est = rank * (m + 1) / position - 1
        if n_est > 0:
            estimates.append(n_est)
    
    return np.median(estimates) if len(estimates) > 0 else np.nan


def spacing_estimator_discrete(
    sample_ranks: np.ndarray,
    trim_frac: float = 0.25
) -> float:
    """
    Stimatore basato sulla spaziatura per popolazioni discrete.
    
    Teoria: La spaziatura media tra statistiche d'ordine consecutive
    dovrebbe essere approssimativamente N/m per un campionamento uniforme.
    """
    if len(sample_ranks) < 2:
        return np.nan
    
    sorted_ranks = np.sort(sample_ranks)
    m = len(sorted_ranks)
    
    low = int(np.floor(trim_frac * m))
    high = int(np.ceil((1 - trim_frac) * m)) - 1
    
    if high <= low:
        low, high = 0, m - 1
    
    if high < 0:
        return np.nan
    
    spacings = sorted_ranks[low+1:high+1] - sorted_ranks[low:high]
    # Correzione: La mediana di un esponenziale è ln(2) * media.
    # Dividiamo per ln(2) per stimare la spaziatura media.
    avg_spacing = np.median(spacings) / np.log(2)
    
    # N ≈ m * spaziatura_media
    return m * avg_spacing if avg_spacing > 0 else np.nan


def capture_recapture_chapman(sample1_ids: np.ndarray, sample2_ids: np.ndarray) -> float:
    """Stimatore di Chapman per cattura-ricattura."""
    if len(sample1_ids) == 0 or len(sample2_ids) == 0:
        return np.nan
    
    set1, set2 = set(sample1_ids.tolist()), set(sample2_ids.tolist())
    overlap = len(set1 & set2)
    
    if overlap == 0:
        return np.inf
    
    m1, m2 = len(sample1_ids), len(sample2_ids)
    # Formula di Chapman (meno distorta di Lincoln-Petersen per piccoli campioni)
    n_est = ((m1 + 1) * (m2 + 1)) / (overlap + 1) - 1
    
    return n_est if np.isfinite(n_est) else np.nan


def max_observed_estimator(sample_ranks: np.ndarray, m: int) -> float:
    """
    Semplice stimatore basato sul massimo rango osservato.
    
    Teoria: max(campione) ≈ m/(m+1) * N
    Quindi N ≈ max(campione) * (m+1)/m
    """
    if len(sample_ranks) == 0:
        return np.nan
    
    max_rank = np.max(sample_ranks)
    return max_rank * (m + 1) / m


def german_tank_estimator(sample_ranks: np.ndarray) -> float:
    """
    Stimatore del Problema dei Carri Armati Tedeschi (stimatore di frequenza).
    
    Stimatore corretto a varianza minima (MVUE):
    N ≈ max(campione) + max(campione)/m - 1
    """
    if len(sample_ranks) == 0:
        return np.nan
    
    m = len(sample_ranks)
    max_rank = np.max(sample_ranks)
    return max_rank + max_rank / m - 1


# -----------------------------
# 2. GENERAZIONE DEI DATI
# -----------------------------

def generate_discrete_population(n: int, distribution: str = "uniform", **kwargs) -> np.ndarray:
    """
    Genera una popolazione discreta di n individui con ID unici (da 1 a n).
    
    Argomenti:
        n: Dimensione della popolazione
        distribution: "uniform" o "pareto"
    
    Ritorna:
        Array di n ID unici: [1, 2, 3, ..., n]
    """
    return np.arange(1, n + 1)


def generate_pareto_weighted_population(n: int, alpha: float = 1.5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Genera una popolazione discreta dove gli ID hanno pesi distribuiti secondo Pareto.
    
    Molti sistemi di ID reali mostrano un comportamento tipo Pareto:
    - Alcuni ID (numeri bassi) sono molto comuni
    - La maggior parte degli ID (numeri alti) sono visti raramente
    
    Argomenti:
        n: Numero totale di ID unici (dimensione della popolazione)
        alpha: Parametro di forma di Pareto (più basso = più sbilanciato)
                alpha=1.5 significa una distribuzione ~80-20
    
    Ritorna:
        Tupla [ID, pesi] dove i pesi seguono la distribuzione di Pareto
    """
    ids = np.arange(1, n + 1)
    
    # Genera pesi Pareto: P(x) ~ x^(-alpha)
    weights = 1.0 / (ids ** alpha)
    
    # Normalizza a probabilità
    weights = weights / np.sum(weights)
    
    return ids, weights


def sample_from_population(population: np.ndarray, m: int, replace: bool = False, weights: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Campiona m individui dalla popolazione.
    
    Argomenti:
        population: Array di ID degli individui
        m: Dimensione del campione
        replace: Se campionare con reinserimento
        weights: Pesi probabilistici opzionali per ogni ID
    
    Ritorna:
        Array di ID campionati
    """
    if m > len(population) and not replace:
        raise ValueError(f"Impossibile campionare {m} dalla popolazione di {len(population)} senza reinserimento")
    
    return np.random.choice(population, size=m, replace=replace, p=weights)


# -----------------------------
# 3. INTERVALLI DI CONFIDENZA
# -----------------------------

def cimad_imp_interval(estimates: np.ndarray, alpha: float = 0.05) -> Tuple[float, float]:
    """Intervallo di confidenza robusto migliorato per la mediana usando l'approssimazione binomiale."""
    R = len(estimates)
    if R == 0:
        return np.nan, np.nan
    
    med = np.median(estimates)
    z = stats.norm.ppf(1 - alpha / 2)
    # Calcola l'indice k basato sulla statistica d'ordine per la mediana
    k = int(np.floor((R + 1) / 2 - np.sqrt(R / 4) * z))
    k = max(1, min(k, R - 1))
    p = k / R
    deviations = np.abs(estimates - med)
    q_imp = np.quantile(deviations, p)
    return med - q_imp, med + q_imp


# -----------------------------
# 4. ESPERIMENTI
# -----------------------------

def run_discrete_experiment(
    n_true: int = 100_000,
    m: int = 1_000,
    R: int = 1000,
    seed: Optional[int] = None,
    save_results: bool = True
):
    """
    Esegue un esperimento con una popolazione veramente discreta.
    """
    if seed is not None:
        np.random.seed(seed)
    
    print("=" * 70)
    print("STIMA DELLA DIMENSIONE DELLA POPOLAZIONE DISCRETA")
    print("=" * 70)
    print(f"Dimensione vera della popolazione (N): {n_true:,}")
    print(f"Dimensione del campione (m): {m:,}")
    print(f"Rapporto di campionamento (m/n): {m/n_true:.4f}")
    print(f"Ripetizioni (R): {R:,}")
    print("=" * 70)
    
    # Genera popolazione: individui numerati da 1 a N
    population = generate_discrete_population(n_true)
    print(f"\nPopolazione: {len(population):,} individui con ID da {population[0]} a {population[-1]}")
    
    # Contenitori per le stime
    estimators = {
        'rank_inversion': [],
        'spacing': [],
        'max_observed': [],
        'german_tank': [],
        'cr': []
    }
    
    print(f"\nEsecuzione di {R:,} simulazioni...")
    for r in range(R):
        if (r + 1) % 100 == 0:
            print(f"  Progresso: {r+1:,}/{R:,}", end='\r')
        
        # Campiona due campioni indipendenti (per cattura-ricattura)
        sample1 = sample_from_population(population, m, replace=False)
        sample2 = sample_from_population(population, m, replace=False)
        
        # Esegue gli stimatori
        estimators['rank_inversion'].append(rank_inversion_estimator_discrete(sample1, m))
        estimators['spacing'].append(spacing_estimator_discrete(sample1))
        estimators['max_observed'].append(max_observed_estimator(sample1, m))
        estimators['german_tank'].append(german_tank_estimator(sample1))
        estimators['cr'].append(capture_recapture_chapman(sample1, sample2))
    
    print(f"  Progresso: {R:,}/{R:,} - Completato!\n")
    
    # Calcola e visualizza i risultati
    print("=" * 70)
    print("RISULTATI")
    print("=" * 70)
    
    results = {}
    for name, est_list in estimators.items():
        est_arr = np.array(est_list)
        valid_mask = np.isfinite(est_arr)
        
        if np.sum(valid_mask) == 0:
            print(f"{name:>20}: Nessuna stima valida")
            continue
        
        est_valid = est_arr[valid_mask]
        med = np.median(est_valid)
        mean = np.mean(est_valid)
        mad = np.median(np.abs(est_valid - med))
        std = np.std(est_valid)
        rel_err = np.abs(med - n_true) / n_true * 100
        bias = mean - n_true
        
        ci_low, ci_up = cimad_imp_interval(est_valid)
        coverage = ci_low <= n_true <= ci_up
        
        results[name] = {
            'median': float(med),
            'mean': float(mean),
            'bias': float(bias),
            'rel_error': float(rel_err),
            'mad': float(mad),
            'std': float(std),
            'coverage': bool(coverage),
            'valid_pct': float(np.sum(valid_mask) / len(est_arr) * 100)
        }
        
        print(f"{name:>20}: mediana={med:>12,.0f}, media={mean:>12,.0f}, err_rel={rel_err:>6.2f}%, bias={bias:>10,.0f}, copertura={coverage}")
    
    print("=" * 70)
    
    # Salva i risultati se richiesto
    if save_results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(RESULTS_DIR, f"discrete_experiment_n{n_true}_m{m}_R{R}_{timestamp}.json")
        with open(filename, 'w') as f:
            json.dump({
                'parameters': {
                    'n_true': n_true,
                    'm': m,
                    'R': R,
                    'seed': seed,
                    'ratio': m / n_true
                },
                'results': results
            }, f, indent=2)
        print(f"\n✓ Risultati salvati in: {filename}")
    
    return results


def run_mn_ratio_analysis_discrete(
    n_true: int = 100_000,
    ratios: Optional[List[float]] = None,
    R: int = 100,
    seed: Optional[int] = None,
    save_results: bool = True
):
    """Analyze performance across different m/n ratios."""
    if ratios is None:
        ratios = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2]
    
    if seed is not None:
        np.random.seed(seed)
    
    print("=" * 70)
    print("M/N RATIO ANALYSIS - DISCRETE POPULATIONS")
    print("=" * 70)
    print(f"True population size: {n_true:,}")
    print(f"Testing {len(ratios)} different ratios")
    print(f"Repetitions per ratio: {R:,}")
    print("=" * 70)
    
    population = generate_discrete_population(n_true)
    
    results_by_ratio = {}
    
    for ratio in ratios:
        m = int(ratio * n_true)
        print(f"\nTesting m/n = {ratio:.4f} (m = {m:,})...")
        
        estimators = {
            'rank_inversion': [],
            'spacing': [],
            'max_observed': [],
            'german_tank': [],
            'cr': []
        }
        
        for r in range(R):
            sample1 = sample_from_population(population, m, replace=False)
            sample2 = sample_from_population(population, m, replace=False)
            
            estimators['rank_inversion'].append(rank_inversion_estimator_discrete(sample1, m))
            estimators['spacing'].append(spacing_estimator_discrete(sample1))
            estimators['max_observed'].append(max_observed_estimator(sample1, m))
            estimators['german_tank'].append(german_tank_estimator(sample1))
            estimators['cr'].append(capture_recapture_chapman(sample1, sample2))
        
        ratio_results = {}
        for name, est_list in estimators.items():
            est_arr = np.array(est_list)
            valid_mask = np.isfinite(est_arr)
            
            if np.sum(valid_mask) > 0:
                est_valid = est_arr[valid_mask]
                med = np.median(est_valid)
                rel_err = np.abs(med - n_true) / n_true * 100
            else:
                med = np.nan
                rel_err = np.nan
            
            ratio_results[name] = {'median': med, 'rel_error': rel_err}
            print(f"  {name:>20}: median={med:>12,.0f}, rel_err={rel_err:>6.2f}%")
        
        results_by_ratio[ratio] = ratio_results
    
    # Save results if requested
    if save_results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(RESULTS_DIR, f"mn_ratio_analysis_n{n_true}_R{R}_{timestamp}.json")
        with open(filename, 'w') as f:
            json.dump({
                'parameters': {
                    'n_true': n_true,
                    'ratios': ratios,
                    'R': R,
                    'seed': seed
                },
                'results_by_ratio': results_by_ratio
            }, f, indent=2, default=str)
        print(f"\n✓ Results saved to: {filename}")
    
    return results_by_ratio


# -----------------------------
# 5. MAIN
# -----------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discrete Population Size Estimation")
    parser.add_argument("--n-true", type=int, default=100_000, help="True population size")
    parser.add_argument("--m", type=int, default=1_000, help="Sample size")
    parser.add_argument("--repetitions", type=int, default=1000, help="Number of repetitions")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--analysis", action="store_true", help="Run m/n ratio analysis")
    parser.add_argument("--no-save", action="store_true", help="Don't save results automatically")
    
    args = parser.parse_args()
    
    save_results = not args.no_save
    
    if args.analysis:
        results = run_mn_ratio_analysis_discrete(
            n_true=args.n_true,
            R=args.repetitions,
            seed=args.seed,
            save_results=save_results
        )
    else:
        results = run_discrete_experiment(
            n_true=args.n_true,
            m=args.m,
            R=args.repetitions,
            seed=args.seed,
            save_results=save_results
        )
    
    print("\n✓ Experiment complete!")
