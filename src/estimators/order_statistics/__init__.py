"""
Order Statistics-based Population Size Estimators.

This module contains estimators based on order statistics from observed
sequential IDs, including the classic German Tank estimator and variants.
"""

from .german_tank import GermanTankEstimator
from .spacing import SpacingEstimator
from .rank_inversion import RankInversionEstimator
from .capture_recapture import CaptureRecaptureEstimator

__all__ = [
    "GermanTankEstimator",
    "SpacingEstimator",
    "RankInversionEstimator",
    "CaptureRecaptureEstimator",
]
