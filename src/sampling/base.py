"""
Base sampler interface for population size estimation.

This module defines the abstract interface that all samplers must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional

import numpy as np


class BaseSampler(ABC):
    """
    Abstract base class for all sampling strategies.
    
    All samplers must implement this interface to ensure consistent behavior
    across different sampling methods.
    
    Subclasses must implement:
        - name property: Return the sampler name
        - sample method: Sample a fraction of the population
        - sample_n method: Sample exactly n elements
        
    Example:
        >>> class MySampler(BaseSampler):
        ...     @property
        ...     def name(self) -> str:
        ...         return "MySampler"
        ...     
        ...     def sample(self, ids, fraction, seed=None):
        ...         n = int(len(ids) * fraction)
        ...         return self.sample_n(ids, n, seed)
        ...     
        ...     def sample_n(self, ids, n, seed=None):
        ...         rng = np.random.default_rng(seed)
        ...         return rng.choice(ids, size=n, replace=False)
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return sampler name for logging and results.
        
        Returns:
            String identifier for this sampler
        """
        pass
    
    @abstractmethod
    def sample(
        self, 
        ids: np.ndarray, 
        fraction: float, 
        seed: Optional[int] = None
    ) -> np.ndarray:
        """
        Sample a fraction of the population.
        
        Args:
            ids: Array of node IDs to sample from
            fraction: Fraction of population to sample (0.0 to 1.0)
            seed: Random seed for reproducibility
            
        Returns:
            Array of sampled node IDs
        """
        pass
    
    @abstractmethod
    def sample_n(
        self, 
        ids: np.ndarray, 
        n: int, 
        seed: Optional[int] = None
    ) -> np.ndarray:
        """
        Sample exactly n elements from the population.
        
        Args:
            ids: Array of node IDs to sample from
            n: Number of elements to sample
            seed: Random seed for reproducibility
            
        Returns:
            Array of sampled node IDs
        """
        pass
    
    def validate_fraction(self, fraction: float) -> None:
        """
        Validate that fraction is in valid range.
        
        Args:
            fraction: Fraction to validate
            
        Raises:
            ValueError: If fraction is not in [0, 1]
        """
        if not 0.0 <= fraction <= 1.0:
            raise ValueError(f"Fraction must be between 0 and 1, got {fraction}")
    
    def validate_sample_size(self, n: int, population_size: int) -> None:
        """
        Validate that sample size is valid.
        
        Args:
            n: Sample size to validate
            population_size: Size of the population
            
        Raises:
            ValueError: If sample size is invalid
        """
        if n < 0:
            raise ValueError(f"Sample size must be non-negative, got {n}")
        if n > population_size:
            raise ValueError(
                f"Sample size ({n}) cannot exceed population size ({population_size})"
            )
    
    def __repr__(self) -> str:
        """Return string representation of the sampler."""
        return f"{self.__class__.__name__}()"
    
    def __str__(self) -> str:
        """Return human-readable string."""
        return f"{self.name} Sampler"
