# Figures Directory

This directory contains plots and visualizations from experiments.

## File Naming Convention

- `mn_ratio_analysis_*.png` - M/N ratio analysis plots (6 subplots)
- `experiment_*.png` - Individual experiment visualizations

## Generated Plots

### M/N Ratio Analysis
The comprehensive analysis generates a 6-panel figure:

1. **Relative Error vs m/n ratio** - Main comparison (log-log scale)
2. **Median Estimates vs m/n ratio** - Actual estimates compared to true N
3. **Variability (MAD) vs m/n ratio** - Estimator stability
4. **Rank Inversion detailed** - Estimates with IQR bands
5. **Spacing detailed** - Estimates with IQR bands
6. **Valid Estimate Percentage** - Success rate of each estimator

## Usage

Figures are automatically generated when running analysis:

```bash
# Automatically saves figure
python analyze_mn_ratio.py --repetitions 100

# Skip plotting
python analyze_mn_ratio.py --no-plot
```

## Requirements

Plotting requires matplotlib:
```bash
pip install matplotlib
```
