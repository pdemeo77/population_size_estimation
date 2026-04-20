"""
Population Size Estimators Module.

This module provides a unified interface for order statistics-based
population size estimation methods.
"""

from .base import BaseEstimator, EstimationResult, create_estimator
from .order_statistics import (
    GermanTankEstimator,
    SpacingEstimator,
    RankInversionEstimator,
    CaptureRecaptureEstimator,
)

__all__ = [
    # Base classes
    "BaseEstimator",
    "EstimationResult",
    "create_estimator",
    # Order statistics estimators
    "GermanTankEstimator",
    "SpacingEstimator",
    "RankInversionEstimator",
    "CaptureRecaptureEstimator",
]
