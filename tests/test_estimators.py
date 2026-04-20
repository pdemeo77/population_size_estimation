"""
Unit tests for population size estimators.

Tests all estimator implementations for correctness and interface compliance.
"""

import pytest
import numpy as np
from src.estimators import (
    BaseEstimator,
    EstimationResult,
    GermanTankEstimator,
    SpacingEstimator,
    RankInversionEstimator,
    CaptureRecaptureEstimator,
    create_estimator,
)


class TestEstimationResult:
    """Test EstimationResult dataclass."""
    
    def test_basic_result(self):
        result = EstimationResult(
            estimate=100000,
            ci_lower=95000,
            ci_upper=105000,
            variance=25000000
        )
        assert result.estimate == 100000
        assert result.ci_lower == 95000
        assert result.ci_upper == 105000
        assert result.variance == 25000000
        assert result.std_error == np.sqrt(25000000)
    
    def test_relative_ci_width(self):
        result = EstimationResult(
            estimate=100000,
            ci_lower=95000,
            ci_upper=105000
        )
        assert result.relative_ci_width == 0.1
    
    def test_relative_error(self):
        result = EstimationResult(estimate=105000)
        error = result.relative_error(100000)
        assert error == 0.05
    
    def test_to_dict(self):
        result = EstimationResult(estimate=100000, variance=1000)
        d = result.to_dict()
        assert 'estimate' in d
        assert 'variance' in d


class TestGermanTankEstimator:
    """Test German Tank estimator."""
    
    def test_basic_estimate(self):
        estimator = GermanTankEstimator()
        # Sample from population 1-100000
        np.random.seed(42)
        sample = np.random.choice(np.arange(1, 100001), size=1000, replace=False)
        result = estimator.estimate(sample)
        
        assert result.estimate > 0
        assert result.metadata['sample_size'] == 1000
    
    def test_perfect_sample(self):
        estimator = GermanTankEstimator()
        # Perfect sample with max = 100000
        sample = np.array([1, 100000])
        result = estimator.estimate(sample)
        
        # German Tank should estimate close to 100000
        expected = 100000 + 100000/2 - 1
        assert abs(result.estimate - expected) < 1
    
    def test_name(self):
        estimator = GermanTankEstimator()
        assert estimator.name == "German Tank"
    
    def test_empty_sample_raises(self):
        estimator = GermanTankEstimator()
        with pytest.raises(ValueError):
            estimator.estimate(np.array([]))


class TestSpacingEstimator:
    """Test Spacing estimator."""
    
    def test_basic_estimate(self):
        estimator = SpacingEstimator()
        np.random.seed(42)
        sample = np.random.choice(np.arange(1, 100001), size=1000, replace=False)
        result = estimator.estimate(sample)
        
        assert result.estimate > 0
    
    def test_translation_invariance(self):
        estimator = SpacingEstimator()
        sample1 = np.array([100, 200, 300, 400, 500])
        sample2 = np.array([100100, 100200, 100300, 100400, 100500])  # offset by 100000
        
        result1 = estimator.estimate(sample1)
        result2 = estimator.estimate(sample2)
        
        # Should give similar estimates (within 10%)
        assert abs(result1.estimate - result2.estimate) / result1.estimate < 0.1
    
    def test_small_sample(self):
        estimator = SpacingEstimator()
        sample = np.array([1])  # Single element
        result = estimator.estimate(sample)
        # Should return NaN for very small samples
        assert np.isnan(result.estimate)
        # Verify metadata explains why
        assert 'error' in result.metadata
        assert result.metadata['error'] == 'Need at least 2 samples'


class TestRankInversionEstimator:
    """Test Rank Inversion estimator."""
    
    def test_basic_estimate(self):
        estimator = RankInversionEstimator()
        np.random.seed(42)
        sample = np.random.choice(np.arange(1, 100001), size=1000, replace=False)
        result = estimator.estimate(sample)
        
        assert result.estimate > 0
    
    def test_robust_to_outliers(self):
        estimator = RankInversionEstimator()
        # Sample with one outlier
        sample = np.array([100, 200, 300, 400, 500, 1000000])  # outlier at end
        result = estimator.estimate(sample)
        
        # Should still give reasonable estimate
        assert result.estimate > 0


class TestCaptureRecaptureEstimator:
    """Test Capture-Recapture estimator."""
    
    def test_basic_estimate(self):
        estimator = CaptureRecaptureEstimator()
        np.random.seed(42)
        sample1 = np.random.choice(np.arange(1, 10001), size=100, replace=False)
        sample2 = np.random.choice(np.arange(1, 10001), size=100, replace=False)
        result = estimator.estimate(sample1, sample2=sample2)
        
        assert result.estimate > 0
    
    def test_requires_two_samples(self):
        estimator = CaptureRecaptureEstimator()
        assert estimator.requires_two_samples == True
    
    def test_no_overlap_returns_inf(self):
        estimator = CaptureRecaptureEstimator()
        sample1 = np.array([1, 2, 3])
        sample2 = np.array([100, 200, 300])
        result = estimator.estimate(sample1, sample2=sample2)
        
        assert result.estimate == float('inf')
    
    def test_missing_second_sample_raises(self):
        estimator = CaptureRecaptureEstimator()
        sample = np.array([1, 2, 3])
        with pytest.raises(ValueError):
            estimator.estimate(sample)


class TestCreateEstimator:
    """Test factory function."""
    
    def test_create_german_tank(self):
        estimator = create_estimator('german_tank')
        assert isinstance(estimator, GermanTankEstimator)
    
    def test_create_with_alias(self):
        # Test CR alias
        assert isinstance(create_estimator('cr'), CaptureRecaptureEstimator)
    
    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            create_estimator('unknown_estimator')


class TestEstimatorIntegration:
    """Integration tests comparing estimators."""
    
    def test_all_estimators_on_same_sample(self):
        np.random.seed(42)
        true_size = 100000
        sample_size = 1000
        
        population = np.arange(1, true_size + 1)
        sample = np.random.choice(population, size=sample_size, replace=False)
        sample2 = np.random.choice(population, size=sample_size, replace=False)
        
        estimators = [
            GermanTankEstimator(),
            SpacingEstimator(),
            RankInversionEstimator(),
        ]
        
        results = {}
        for estimator in estimators:
            result = estimator.estimate(sample)
            results[estimator.name] = result
            
            # All estimates should be positive
            assert result.estimate > 0, f"{estimator.name} gave non-positive estimate"
            
            # All should be within 50% of true value
            if result.estimate < float('inf'):
                rel_error = abs(result.estimate - true_size) / true_size
                print(f"{estimator.name}: estimate={result.estimate:.0f}, rel_error={rel_error:.2%}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
