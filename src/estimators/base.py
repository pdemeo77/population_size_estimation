"""
Base classes for population size estimators.

This module defines the abstract interface that all estimators must implement,
ensuring consistent behavior across different estimation methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple
import numpy as np
from scipy import stats


@dataclass
class EstimationResult:
    """
    Container for estimation results with metadata.
    
    Attributes:
        estimate: The estimated population size
        ci_lower: Lower bound of confidence interval (optional)
        ci_upper: Upper bound of confidence interval (optional)
        variance: Estimated variance of the estimator (optional)
        std_error: Standard error of the estimate (optional)
        metadata: Additional information about the estimation process
        
    Example:
        >>> result = EstimationResult(
        ...     estimate=100000,
        ...     ci_lower=95000,
        ...     ci_upper=105000,
        ...     variance=25000000
        ... )
        >>> result.relative_ci_width
        0.1
    """
    estimate: float
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    variance: Optional[float] = None
    std_error: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Compute derived quantities if not provided."""
        if self.variance is not None and self.std_error is None:
            self.std_error = np.sqrt(self.variance)
    
    @property
    def relative_ci_width(self) -> Optional[float]:
        """Return the relative width of the confidence interval."""
        if self.ci_lower is not None and self.ci_upper is not None and self.estimate != 0:
            return (self.ci_upper - self.ci_lower) / self.estimate
        return None
    
    @property
    def ci_contains_estimate(self) -> Optional[bool]:
        """Check if the estimate falls within the confidence interval."""
        if self.ci_lower is not None and self.ci_upper is not None:
            return self.ci_lower <= self.estimate <= self.ci_upper
        return None
    
    def relative_error(self, true_size: float) -> float:
        """
        Compute relative error against true population size.
        
        Args:
            true_size: The true population size
            
        Returns:
            Relative error as a fraction (not percentage)
        """
        if true_size == 0:
            return float('inf') if self.estimate != 0 else 0.0
        return abs(self.estimate - true_size) / true_size
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'estimate': self.estimate,
            'ci_lower': self.ci_lower,
            'ci_upper': self.ci_upper,
            'variance': self.variance,
            'std_error': self.std_error,
            'metadata': self.metadata
        }


class BaseEstimator(ABC):
    """
    Abstract base class for all population size estimators.
    
    All estimators must implement this interface to ensure consistent behavior
    across different estimation methods. The base class provides common
    validation and utility methods.
    
    Subclasses must implement:
        - name property: Return the estimator name
        - estimate method: Perform the estimation
        
    Optionally override:
        - requires_two_samples: Return True if estimator needs two samples
        - validate_input: Custom input validation
        
    Example:
        >>> class MyEstimator(BaseEstimator):
        ...     @property
        ...     def name(self) -> str:
        ...         return "MyEstimator"
        ...     
        ...     def estimate(self, sample, **kwargs):
        ...         self.validate_input(sample)
        ...         return EstimationResult(estimate=len(sample) * 2)
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return estimator name for logging and results.
        
        Returns:
            String identifier for this estimator
        """
        pass
    
    @property
    def requires_two_samples(self) -> bool:
        """
        Indicate if this estimator requires two independent samples.
        
        Override to return True for estimators like Capture-Recapture
        that need two separate samples.
        
        Returns:
            True if two samples are required, False otherwise
        """
        return False
    
    @abstractmethod
    def estimate(self, sample: np.ndarray, **kwargs) -> EstimationResult:
        """
        Estimate population size from a sample.
        
        Args:
            sample: Array of observed IDs/identifiers (1D numpy array)
            **kwargs: Additional parameters
                - sample2: Second sample for two-sample estimators
                - m: Sample size (if different from len(sample))
                - ci_alpha: Significance level for confidence intervals
                
        Returns:
            EstimationResult containing the estimate and metadata
        """
        pass
    
    def validate_input(self, sample: np.ndarray) -> None:
        """
        Validate input sample.
        
        Args:
            sample: Input sample to validate
            
        Raises:
            ValueError: If sample is empty or contains invalid values
            TypeError: If sample is not a numpy array
        """
        if sample is None:
            raise ValueError("Sample cannot be None")
        if not isinstance(sample, np.ndarray):
            raise TypeError(f"Sample must be a numpy array, got {type(sample)}")
        if len(sample) == 0:
            raise ValueError("Sample cannot be empty")
        if sample.ndim != 1:
            raise ValueError(f"Sample must be 1-dimensional, got {sample.ndim} dimensions")
        if not np.all(np.isfinite(sample)):
            raise ValueError("Sample contains non-finite values (inf or nan)")
    
    def compute_confidence_interval(
        self,
        estimate: float,
        std_error: float,
        alpha: float = 0.05,
        method: str = 'normal'
    ) -> Tuple[float, float]:
        """
        Compute confidence interval for the estimate.
        
        Args:
            estimate: Point estimate
            std_error: Standard error of the estimate
            alpha: Significance level (default 0.05 for 95% CI)
            method: Method for computing CI ('normal', 'log')
            
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        z = stats.norm.ppf(1 - alpha / 2)
        
        if method == 'normal':
            ci_lower = max(0, estimate - z * std_error)
            ci_upper = estimate + z * std_error
        elif method == 'log':
            # Log-normal CI (better for positive estimates)
            if estimate <= 0:
                ci_lower, ci_upper = 0, estimate + z * std_error
            else:
                log_est = np.log(estimate)
                log_se = std_error / estimate
                ci_lower = np.exp(log_est - z * log_se)
                ci_upper = np.exp(log_est + z * log_se)
        else:
            raise ValueError(f"Unknown CI method: {method}")
        
        return ci_lower, ci_upper
    
    def __repr__(self) -> str:
        """Return string representation of the estimator."""
        return f"{self.__class__.__name__}()"
    
    def __str__(self) -> str:
        """Return human-readable string."""
        return f"{self.name} Estimator"


def create_estimator(estimator_type: str, **kwargs) -> BaseEstimator:
    """
    Factory function to create estimators by name.
    
    Args:
        estimator_type: Name of the estimator type
        **kwargs: Parameters to pass to the estimator constructor
        
    Returns:
        Configured estimator instance
        
    Raises:
        ValueError: If estimator type is unknown
        
    Example:
        >>> estimator = create_estimator('german_tank')
        >>> result = estimator.estimate(sample)
    """
    # Import here to avoid circular imports
    from .order_statistics import (
        GermanTankEstimator,
        SpacingEstimator,
        RankInversionEstimator,
        CaptureRecaptureEstimator,
    )
    
    estimators = {
        'german_tank': GermanTankEstimator,
        'spacing': SpacingEstimator,
        'rank_inversion': RankInversionEstimator,
        'capture_recapture': CaptureRecaptureEstimator,
        'cr': CaptureRecaptureEstimator,
    }
    
    key = estimator_type.lower().replace('-', '_').replace(' ', '_')
    
    if key not in estimators:
        available = ', '.join(sorted(estimators.keys()))
        raise ValueError(
            f"Unknown estimator type: '{estimator_type}'. "
            f"Available types: {available}"
        )
    
    return estimators[key](**kwargs)
