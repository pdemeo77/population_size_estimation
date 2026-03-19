"""
Capture-Recapture Estimator.

Overlap-based estimator using two independent samples, also known as
the Lincoln-Petersen method with Chapman's bias correction.
"""

import numpy as np
from typing import Optional
from ..base import BaseEstimator, EstimationResult


class CaptureRecaptureEstimator(BaseEstimator):
    """
    Capture-Recapture estimator (Chapman's bias-corrected version).
    
    This estimator requires two independent samples from the same population.
    It estimates population size based on the overlap between samples.
    
    Formula (Chapman):
        N̂ = ((m₁ + 1)(m₂ + 1) / (I + 1)) - 1
        
    Where:
        m₁ = size of first sample
        m₂ = size of second sample  
        I = number of elements in both samples (intersection)
    
    Properties:
        - Only uses overlap information, ignores ID magnitude
        - Works well with sparse IDs and gaps
        - Requires two independent samples
        - Less biased than Lincoln-Petersen for small samples
        
    Example:
        >>> estimator = CaptureRecaptureEstimator()
        >>> sample1 = np.array([100, 500, 1000, 5000, 9000])
        >>> sample2 = np.array([500, 2000, 5000, 7000, 9000])
        >>> result = estimator.estimate(sample1, sample2=sample2)
        >>> print(f"Estimated population: {result.estimate:.0f}")
    """
    
    @property
    def name(self) -> str:
        return "Capture-Recapture"
    
    @property
    def requires_two_samples(self) -> bool:
        return True
    
    def estimate(
        self, 
        sample: np.ndarray, 
        sample2: Optional[np.ndarray] = None,
        **kwargs
    ) -> EstimationResult:
        """
        Estimate population size using capture-recapture method.
        
        Args:
            sample: First sample of observed IDs
            sample2: Second independent sample (required)
            **kwargs: Additional parameters (ignored)
            
        Returns:
            EstimationResult with estimate and metadata
        """
        self.validate_input(sample)
        
        if sample2 is None:
            raise ValueError(
                "CaptureRecaptureEstimator requires a second sample. "
                "Pass sample2 as a keyword argument."
            )
        
        self.validate_input(sample2)
        
        m1 = len(sample)
        m2 = len(sample2)
        
        # Compute intersection
        set1 = set(sample.tolist())
        set2 = set(sample2.tolist())
        intersection = len(set1 & set2)
        
        # Handle no overlap case
        if intersection == 0:
            return EstimationResult(
                estimate=float('inf'),
                variance=None,
                metadata={
                    'm1': m1,
                    'm2': m2,
                    'intersection': 0,
                    'warning': 'No overlap between samples - estimate is infinite'
                }
            )
        
        # Chapman's bias-corrected formula
        # N̂ = ((m₁ + 1)(m₂ + 1) / (I + 1)) - 1
        estimate = float(((m1 + 1) * (m2 + 1)) / (intersection + 1) - 1)
        
        # Variance estimate (Chapman's variance formula)
        # Var(N̂) ≈ ((m₁ + 1)(m₂ + 1)(m₁ - I)(m₂ - I)) / ((I + 1)²(I + 2))
        if intersection > 0:
            numerator = (m1 + 1) * (m2 + 1) * (m1 - intersection) * (m2 - intersection)
            denominator = (intersection + 1) ** 2 * (intersection + 2)
            variance = float(numerator / denominator) if denominator > 0 else None
        else:
            variance = None
        
        # Confidence interval
        ci_lower = None
        ci_upper = None
        if variance is not None and variance > 0:
            std_error = np.sqrt(variance)
            z = 1.96  # 95% CI
            ci_lower = max(1, estimate - z * std_error)
            ci_upper = estimate + z * std_error
        
        return EstimationResult(
            estimate=estimate,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            variance=variance,
            metadata={
                'm1': m1,
                'm2': m2,
                'intersection': intersection,
                'overlap_rate': intersection / min(m1, m2) if min(m1, m2) > 0 else 0
            }
        )


def capture_recapture_chapman(
    sample1_ids: np.ndarray, 
    sample2_ids: np.ndarray
) -> float:
    """
    Backward-compatible function for Capture-Recapture estimator.
    
    Args:
        sample1_ids: First sample of observed IDs
        sample2_ids: Second independent sample
        
    Returns:
        Estimated population size (infinity if no overlap)
    """
    estimator = CaptureRecaptureEstimator()
    result = estimator.estimate(sample1_ids, sample2=sample2_ids)
    return result.estimate
