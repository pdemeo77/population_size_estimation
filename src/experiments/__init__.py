"""
Experiments module for population size estimation.

This module provides utilities for running experiments, computing metrics,
and generating visualizations.
"""

from .distortions import (
    add_offset,
    add_gaps,
    add_multiplicative_noise,
    apply_zipf_bias,
)
from .runner import ExperimentRunner

__all__ = [
    "add_offset",
    "add_gaps",
    "add_multiplicative_noise",
    "apply_zipf_bias",
    "ExperimentRunner",
]
