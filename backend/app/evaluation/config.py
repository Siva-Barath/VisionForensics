"""
Evaluation and Benchmarking Configuration
"""
from typing import List
from pydantic import BaseModel

class EvaluationConfig(BaseModel):
    # Datasets
    default_dataset_path: str = "data/evaluation/default_benchmark"
    
    # Robustness Testing
    blur_levels: List[int] = [3, 5, 7]
    noise_levels: List[float] = [0.01, 0.05, 0.1]
    jpeg_qualities: List[int] = [90, 70, 50]
    
    # Validation settings
    require_docs: bool = True
    require_tests: bool = True
    min_coverage_pct: float = 80.0
