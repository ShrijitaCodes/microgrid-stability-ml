"""
Stability Analysis of Interconnected Microgrids - ML/DL Pipeline

A comprehensive Python package for predicting small-signal stability in
interconnected microgrids using machine learning and deep learning models,
with support for privacy-preserving federated learning.

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Academic Research Project"
__license__ = "MIT"

# Core imports
from src.dataset_generation import SyntheticMicrogridGenerator
from src.feature_engineering import FeatureExtractor
from src.models import (
    ModelBenchmark,
    NeuralNetworkTrainer,
    StackingEnsemble,
    FederatedLearning,
)
from src.validation import PandapowerValidator

__all__ = [
    "SyntheticMicrogridGenerator",
    "FeatureExtractor",
    "ModelBenchmark",
    "NeuralNetworkTrainer",
    "StackingEnsemble",
    "FederatedLearning",
    "PandapowerValidator",
]
