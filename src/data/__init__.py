"""
Data loading module for population size estimation experiments.

This module provides utilities for downloading and loading graph datasets
from the Stanford Network Analysis Project (SNAP).
"""

from .loader import DatasetLoader, SNAP_DATASETS

__all__ = ["DatasetLoader", "SNAP_DATASETS"]
