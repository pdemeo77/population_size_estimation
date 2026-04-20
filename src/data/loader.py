"""
Dataset loader for SNAP graph datasets.

This module provides utilities for downloading and loading graph datasets
from the Stanford Network Analysis Project (SNAP).
"""

import gzip
import logging
import os
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# SNAP dataset URLs and metadata
SNAP_DATASETS: Dict[str, Dict[str, str]] = {
    "web-Stanford": {
        "url": "https://snap.stanford.edu/data/web-Stanford.txt.gz",
        "description": "Web graph from Stanford.edu",
        "nodes": "281K",
        "edges": "2.3M",
    },
    "web-Google": {
        "url": "https://snap.stanford.edu/data/web-Google.txt.gz",
        "description": "Web graph from Google",
        "nodes": "875K",
        "edges": "5.1M",
    },
    "soc-Pokec": {
        "url": "https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz",
        "description": "Social network from Pokec",
        "nodes": "1.6M",
        "edges": "30M",
    },
    "soc-LiveJournal1": {
        "url": "https://snap.stanford.edu/data/soc-LiveJournal1.txt.gz",
        "description": "Social network from LiveJournal",
        "nodes": "4.8M",
        "edges": "69M",
    },
    "soc-twitter-follows": {
        "url": "https://snap.stanford.edu/data/twitter_combined.txt.gz",
        "description": "Twitter social network (follower relationships)",
        "nodes": "1.9M",
        "edges": "1.5B",
    },
    "road-USA": {
        "url": "https://snap.stanford.edu/data/usa.osm.graph.txt.gz",
        "description": "USA road network from OpenStreetMap",
        "nodes": "23.9M",
        "edges": "58.3M",
    },
}


class DatasetLoader:
    """
    Loader for SNAP graph datasets.
    
    This class handles downloading, extracting, and parsing SNAP datasets
    to extract node IDs for population size estimation experiments.
    
    Attributes:
        data_dir: Base directory for storing downloaded data
        datasets: Dictionary of available datasets with metadata
        
    Example:
        >>> loader = DatasetLoader()
        >>> node_ids = loader.get_dataset("web-Stanford")
        >>> print(f"Loaded {len(node_ids)} nodes")
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the dataset loader.
        
        Args:
            data_dir: Directory to store downloaded data. 
                     Defaults to data/raw/ relative to project root.
        """
        if data_dir is None:
            # Find project root (where src/ is located)
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data" / "raw"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, np.ndarray] = {}
        
    def download_snap_dataset(
        self, 
        name: str, 
        force: bool = False,
        show_progress: bool = True
    ) -> Path:
        """
        Download and extract a SNAP dataset.
        
        Args:
            name: Name of the dataset (e.g., "web-Stanford")
            force: If True, re-download even if file exists
            show_progress: If True, show download progress
            
        Returns:
            Path to the extracted .txt file
            
        Raises:
            ValueError: If dataset name is unknown
            RuntimeError: If download fails
        """
        if name not in SNAP_DATASETS:
            available = ", ".join(sorted(SNAP_DATASETS.keys()))
            raise ValueError(
                f"Unknown dataset: '{name}'. Available: {available}"
            )
        
        url = SNAP_DATASETS[name]["url"]
        gz_path = self.data_dir / f"{name}.txt.gz"
        txt_path = self.data_dir / f"{name}.txt"
        
        # Check if already extracted
        if txt_path.exists() and not force:
            logger.info(f"Dataset '{name}' already extracted at {txt_path}")
            return txt_path
        
        # Download .gz file
        if not gz_path.exists() or force:
            logger.info(f"Downloading {name} from {url}...")
            
            def progress_hook(block_num: int, block_size: int, total_size: int):
                if show_progress and total_size > 0:
                    downloaded = block_num * block_size
                    percent = min(100, downloaded * 100 // total_size)
                    print(f"\rDownloading: {percent}% ({downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB)", end="")
            
            try:
                urllib.request.urlretrieve(url, gz_path, progress_hook)
                if show_progress:
                    print()  # New line after progress
                logger.info(f"Downloaded to {gz_path}")
            except Exception as e:
                raise RuntimeError(f"Failed to download {name}: {e}")
        
        # Extract .gz file
        logger.info(f"Extracting {gz_path}...")
        try:
            with gzip.open(gz_path, 'rb') as f_in:
                with open(txt_path, 'wb') as f_out:
                    # Read in chunks to handle large files
                    chunk_size = 1024 * 1024  # 1MB chunks
                    while True:
                        chunk = f_in.read(chunk_size)
                        if not chunk:
                            break
                        f_out.write(chunk)
            logger.info(f"Extracted to {txt_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to extract {name}: {e}")
        
        return txt_path
    
    def load_edge_list(
        self, 
        filepath: Path,
        skip_comments: bool = True,
        comment_char: str = '#'
    ) -> np.ndarray:
        """
        Load edge list from a SNAP-format file.
        
        SNAP format: Each line contains "source target" (space-separated).
        Lines starting with # are comments.
        
        Args:
            filepath: Path to the edge list file
            skip_comments: If True, skip lines starting with comment_char
            comment_char: Character that indicates a comment line
            
        Returns:
            Array of shape (num_edges, 2) with (source, target) pairs
        """
        edges: List[Tuple[int, int]] = []
        
        logger.info(f"Loading edge list from {filepath}...")
        
        with open(filepath, 'r') as f:
            for i, line in enumerate(f):
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                    
                # Skip comments
                if skip_comments and line.startswith(comment_char):
                    continue
                
                # Parse edge
                try:
                    parts = line.split()
                    if len(parts) >= 2:
                        source = int(parts[0])
                        target = int(parts[1])
                        edges.append((source, target))
                except ValueError as e:
                    logger.warning(f"Skipping malformed line {i+1}: {line[:50]}...")
                    continue
        
        logger.info(f"Loaded {len(edges)} edges")
        return np.array(edges, dtype=np.int64)
    
    def extract_node_ids(
        self, 
        edges: np.ndarray,
        sort: bool = True
    ) -> np.ndarray:
        """
        Extract unique node IDs from edge list.
        
        Args:
            edges: Array of shape (num_edges, 2) with (source, target) pairs
            sort: If True, return sorted node IDs
            
        Returns:
            Array of unique node IDs
        """
        # Get unique nodes from both columns
        sources = edges[:, 0]
        targets = edges[:, 1]
        unique_nodes = np.unique(np.concatenate([sources, targets]))
        
        if sort:
            unique_nodes = np.sort(unique_nodes)
            
        logger.info(f"Extracted {len(unique_nodes)} unique nodes")
        return unique_nodes
    
    def get_dataset(
        self, 
        name: str,
        force_download: bool = False,
        use_cache: bool = True
    ) -> np.ndarray:
        """
        Get node IDs for a dataset, downloading if necessary.
        
        This is the main entry point for loading datasets. It handles
        downloading, extraction, and parsing automatically.
        
        Args:
            name: Name of the dataset (e.g., "web-Stanford")
            force_download: If True, re-download even if file exists
            use_cache: If True, cache loaded node IDs in memory
            
        Returns:
            Array of unique node IDs
            
        Raises:
            ValueError: If dataset name is unknown
        """
        # Check memory cache
        if use_cache and name in self._cache:
            logger.info(f"Using cached node IDs for '{name}'")
            return self._cache[name]
        
        # Download and extract if needed
        txt_path = self.download_snap_dataset(name, force=force_download)
        
        # Load edge list and extract nodes
        edges = self.load_edge_list(txt_path)
        node_ids = self.extract_node_ids(edges)
        
        # Cache in memory
        if use_cache:
            self._cache[name] = node_ids
            
        return node_ids
    
    def get_dataset_info(self, name: str) -> Dict[str, str]:
        """
        Get metadata about a dataset.
        
        Args:
            name: Name of the dataset
            
        Returns:
            Dictionary with dataset metadata
        """
        if name not in SNAP_DATASETS:
            raise ValueError(f"Unknown dataset: '{name}'")
            
        info = SNAP_DATASETS[name].copy()
        info["name"] = name
        return info
    
    def list_datasets(self) -> List[str]:
        """
        List available datasets.
        
        Returns:
            List of dataset names
        """
        return list(SNAP_DATASETS.keys())
    
    def download_all(self, force: bool = False) -> Dict[str, Path]:
        """
        Download all available datasets.
        
        Args:
            force: If True, re-download even if files exist
            
        Returns:
            Dictionary mapping dataset names to extracted file paths
        """
        paths = {}
        for name in SNAP_DATASETS:
            try:
                paths[name] = self.download_snap_dataset(name, force=force)
            except Exception as e:
                logger.error(f"Failed to download {name}: {e}")
                paths[name] = None
        return paths
    
    def clear_cache(self) -> None:
        """Clear the in-memory cache of loaded datasets."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_graph(self, name: str) -> Tuple[np.ndarray, Dict[int, List[int]]]:
        """
        Get both node IDs and adjacency list for a dataset.
        
        This is useful for graph-based sampling methods like BFS and Random Walk.
        
        Args:
            name: Name of the dataset
            
        Returns:
            Tuple of (node_ids, adjacency_list)
            where adjacency_list maps node_id -> list of neighbor node_ids
        """
        # Download and extract if needed
        txt_path = self.download_snap_dataset(name)
        
        # Load edge list
        edges = self.load_edge_list(txt_path)
        
        # Build adjacency list
        adjacency: Dict[int, List[int]] = {}
        for source, target in edges:
            if source not in adjacency:
                adjacency[source] = []
            if target not in adjacency:
                adjacency[target] = []
            adjacency[source].append(target)
            adjacency[target].append(source)  # Undirected graph
        
        # Get unique nodes
        node_ids = self.extract_node_ids(edges)
        
        return node_ids, adjacency


def demo():
    """Demonstrate the DatasetLoader functionality."""
    loader = DatasetLoader()
    
    print("Available datasets:")
    for name in loader.list_datasets():
        info = loader.get_dataset_info(name)
        print(f"  - {name}: {info['nodes']} nodes, {info['edges']} edges")
    
    # Load smallest dataset as a test
    print("\nLoading web-Stanford (smallest dataset)...")
    node_ids = loader.get_dataset("web-Stanford")
    
    print(f"Loaded {len(node_ids):,} unique nodes")
    print(f"Node ID range: {node_ids.min():,} to {node_ids.max():,}")
    print(f"First 10 node IDs: {node_ids[:10]}")


if __name__ == "__main__":
    demo()
