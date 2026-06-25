from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="microgrid-stability-ml",
    version="1.0.0",
    author="",
    author_email="",
    description="Machine Learning for Small-Signal Stability Prediction in Interconnected Microgrids",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/user/microgrid-stability-ml",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Development Status :: 4 - Beta",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "scipy>=1.7.0",
        "scikit-learn>=0.24.0",
        "tensorflow>=2.8.0",
        "xgboost>=1.5.0",
        "matplotlib>=3.4.0",
        "seaborn>=0.11.0",
        "pandapower>=2.8.0",
        "joblib>=1.0.0",
        "tqdm>=4.62.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-cov>=2.12.0",
            "black>=21.6b0",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ],
        "notebooks": [
            "jupyter>=1.0.0",
            "jupyterlab>=3.0.0",
            "ipywidgets>=7.6.0",
        ],
    },
    project_urls={
        "Bug Tracker": "https://github.com/user/microgrid-stability-ml/issues",
        "Documentation": "https://github.com/user/microgrid-stability-ml/blob/main/ARCHITECTURE.md",
        "Source Code": "https://github.com/user/microgrid-stability-ml",
    },
)
