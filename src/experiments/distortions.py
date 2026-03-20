"""
Distortion functions for population size estimation experiments.

This module provides functions to inject various distortions
into the node ID data to test estimator robustness
under different conditions.
"""

from typing import Optional

import numpy as np


def add_offset(ids: np.ndarray, offset: int) -> np.ndarray:
    """
    Add a constant offset to all node IDs.
    
    This distortion simulates the case where the true starting
    ID is unknown (e.g., IDs starting from 1,000,001 instead of 1).
    
    Args:
        ids: Array of node IDs
        offset: Constant to add to each ID
        
    Returns:
        Array of offset node IDs
        
    Example:
        >>> ids = np.array([1, 2, 3, 4, 5])
        >>> add_offset(ids, 1000000)  # IDs now start at 1,000,001
        array([1000001, 1000002, 1000003, 1000004, 1000005])
    """
    return ids + offset


def add_gaps(ids: np.ndarray, gap_fraction: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Randomly remove a fraction of node IDs to create gaps.
    
    This simulates the case where the ID space has holes
    (e.g., due to deleted records or sparse sampling).
    
    Args:
        ids: Array of node IDs
        gap_fraction: Fraction of IDs to remove (0.0 to 1.0)
        seed: Random seed for reproducibility
        
    Returns:
        Array of node IDs with gaps
        
    Example:
        >>> ids = np.arange(1, 101)
        >>> add_gaps(ids, 0.2, seed=42)  # Remove 20% of IDs
        array([1, 2, ..., 80])  # 80 IDs remaining
    """
    rng = np.random.default_rng(seed)
    n_original = len(ids)
    n_remove = int(n_original * gap_fraction)
    
    if n_remove == 0:
        return ids.copy()
    
    # Randomly select indices to keep
    n_keep = n_original - n_remove
    indices_to_keep = rng.choice(
        n_original, size=n_keep, replace=False
    )
    
    # Return only the kept IDs
    return ids[indices_to_keep]


def add_multiplicative_noise(
    ids: np.ndarray, 
    q: float, 
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Apply multiplicative noise to node IDs.
    
    This simulates corruption or measurement errors in the IDs.
    Each ID is multiplied by (1 + q), where q is drawn from
    a normal distribution centered at 0.
    
    Args:
        ids: Array of node IDs
        q: Noise parameter (small values create small noise)
        seed: Random seed for reproducibility
        
    Returns:
        Array of corrupted node IDs
        
    Example:
        >>> ids = np.array([100, 200, 300, 400, 500])
        >>> add_multiplicative_noise(ids, 0.1, seed=42)
        # IDs multiplied by ~1.1x
        array([110, 220, 330, 440, 550])  # approximately
    """
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, q, size=len(ids))
    return ids * (1 + noise)


def apply_zipf_bias(
    ids: np.ndarray, 
    alpha: float, 
    sample_size: Optional[int] = None,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Apply Zipf-distributed sampling bias.
    
    This simulates popularity bias where some items are more likely
    to be sampled than others. The sampling is done with replacement,
    so the same items can appear multiple times.
    
    Args:
        ids: Array of node IDs
        alpha: Zipf distribution parameter (higher = more bias)
        sample_size: Number of samples to draw (default: same as input size)
        seed: Random seed for reproducibility
        
    Returns:
        Array of sampled node IDs (with duplicates)
        
    Example:
        >>> ids = np.arange(1, 101)
        >>> biased_sample = apply_zipf_bias(ids, alpha=1.5, sample_size=50, seed=42)
        >>> print(f"Sample size: {len(biased_sample)}")  # May be < 50
    """
    rng = np.random.default_rng(seed)
    n = len(ids)
    
    if sample_size is None:
        sample_size = n
    
    # Compute Zipf weights (1/rank^alpha)
    ranks = np.arange(1, n + 1)
    weights = 1.0 / (ranks ** alpha)
    weights = weights / weights.sum()  # Normalize
    
    # Sample with replacement according to weights
    indices = rng.choice(n, size=sample_size, replace=True, p=weights)
    
    return ids[indices]


# =============================================================================
# Convenience functions to apply multiple distortions
# ============================================================================

def apply_distortions(
    ids: np.ndarray,
    offset: int = 0,
    gap_fraction: float = 0.0,
    multiplicative_noise: float = 0.0,
    zipf_alpha: Optional[float] = None,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Apply multiple distortions to sequence.
    
    This is a convenience function that chains multiple distortion
    functions. Only non-zero parameters are applied.
    
    Args:
        ids: Array of node IDs
        offset: Constant to add to each ID (default: 0)
        gap_fraction: Fraction of IDs to remove (default: 0)
        multiplicative_noise: Noise parameter (default: 0)
        zipf_alpha: Zipf bias parameter (default: None)
        seed: Random seed for reproducibility
        
    Returns:
        Array of distorted node IDs
        
    Example:
        >>> ids = np.arange(1, 101)
        >>> distorted = apply_distortions(
        ...     ids, 
        ...     offset=100000, 
        ...     gap_fraction=0.1,
        ...     seed=42
        ... )
        >>> print(f"Original: {len(ids)}, Distorted: {len(distorted)}")
    """
    result = ids.copy()
    
    # Apply offset
    if offset != 0:
        result = add_offset(result, offset)
    
    # Apply gaps
    if gap_fraction > 0:
        result = add_gaps(result, gap_fraction, seed=seed)
    
    # Apply multiplicative noise
    if multiplicative_noise > 0:
        result = add_multiplicative_noise(result, multiplicative_noise, seed=seed)
    
    # Apply Zipf bias
    if zipf_alpha is not None:
        result = apply_zipf_bias(result, zipf_alpha, seed=seed)
    
    return result
