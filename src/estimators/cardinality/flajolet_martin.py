"""
Flajolet-Martin Estimator.

Probabilistic cardinality estimation using bit pattern observation.
Reference: Flajolet & Martin, 1985 - Probabilistic Counting
"""

import numpy as np
from typing import Optional, List
from ..base import BaseEstimator, EstimationResult


class FlajoletMartinEstimator(BaseEstimator):
    """
    Flajolet-Martin cardinality estimator.
    
    This estimator uses hash-based bit patterns to estimate cardinality.
    It's particularly useful for streaming data and uses constant memory.
    
    Algorithm:
        1. Hash each element to a binary string
        2. Find the position of the leftmost 1-bit (ρ) for each hash
        3. The maximum ρ across all elements estimates log₂(n)
        4. Use multiple hash functions and average for better accuracy
    
    Formula:
        N̂ ≈ 2^M / φ
        
    Where:
        M = mean of maximum ρ values across hash functions
        φ ≈ 0.77351 (correction constant)
    
    Properties:
        - O(1) memory usage per hash function
        - Works with any hashable data type
        - Accuracy improves with more hash functions
        - Standard error ≈ 0.78 / sqrt(k) for k hash functions
        
    Example:
        >>> estimator = FlajoletMartinEstimator(num_hash_functions=64)
        >>> sample = np.array([100, 500, 1000, 5000, 9000])
        >>> result = estimator.estimate(sample)
        >>> print(f"Estimated population: {result.estimate:.0f}")
        
    References:
        - Flajolet & Martin, 1985 - "Probabilistic Counting Algorithms 
          for Data Base Applications"
    """
    
    # Correction constant φ
    PHI = 0.77351
    
    def __init__(self, num_hash_functions: int = 64, seed: int = 42):
        """
        Initialize Flajolet-Martin estimator.
        
        Args:
            num_hash_functions: Number of hash functions for averaging
            seed: Random seed for hash function generation
        """
        self.num_hash_functions = num_hash_functions
        self.seed = seed
        self._hash_seeds = self._generate_hash_seeds()
    
    def _generate_hash_seeds(self) -> np.ndarray:
        """Generate seeds for multiple hash functions."""
        rng = np.random.RandomState(self.seed)
        return rng.randint(0, 2**31 - 1, size=self.num_hash_functions)
    
    @property
    def name(self) -> str:
        return "Flajolet-Martin"
    
    def estimate(self, sample: np.ndarray, **kwargs) -> EstimationResult:
        """
        Estimate population size using Flajolet-Martin algorithm.
        
        Args:
            sample: Array of observed IDs
            **kwargs: Additional parameters (ignored)
            
        Returns:
            EstimationResult with estimate and variance
        """
        self.validate_input(sample)
        
        # For each hash function, find max rho
        max_rhos = []
        for seed in self._hash_seeds:
            rho_values = [self._rho(self._hash(int(x), seed)) for x in sample]
            max_rhos.append(max(rho_values))
        
        max_rhos = np.array(max_rhos)
        
        # Average across hash functions
        mean_rho = np.mean(max_rhos)
        
        # FM estimate: n ≈ 2^mean_rho / phi
        estimate = (2 ** mean_rho) / self.PHI
        
        # Variance estimation
        # Standard error ≈ 0.78 / sqrt(k)
        variance = (0.78 / np.sqrt(self.num_hash_functions)) ** 2 * (estimate ** 2)
        std_error = np.sqrt(variance)
        
        # 95% confidence interval
        z = 1.96
        ci_lower = max(1, estimate - z * std_error)
        ci_upper = estimate + z * std_error
        
        return EstimationResult(
            estimate=float(estimate),
            ci_lower=float(ci_lower),
            ci_upper=float(ci_upper),
            variance=float(variance),
            metadata={
                'num_hash_functions': self.num_hash_functions,
                'mean_rho': float(mean_rho),
                'max_rhos': [float(x) for x in max_rhos[:5]]  # Store first 5 for debugging
            }
        )
    
    def _hash(self, value: int, seed: int) -> int:
        """
        MurmurHash3-style hash function.
        
        Args:
            value: Value to hash
            seed: Hash function seed
            
        Returns:
            32-bit hash value
        """
        # Simple but effective hash using multiplication and XOR
        h = seed ^ value
        h = ((h >> 16) ^ h) * 0x85ebca6b
        h = ((h >> 13) ^ h) * 0xc2b2ae35
        h = (h >> 16) ^ h
        return h & 0xFFFFFFFF  # Keep only 32 bits
    
    def _rho(self, hash_value: int) -> int:
        """
        Find position of leftmost 1-bit (1-indexed).
        
        This is the position of the least significant 1-bit when viewing
        the hash as a binary string from right to left.
        
        Args:
            hash_value: Hash value to analyze
            
        Returns:
            Position of leftmost 1-bit (0 if hash is 0)
        """
        # Convert to Python int to ensure bit_length() is available
        hash_value = int(hash_value)
        if hash_value == 0:
            return 0
        # Find position of least significant 1-bit
        return (hash_value & -hash_value).bit_length()
