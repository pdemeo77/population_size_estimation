"""
Sampling strategies for population size estimation experiments.

This module provides various sampling methods for extracting subsets
from node ID populations.
"""

from .base import BaseSampler
from .uniform import UniformSampler

__all__ = ["BaseSampler", "UniformSampler"]
