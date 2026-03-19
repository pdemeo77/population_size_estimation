"""
Rank Inversion Estimator.

Robust estimator based on the relationship between sample position and population rank.
"""

import numpy as np
from typing import Optional
from ..base import BaseEstimator, EstimationResult


class RankInversionEstimator(BaseEstimator):
    """
    Rank Inversion estimator for population size.
    
    This estimator exploits the relationship between the position of an element
    in the sorted sample and its rank in the population. It's naturally robust
    to outliers through median aggregation.
    
    Theory:
        For rank r in a sample of size m from population N:
        E[r] ≈ (position/(m+1)) * (N+1)
        
        Therefore: N ≈ r * (m+1) / position - 1
    
    Properties:
        - Robust to outliers (uses median aggregation)
        - Works well with pooled estimates
        - Good for corrupted data
        
    Example:
        >>> estimator = RankInversionEstimator()
        >>> sample = np.array([100, 500, 1000, 5000, 9000])
        >>> result = estimator.estimate(sample)
        >>> print(f"Estimated population: {result.estimate:.0f}")
    """
    
    def __init__(self, trim_frac: float = 0.25):
        """
        Initialize Rank Inversion estimator.
        
        Args:
            trim_frac: Fraction to trim from each end when computing median
        """
        self.trim_frac = trim_frac
    
    @property
    def name(self) -> str:
        return "Rank Inversion"
    
    def estimate(self, sample: np.ndarray, **kwargs) -> EstimationResult:
        """
        Estimate population size using rank inversion method.
        
        Args:
            sample: Array of observed IDs
            **kwargs: Additional parameters
                - m: Sample size (defaults to len(sample))
        """
        self.validate_input(sample)
        
        m = kwargs.get('m', len(sample))
        sample_ranks = sample
        
        if len(sample_ranks) == 0:
            return EstimationResult(
                estimate=float('nan'),
                metadata={'error': 'Empty sample'}
            )
        
        sorted_ranks = np.sort(sample_ranks)
        n_use = len(sorted_ranks)
        
        # Determine trim range
        low = int(np.floor(self.trim_frac * n_use))
        high = int(np.ceil((1 - self.trim_frac) * n_use))
        
        if high <= low:
            low, high = 0, n_use
        
        # Compute individual estimates
        estimates = []
        for i in range(low, high):
            rank = sorted_ranks[i]
            position = i + 1  # 1-indexed position
            # N ≈ rank * (m+1) / position - 1
            n_est = rank * (m + 1) / position - 1
            if n_est > 0:
                estimates.append(n_est)
        
        if len(estimates) == 0:
            return EstimationResult(
                estimate=float('nan'),
                metadata={'error': 'No valid estimates'}
            )
        
        # Use median for robustness
        final_estimate = float(np.median(estimates))
        
        # Estimate variance from spread of individual estimates
        # Note: estimates are correlated (derived from same sample), so we apply
        # a correction factor to avoid underestimating variance
        if len(estimates) > 1:
            # Apply Bessel's correction and account for correlation
            # The effective sample size is reduced due to correlation
            raw_variance = np.var(estimates, ddof=1)
            # Correction factor: estimates from same sample are correlated,
            # so inflate variance to account for reduced effective sample size
            correlation_factor = 1.0 + 0.5 * (len(estimates) - 1) / max(len(estimates), 1)
            variance = float(raw_variance * correlation_factor)
            std_error = np.sqrt(variance)
            z = 1.96  # 95% CI
            ci_lower = max(1, final_estimate - z * std_error)
            ci_upper = final_estimate + z * std_error
        else:
            variance = None
            ci_lower = None
            ci_upper = None
        
        return EstimationResult(
            estimate=final_estimate,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            variance=variance,
            metadata={
                'num_estimates': len(estimates),
                'trim_frac': self.trim_frac,
                'sample_size': m
            }
        )


def rank_inversion_estimator_discrete(
    sample_ranks: np.ndarray,
    m: int,
    trim_frac: float = 0.25
) -> float:
    """
    Backward-compatible function for Rank Inversion estimator.
    
    Args:
        sample_ranks: Ranks of sampled individuals (1 to N)
        m: Sample size
        trim_frac: Fraction to trim from each end
        
    Returns:
        Estimated population size
    """
    estimator = RankInversionEstimator(trim_frac=trim_frac)
    result = estimator.estimate(sample_ranks, m=m)
    return result.estimate
