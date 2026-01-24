# Results Directory

This directory contains JSON output files from experiments.

## File Naming Convention

- `discrete_experiment_*.json` - Single discrete population experiments
- `mn_ratio_analysis_*.json` - M/N ratio analysis results
- `experiment1_*.json` - Experiment 1 from main estimators

## Structure

Each result file contains:
- **parameters**: Experiment configuration (n_true, m, R, seed, etc.)
- **results**: Statistical results for each estimator
  - median, mean, bias, relative error, MAD, standard deviation
  - coverage (whether true value falls in confidence interval)
  - valid percentage

## Usage

Results are automatically saved when running experiments:

```bash
# Automatically saves results
python discrete_estimators.py --n-true 100000 --m 1000 --repetitions 1000

# Skip automatic saving
python discrete_estimators.py --no-save
```

Results can be loaded and analyzed:

```python
import json

with open('results/discrete_experiment_*.json', 'r') as f:
    data = json.load(f)
    
print(data['parameters'])
print(data['results'])
```
