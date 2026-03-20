"""
German Tank Estimator.

The classic frequency-based estimator from WWII, also known as the 
minimum-variance unbiased estimator (MVUE) for sequential IDs.
"""

import numpy as np
from typing import Optional
from ..base import BaseEstimator, EstimationResult


class GermanTankEstimator(BaseEstimator):
    """
    German Tank Problem estimator (MVUE for sequential IDs).
    
    Formula: N_hat = max(sample) + max(sample)/m - 1
    
    Properties:
        - Unbiased for sequential IDs starting at 1
        - Fails when there is an unknown offset
        - Very sensitive to outliers
    """
    
    @property
    def name(self) -> str:
        return "German Tank"
    
    def estimate(self, sample: np.ndarray, **kwargs) -> EstimationResult:
        """Estimate population size using German Tank formula."""
        self.validate_input(sample)
        
        m = len(sample)
        max_obs = np.max(sample)
        
        # German Tank MVUE formula
        estimate = float(max_obs + max_obs / m - 1)
        
        # Variance from order statistics
        # Cast to float before multiplication to avoid integer overflow on large IDs
        if max_obs > m and m > 1:
            variance = float((float(max_obs) * (max_obs - m)) / (float(m) * (m + 1)))
            std_error = np.sqrt(variance)
            z = 1.96  # 95% CI
            ci_lower = max(1, estimate - z * std_error)
            ci_upper = estimate + z * std_error
        else:
            variance = None
            ci_lower = None
            ci_upper = None
        
        return EstimationResult(
            estimate=estimate,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            variance=variance,
            metadata={
                'max_observed': int(max_obs),
                'sample_size': m
            }
        )


def german_tank_estimator(sample: np.ndarray) -> float:
    """
    Backward-compatible function for German Tank estimator.
    
    Args:
        sample: Array of observed sequential IDs
        
    Returns:
        Estimated population size
    """
    estimator = GermanTankEstimator()
    result = estimator.estimate(sample)
    return result.estimate
