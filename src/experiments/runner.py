"""
Experiment runner for population size estimation experiments.

 
This module provides the main ExperimentRunner class that handles
 experiment configuration, execution, and results aggregation.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import yaml

from src.estimators import create_estimator, EstimationResult
from src.data import DatasetLoader
from src.sampling import UniformSampler
from .distortions import apply_distortions


 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExperimentRunner:
    """
    Runner for population size estimation experiments.
    
    This class handles:
    - Loading experiment configurations from YAML files
    - Running experiments with various samplers, estimators, and distortions
    - Aggregating results and computing metrics
    - Saving results to JSON files
    
    Attributes:
        loader: DatasetLoader instance for loading data
        results_dir: Directory for saving results
        
    Example:
        >>> runner = ExperimentRunner()
        >>> config = runner.load_config("configs/baseline.yaml")
        >>> results = runner.run_config(config)
        >>> runner.save_results(results, "results/baseline.json")
    """
    
    def __init__(
        self, 
        results_dir: str = "results",
        data_dir: Optional[str] = None
    ):
        """
        Initialize the experiment runner.
        
        Args:
            results_dir: Directory for saving results
            data_dir: Directory for storing downloaded data (default: data/raw)
        """
        self.loader = DatasetLoader(data_dir=data_dir)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Sampler registry
        self._samplers = {
            "uniform": UniformSampler(),
        }
        
    def load_config(self, path: str) -> Dict[str, Any]:
        """
        Load experiment configuration from YAML file.
        
        Args:
            path: Path to YAML configuration file
            
        Returns:
            Dictionary with configuration parameters
            
        Raises:
                FileNotFoundError: If config file doesn't exist
                yaml.YAMLError: If config file is malformed
        """
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Set defaults
        config.setdefault('random_seed', 42)
        config.setdefault('num_repeats', 100)
        config.setdefault('distortions', {})
        
        return config
    
    def create_sampler(self, name: str):
        """
        Create a sampler by name.
        
        Args:
            name: Name of the sampler (e.g., "uniform")
            
        Returns:
            Sampler instance
            
        Raises:
                ValueError: If sampler name is unknown
        """
        name_lower = name.lower()
        if name_lower not in self._samplers:
            available = ", ".join(sorted(self._samplers.keys()))
            raise ValueError(
                f"Unknown sampler: '{name}'. Available: {available}"
            )
        return self._samplers[name_lower]
    
    def run_single(
        self,
        ids: np.ndarray,
        sampler_name: str,
        estimator_name: str,
        fraction: float,
        repeat_idx: int,
        seed: int,
        distortions_config: Optional[Dict[str, Any]] = None,
        true_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run a single experiment.
        
        Args:
            ids: Array of node IDs to sample from
            sampler_name: Name of the sampler to use
            estimator_name: Name of the estimator to use
            fraction: Fraction of population to sample
            repeat_idx: Index of this repeat (for seeding)
            seed: Random seed
            distortions_config: Dictionary of distortion parameters
            true_size: True population size (if known)
            
        Returns:
            Dictionary with experiment results
        """
        start_time = time.time()
        
        # Create sampler and estimator
        sampler = self.create_sampler(sampler_name)
        estimator = create_estimator(estimator_name)
        
        # Set random seed for this repeat
        repeat_seed = seed + repeat_idx
        
        # Sample
        sample = sampler.sample(ids, fraction, seed=repeat_seed)
        
        # Apply distortions if specified
        if distortions_config:
            sample = apply_distortions(sample, **distortions_config, seed=repeat_seed)
        
        # Estimate
        if estimator.requires_two_samples:
            # For capture-recapture, draw two independent samples
            sample2 = sampler.sample(ids, fraction, seed=repeat_seed + 10000)
            if distortions_config:
                sample2 = apply_distortions(sample2, **distortions_config, seed=repeat_seed + 20000)
            result = estimator.estimate(sample, sample2=sample2)
        else:
            result = estimator.estimate(sample)
        
        end_time = time.time()
        
        # Build result dictionary
        result_dict = {
            "sampler": sampler_name,
            "estimator": estimator_name,
            "fraction": fraction,
            "repeat_idx": repeat_idx,
            "estimate": result.estimate,
            "ci_lower": result.ci_lower,
            "ci_upper": result.ci_upper,
            "std_error": result.std_error,
            "runtime_ms": (end_time - start_time) * 1000,
            "metadata": result.metadata,
        }
        
        # Add true size metrics if available
        if true_size is not None:
            result_dict["true_size"] = true_size
            result_dict["relative_error"] = abs(result.estimate - true_size) / true_size
            if result.ci_lower is not None and result.ci_upper is not None:
                result_dict["ci_covers_true"] = (
                    result.ci_lower <= true_size <= result.ci_upper
                )
        
        return result_dict
    
    def run_config(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Run all experiments specified in configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            List of result dictionaries
        """
        all_results = []
        
        # Load dataset
        logger.info(f"Loading dataset: {config['dataset']}")
        ids = self.loader.get_dataset(config['dataset'])
        true_size = len(ids)
        logger.info(f"Loaded {true_size:,} nodes")
        
        # Get parameters
        sampler_name = config.get('sampler', 'uniform')
        sample_fractions = config.get('sample_fractions', [0.01, 0.05, 0.1])
        estimators = config.get('estimators', ['german_tank', 'spacing', 'rank_inversion'])
        num_repeats = config.get('num_repeats', 100)
        seed = config.get('random_seed', 42)
        distortions_config = config.get('distortions', {})
        
        # Calculate total experiments
        total_experiments = (
            len(sample_fractions) * len(estimators) * num_repeats
        )
        logger.info(f"Running {total_experiments:,} experiments")
        
        # Run all combinations
        experiment_count = 0
        for fraction in sample_fractions:
            for estimator_name in estimators:
                for repeat_idx in range(num_repeats):
                    experiment_count += 1
                    
                    if experiment_count % 100 == 0:
                        logger.info(f"Progress: {experiment_count}/{total_experiments}")
                    
                    try:
                        result = self.run_single(
                            ids=ids,
                            sampler_name=sampler_name,
                            estimator_name=estimator_name,
                            fraction=fraction,
                            repeat_idx=repeat_idx,
                            seed=seed,
                            distortions_config=distortions_config if distortions_config else None,
                            true_size=true_size,
                        )
                        all_results.append(result)
                    except Exception as e:
                        logger.error(f"Experiment failed: {e}")
                        all_results.append({
                            "sampler": sampler_name,
                            "estimator": estimator_name,
                            "fraction": fraction,
                            "repeat_idx": repeat_idx,
                            "error": str(e),
                        })
        
        logger.info(f"Completed {len(all_results):,} experiments")
        return all_results
    
    def aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results by estimator and fraction.
        
        Args:
            results: List of individual experiment results
            
        Returns:
            Dictionary with aggregated metrics
        """
        aggregated = {}
        
        for result in results:
            if "error" in result:
                continue
                
            key = (result["estimator"], result["fraction"])
            
            if key not in aggregated:
                aggregated[key] = {
                    "estimator": result["estimator"],
                    "fraction": result["fraction"],
                    "estimates": [],
                    "relative_errors": [],
                    "runtimes": [],
                    "ci_coverage": [],
                }
            
            aggregated[key]["estimates"].append(result["estimate"])
            if "relative_error" in result:
                aggregated[key]["relative_errors"].append(result["relative_error"])
            if "runtime_ms" in result:
                aggregated[key]["runtimes"].append(result["runtime_ms"])
            if "ci_covers_true" in result:
                aggregated[key]["ci_coverage"].append(result["ci_covers_true"])
        
        # Compute summary statistics
        summary = []
        for key, data in aggregated.items():
            estimates = np.array(data["estimates"])
            relative_errors = np.array(data["relative_errors"]) if data["relative_errors"] else None
            runtimes = np.array(data["runtimes"]) if data["runtimes"] else None
            ci_coverage = np.array(data["ci_coverage"]) if data["ci_coverage"] else None
            
            summary.append({
                "estimator": data["estimator"],
                "fraction": data["fraction"],
                "num_repeats": len(estimates),
                "median_estimate": float(np.median(estimates)),
                "mean_estimate": float(np.mean(estimates)),
                "std_estimate": float(np.std(estimates)),
                "mean_relative_error": float(np.mean(relative_errors)) if relative_errors is not None else None,
                "median_relative_error": float(np.median(relative_errors)) if relative_errors is not None else None,
                "mean_runtime_ms": float(np.mean(runtimes)) if runtimes is not None else None,
                "ci_coverage_rate": float(np.mean(ci_coverage)) if ci_coverage is not None else None,
            })
        
        return summary
    
    def save_results(self, results: List[Dict[str, Any]], path: str) -> None:
        """
        Save results to JSON file.
        
        Args:
            results: List of result dictionaries
            path: Path to output file (relative to results_dir)
        """
        full_path = self.results_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {full_path}")
    
    def save_aggregated(self, aggregated: Dict[str, Any], path: str) -> None:
        """
        Save aggregated results to JSON file.
        
        Args:
            aggregated: Aggregated results dictionary
            path: Path to output file (relative to results_dir)
        """
        full_path = self.results_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            json.dump(aggregated, f, indent=2)
        
        logger.info(f"Aggregated results saved to {full_path}")


def run_experiment(config_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to run an experiment from config file.
    
    Args:
        config_path: Path to YAML configuration file
        output_path: Path to output JSON file (default: from config)
        
    Returns:
            Dictionary with aggregated results
    """
    runner = ExperimentRunner()
    config = runner.load_config(config_path)
    results = runner.run_config(config)
    aggregated = runner.aggregate_results(results)
    
    # Determine output path
    if output_path is None:
        output_path = config.get('output', 'results/experiment.json')
    
    # Save both raw and aggregated results
    runner.save_results(results, output_path.replace('.json', '_raw.json'))
    runner.save_aggregated(aggregated, output_path)
    
    return aggregated


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run population size estimation experiments")
    parser.add_argument("--config", "-c", required=True, help="Path to config file")
    parser.add_argument("--output", "-o", default=None, help="Path to output file")
    
    args = parser.parse_args()
    
    run_experiment(args.config, args.output)
