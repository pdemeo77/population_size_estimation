"""
Uniform random sampler for population size estimation.

This module implements simple random sampling without replacement.
"""

from typing import Optional

import numpy as np

from .base import BaseSampler


class UniformSampler(BaseSampler):
    """
    Uniform random sampler without replacement.
    
    This is the baseline sampling method where each element has equal
    probability of being selected. It uses simple random sampling without
    replacement, meaning each element can only be selected once.
    
    Properties:
        - Each element has equal selection probability
        - No element can be selected more than once
        - Statistically unbiased representation of the population
        
    Example:
        >>> sampler = UniformSampler()
        >>> ids = np.arange(1, 100001)  # Population of 100,000
        >>> sample = sampler.sample(ids, fraction=0.01, seed=42)
        >>> print(f"Sampled {len(sample)} elements")
    """
    
    @property
    def name(self) -> str:
        """Return sampler name."""
        return "Uniform"
    
    def sample(
        self, 
        ids: np.ndarray, 
        fraction: float, 
        seed: Optional[int] = None
    ) -> np.ndarray:
        """
        Sample a fraction of the population uniformly at random.
        
        Args:
            ids: Array of node IDs to sample from
            fraction: Fraction of population to sample (0.0 to 1.0)
            seed: Random seed for reproducibility
            
        Returns:
            Array of sampled node IDs
            
        Raises:
            ValueError: If fraction is not in valid range
        """
        self.validate_fraction(fraction)
        
        n = int(len(ids) * fraction)
        return self.sample_n(ids, n, seed)
    
    def sample_n(
        self, 
        ids: np.ndarray, 
        n: int, 
        seed: Optional[int] = None
    ) -> np.ndarray:
        """
        Sample exactly n elements uniformly at random.
        
        Args:
            ids: Array of node IDs to sample from
            n: Number of elements to sample
            seed: Random seed for reproducibility
            
        Returns:
            Array of sampled node IDs
            
        Raises:
            ValueError: If n is not valid
        """
        self.validate_sample_size(n, len(ids))
        
        if n == 0:
            return np.array([], dtype=ids.dtype)
        
        if n == len(ids):
            return ids.copy()
        
        # Use numpy's random generator for better performance and reproducibility
        rng = np.random.default_rng(seed)
        return rng.choice(ids, size=n, replace=False)
