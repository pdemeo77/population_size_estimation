"""
MinCount Estimator.

Cardinality estimation using k minimum hash values.
Reference: Giroire, 2005 - Order Statistics and Estimating Cardinalities
"""

import numpy as np
from typing import Optional
from ..base import BaseEstimator, EstimationResult


class MinCountEstimator(BaseEstimator):
    """
    MinCount cardinality estimator.
    
    This estimator tracks the k smallest hash values and uses them
    to estimate cardinality. It's more stable than single-minimum approaches.
    
    Algorithm:
        1. Hash all elements
        2. Keep track of k smallest hash values
        3. Estimate based on the k-th smallest value
    
    Formula:
        N̂ = (k - 1) * H / u_k
        
    Where:
        k = number of minimum values to track
        H = hash space size (2^hash_size)
        u_k = k-th smallest hash value
    
    Properties:
        - O(k) memory usage
        - More stable than single-minimum estimators
        - Standard error decreases with larger k
        
    Example:
        >>> estimator = MinCountEstimator(k=256)
        >>> sample = np.array([100, 500, 1000, 5000, 9000])
        >>> result = estimator.estimate(sample)
        >>> print(f"Estimated population: {result.estimate:.0f}")
    """
    
    def __init__(self, k: int = 256, hash_size: int = 32):
        """
        Initialize MinCount estimator.
        
        Args:
            k: Number of minimum hash values to track
            hash_size: Bit width of hash function (must be <= 53 for float precision)
        """
        if hash_size > 53:
            raise ValueError(
                f"hash_size must be <= 53 for float precision, got {hash_size}. "
                "Larger hash spaces cause overflow in estimation."
            )
        if hash_size < 8:
            raise ValueError(
                f"hash_size must be >= 8 for meaningful estimation, got {hash_size}"
            )
        
        self.k = k
        self.hash_size = hash_size
        self._hash_space = 2 ** hash_size
    
    @property
    def name(self) -> str:
        return "MinCount"
    
    def estimate(self, sample: np.ndarray, **kwargs) -> EstimationResult:
        """Estimate population size using MinCount algorithm."""
        self.validate_input(sample)
        
        # Hash all elements
        hash_values = np.array([self._hash(int(x)) for x in sample])
        
        # Find k smallest values
        if len(hash_values) < self.k:
            k_smallest = np.sort(hash_values)
            effective_k = len(hash_values)
        else:
            k_smallest = np.partition(hash_values, self.k)[:self.k]
            effective_k = self.k
        
        # k-th smallest value
        u_k = k_smallest[effective_k - 1]
        
        # MinCount estimate: n = (k - 1) * H / u_k
        if u_k > 0:
            estimate = (effective_k - 1) * self._hash_space / u_k
        else:
            estimate = float('inf')
        
        # Variance estimate
        if effective_k > 2:
            variance = (estimate ** 2) / (effective_k - 2)
        else:
            variance = None
        
        # Compute confidence interval
        if variance is not None:
            std_error = np.sqrt(variance)
            z = 1.96
            ci_lower = max(1, estimate - z * std_error)
            ci_upper = estimate + z * std_error
        else:
            ci_lower = None
            ci_upper = None
        
        return EstimationResult(
            estimate=float(estimate),
            ci_lower=float(ci_lower) if ci_lower else None,
            ci_upper=float(ci_upper) if ci_upper else None,
            variance=float(variance) if variance else None,
            metadata={
                'k': self.k,
                'effective_k': effective_k,
                'u_k': float(u_k),
                'hash_space': self._hash_space
            }
        )
    
    def _hash(self, value: int) -> int:
        """
        Hash function using multiplicative method.
        
        Args:
            value: Value to hash
            
        Returns:
            Hash value in range [0, 2^hash_size)
        """
        # Use a large prime multiplier for good distribution
        PRIME = 0x5851F42D4C957F2D
        h = value * PRIME
        # Mix bits
        h = ((h >> 32) ^ h) * PRIME
        h = ((h >> 32) ^ h) * PRIME  
        h = (h >> 32) ^ h
        return h & (self._hash_space - 1)
