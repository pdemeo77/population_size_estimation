"""
HyperLogLog Estimator.

Improved cardinality estimation with log-log scaling and better memory efficiency.
Reference: Flajolet et al., 2007 - HyperLogLog: the analysis of a near-optimal 
cardinality estimation algorithm
"""

import numpy as np
from typing import Optional
from ..base import BaseEstimator, EstimationResult


class HyperLogLogEstimator(BaseEstimator):
    """
    HyperLogLog cardinality estimator.
    
    Algorithm:
        1. Hash each element to a binary string
        2. Use first p bits to select a register (2^p registers)
        3. Track maximum rho (leftmost 1-bit position) in each register
        4. Estimate using harmonic mean of 2^rho values
    
    Properties:
        - Memory: O(2^p) bytes (typically 16KB for p=14)
        - Standard error: approx 1.04 / sqrt(m)
        - Works with any hashable data
        - Best accuracy/memory tradeoff among cardinality estimators
    """
    
    ALPHA = {16: 0.673, 32: 0.697, 64: 0.709}
    
    def __init__(self, precision: int = 14, hash_size: int = 32):
        if precision < 4 or precision > 16:
            raise ValueError("Precision must be between 4 and 16")
        
        if hash_size < precision:
            raise ValueError(
                f"hash_size ({hash_size}) must be >= precision ({precision}). "
                f"Need at least {precision} bits for register indexing."
            )
        
        if hash_size not in (32, 64):
            raise ValueError(
                f"hash_size must be 32 or 64 bits, got {hash_size}"
            )
        
        self.precision = precision
        self.hash_size = hash_size
        self.num_registers = 2 ** precision
        self._alpha = self._compute_alpha()
    
    def _compute_alpha(self) -> float:
        m = self.num_registers
        if m in self.ALPHA:
            return self.ALPHA[m]
        return 0.7213 / (1 + 1.079 / m)
    
    @property
    def name(self) -> str:
        return "HyperLogLog"
    
    def estimate(self, sample: np.ndarray, **kwargs) -> EstimationResult:
        """Estimate population size using HyperLogLog algorithm."""
        self.validate_input(sample)
        
        # Use int32 to avoid int8 overflow: rho values can exceed 127 for large hash spaces
        registers = np.zeros(self.num_registers, dtype=np.int32)
        
        for element in sample:
            hash_val = self._hash(int(element))
            register_idx = hash_val >> (self.hash_size - self.precision)
            remaining_bits = hash_val & ((1 << (self.hash_size - self.precision)) - 1)
            rho = self._rho(remaining_bits) + 1
            registers[register_idx] = max(registers[register_idx], rho)
        
        # Compute raw estimate using harmonic mean over ALL registers (including zeros).
        # When M_j == 0, the contribution is 2^(-0) == 1.0 — excluding zero registers
        # would undercount z and inflate the estimate.
        z = np.sum(2.0 ** (-registers.astype(float)))
        raw_estimate = self._alpha * (self.num_registers ** 2) / z
        
        # Apply range corrections
        estimate = self._apply_correction(raw_estimate, registers)
        
        # Variance estimate
        variance = (1.04 / np.sqrt(self.num_registers)) ** 2 * (estimate ** 2)
        std_error = np.sqrt(variance)
        
        z_score = 1.96
        ci_lower = max(1, estimate - z_score * std_error)
        ci_upper = estimate + z_score * std_error
        
        return EstimationResult(
            estimate=float(estimate),
            ci_lower=float(ci_lower),
            ci_upper=float(ci_upper),
            variance=float(variance),
            metadata={
                'precision': self.precision,
                'num_registers': self.num_registers,
                'zero_registers': int(np.sum(registers == 0))
            }
        )
    
    def _hash(self, value: int) -> int:
        """MurmurHash3-style hash function."""
        h = value ^ 0x9e3779b9
        h = ((h >> 16) ^ h) * 0x85ebca6b
        h = ((h >> 13) ^ h) * 0xc2b2ae35
        h = (h >> 16) ^ h
        return h & 0xFFFFFFFF
    
    def _rho(self, hash_value) -> int:
        """Find position of leftmost 1-bit (0-indexed)."""
        # Convert to Python int to ensure bit_length() is available
        hash_value = int(hash_value)
        if hash_value == 0:
            return 0
        return (hash_value & -hash_value).bit_length() - 1
    
    def _apply_correction(self, estimate: float, registers: np.ndarray) -> float:
        """Apply range-specific bias corrections."""
        # Small range correction (linear counting)
        if estimate <= 2.5 * self.num_registers:
            zeros = np.sum(registers == 0)
            if zeros > 0:
                return self.num_registers * np.log(self.num_registers / zeros)
        
        # Large range correction (for 32-bit hashes)
        if self.hash_size == 32 and estimate > (1/30) * (2 ** 32):
            return -(2 ** 32) * np.log(1 - estimate / (2 ** 32))
        
        return estimate
    
    def memory_usage(self) -> int:
        """Return memory usage in bytes."""
        return self.num_registers  # 1 byte per register
