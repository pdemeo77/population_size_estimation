# Population Size Estimation - A1-A5 Experiments

Statistical validation of discrete population size estimators based on unique sequential IDs. This repository implements and compares classical estimation methods (German Tank, Spacing, Rank Inversion, Capture-Recapture) across five critical experimental scenarios.

## 🎯 Overview

Estimating the total size of a population from a finite sample of unique identifiers (IDs) is fundamental in many applications:
- **Competitive Intelligence**: Estimate competitor's volume from public order/issue IDs
- **Data Quality**: Detect missing or corrupted IDs in databases
- **System Monitoring**: Estimate total users/posts/transactions from sampled IDs

This project provides rigorous statistical validation through **5 benchmark experiments (A1-A5)** that test robustness across realistic scenarios.

## 📊 Experiments Summary

| Experiment | Scenario | Best Estimator | Accuracy |
|-----------|----------|---|---|
| **A1** | Sequential IDs (baseline) | German Tank | < 0.1% error |
| **A2** | IDs with random gaps | Capture-Recapture | < 0.2% error |
| **A3** | Unknown offset/translation | Spacing | < 1% error |
| **A4** | Fixed budget pooling | Rank Inversion | Stable worst-case |
| **A5** | Corrupted data & outliers | Rank Inversion | Robust to 50% corruption |

## 🎓 Key Findings

### German Tank Problem (Maximum-based)
- **Formula**: $\hat{N} = \max(\text{sample}) + \frac{\max(\text{sample})}{m} - 1$
- **Best for**: Clean sequential IDs starting at 1
- **Fails when**: Offset is unknown or data contains outliers

### Spacing Estimator (Translation-Invariant)
- **Formula**: $\hat{N} = m \times \text{median}(\text{gap between consecutive IDs})$
- **Best for**: Unknown offset, data quality issues
- **Advantage**: Differences cancel out any constant offset

### Rank Inversion (Median-based)
- **Method**: Exploit relationship between sample position and population rank
- **Best for**: Robustness to outliers, pooled estimates
- **Advantage**: Naturally robust through median aggregation

### Capture-Recapture (Overlap-based)
- **Formula**: $\hat{N} = \frac{(m_1+1)(m_2+1)}{I+1} - 1$ (Chapman)
- **Best for**: Sparse IDs with gaps (not dependent on absolute values)
- **Requires**: Two independent samples
- **Advantage**: Only uses overlap, ignores ID magnitude

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Dependencies: `numpy`, `scipy`

### Installation
```bash
pip install -r requirements.txt
```

### Run Experiments

```bash
# A1: Baseline validation (sequential IDs)
python run_blockA_pooling.py

# A2: Sparse IDs with gaps
python run_blockA_sparse.py

# A3: Translation invariance (offset unknown)
python run_blockA_translation.py

# A4: Pooling with fixed budget
python run_blockA_pooling.py --pooling

# A5: Robustness to corruption
python run_robustness_outliers.py
```

Results are saved to `results/*.json` with detailed statistics:
- Median estimate
- Relative error percentage
- 95% confidence interval
- Bias and variance metrics

## 📁 Repository Structure

```
discrete_estimators.py              # Core implementation (German Tank, Spacing, Rank, CR)
run_blockA_*.py                     # Experiment runners (A1-A5)
run_robustness_outliers.py          # A5: Outlier robustness test

results/
├── discrete_results.json           # A1 results
├── discrete_sparse_results.json    # A2 results
├── discrete_translation_results.json # A3 results
├── discrete_pooling_results.json   # A4 results
└── robustness_outliers_results.json # A5 results

figures/                            # Generated plots
requirements.txt                    # Python dependencies
```

## 📈 Key Results

### A1: Baseline (Clean Data)
```
m/n ratio | German Tank | Spacing | Rank Inversion
0.01      | 0.03%       | 0.99%   | 0.34%
0.05      | 0.00%       | 0.99%   | 0.09%
0.10      | 0.00%       | 0.99%   | 0.03%
```
**Winner**: German Tank is MVUE for clean sequential data.

### A3: Translation Invariance (Offset Unknown)
```
When IDs start from 50,001 instead of 1:
German Tank: 50% error (completely wrong)
Spacing:     < 1% error (translation-invariant!)
```

### A5: Data Corruption (1% corruption, 10x magnitude)
```
Corruption level | German Tank | Rank Inversion | Spacing
0% (clean)       | 0.24%       | 0.15%         | 0.24%
1%               | 493%        | 0.15%         | 0.24%
5%               | 2000%+      | 0.35%         | 0.99%
```
**Winner**: Rank Inversion robust until median breaks (~50% corruption).

## 🔧 Implementation Details

### Discrete Estimators (not continuous)
This project focuses on **discrete ID-based estimation**, where:
- Population consists of unique identifiers {1, 2, ..., N}
- Sampling is uniform without replacement
- No distributional assumptions (unlike Levene's continuous model)

### Robustness Metrics
- **Median Absolute Deviation (MAD)** for robust spread
- **95% Confidence Intervals** via quantile method
- **Trimmed statistics** to handle outliers

## 📊 Decision Table

| Use Case | Choose |
|----------|--------|
| Sequential IDs, verified clean | **German Tank** |
| Unknown offset (e.g., "order #1,000,001") | **Spacing** |
| IDs with gaps/sparse sampling | **Capture-Recapture** |
| Possibly corrupted data | **Rank Inversion** |
| Multiple independent samples available | **Capture-Recapture** |

## ⚠️ Limitations

- Assumes uniform sampling of IDs (not PPS or stratified)
- Assumes IDs are correctly observed (no misreporting)
- Works best with m/n ≥ 0.001 (sampling fraction)
- May fail under heavy non-uniformity (Pareto-distributed IDs)

## 📚 References

- German Tank Problem: Classic WWII serial number estimation
- Spacing methods: Order statistics theory
- Capture-Recapture: Chapman's bias-adjusted Lincoln-Petersen
- Original continuous model: Levene (2025)

## 💻 Code Example

```python
from discrete_estimators import (
    german_tank_estimator,
    spacing_estimator_discrete,
    rank_inversion_estimator_discrete,
    capture_recapture_chapman
)

# Sample IDs from population [1..100,000]
sample = np.array([1000, 5432, 50000, 87654, 99999])

# Estimate population size
n_tank = german_tank_estimator(sample)           # ~100,000
n_spacing = spacing_estimator_discrete(sample)   # ~100,000
n_rank = rank_inversion_estimator_discrete(sample, m=len(sample))  # ~100,000
```

## 📝 Citation

If you use this code in your research, cite:
```
Population Size Estimation (A1-A5 Experiments)
https://github.com/pdemeo77/population_size_estimation
```

## 🤝 Contributing

For new experiments or improvements:
1. Follow the A1-A5 structure
2. Include JSON results in `results/`
3. Update this README with new findings

## 📧 Questions?

Open an issue on GitHub or check the detailed documentation in the local `experiments.md` file.

---

**Repository**: https://github.com/pdemeo77/population_size_estimation  
**Last Updated**: January 2026
