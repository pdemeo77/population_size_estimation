"""
Population Size Estimators Module.

This module provides a unified interface for various population size estimation
methods, including order statistics-based and cardinality-based estimators.
"""

from .base import BaseEstimator, EstimationResult, create_estimator
from .order_statistics import (
    GermanTankEstimator,
    SpacingEstimator,
    RankInversionEstimator,
    CaptureRecaptureEstimator,
)
from .cardinality import (
    FlajoletMartinEstimator,
    HyperLogLogEstimator,
    MinCountEstimator,
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
    # Cardinality estimators
    "FlajoletMartinEstimator",
    "HyperLogLogEstimator",
    "MinCountEstimator",
]
