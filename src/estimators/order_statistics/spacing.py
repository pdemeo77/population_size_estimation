"""
Spacing Estimator.

Translation-invariant estimator based on gaps between consecutive ordered observations.
"""

import numpy as np
from typing import Optional
from ..base import BaseEstimator, EstimationResult


class SpacingEstimator(BaseEstimator):
    """
    Spacing-based estimator for population size.
    
    This estimator is translation-invariant, meaning it works correctly
    even when the IDs have an unknown offset (e.g., starting from 1,000,001
    instead of 1).
    
    Formula:
        N̂ = m × median(gap between consecutive IDs) / ln(2)
        
    The division by ln(2) corrects for the median of an exponential distribution.
    
    Properties:
        - Translation-invariant (works with unknown offset)
        - Robust to moderate outliers through median
        - Works best with reasonably dense samples
        
    Example:
        >>> estimator = SpacingEstimator()
        >>> sample = np.array([100, 500, 1000, 5000, 9000])
        >>> result = estimator.estimate(sample)
        >>> print(f"Estimated population: {result.estimate:.0f}")
    """
    
    def __init__(self, trim_frac: float = 0.25):
        """
        Initialize Spacing estimator.
        
        Args:
            trim_frac: Fraction to trim from each end when computing median
        """
        self.trim_frac = trim_frac
    
    @property
    def name(self) -> str:
        return "Spacing"
    
    def estimate(self, sample: np.ndarray, **kwargs) -> EstimationResult:
        """Estimate population size using spacing method."""
        self.validate_input(sample)
        
        if len(sample) < 2:
            return EstimationResult(
                estimate=float('nan'),
                metadata={'error': 'Need at least 2 samples'}
            )
        
        sorted_sample = np.sort(sample)
        m = len(sorted_sample)
        
        # Compute spacings between consecutive elements
        spacings = sorted_sample[1:] - sorted_sample[:-1]
        
        # Trim extremes if requested
        if self.trim_frac > 0 and len(spacings) > 4:
            low = int(np.floor(self.trim_frac * len(spacings)))
            high = int(np.ceil((1 - self.trim_frac) * len(spacings)))
            if high > low:
                spacings = spacings[low:high]
        
        # Median spacing, corrected for exponential distribution
        median_spacing = np.median(spacings)
        avg_spacing = median_spacing / np.log(2)
        
        # Estimate: N ≈ m × average_spacing
        estimate = float(m * avg_spacing) if avg_spacing > 0 else float('nan')
        
        # Variance estimate (approximate)
        # Based on variance of spacing estimator
        if not np.isnan(estimate) and len(spacings) > 1:
            spacing_var = np.var(spacings)
            variance = float((m ** 2) * spacing_var / (np.log(2) ** 2) / len(spacings))
        else:
            variance = None
        
        return EstimationResult(
            estimate=estimate,
            variance=variance,
            metadata={
                'median_spacing': float(median_spacing),
                'avg_spacing': float(avg_spacing),
                'sample_size': m,
                'trim_frac': self.trim_frac
            }
        )


def spacing_estimator_discrete(sample: np.ndarray, trim_frac: float = 0.25) -> float:
    """
    Backward-compatible function for Spacing estimator.
    
    Args:
        sample: Array of observed IDs
        trim_frac: Fraction to trim from each end
        
    Returns:
        Estimated population size
    """
    estimator = SpacingEstimator(trim_frac=trim_frac)
    result = estimator.estimate(sample)
    return result.estimate
