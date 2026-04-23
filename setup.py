from setuptools import setup, find_packages

setup(
    name="insight-fabric",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.11",
    install_requires=[
        "pbixray>=0.5.0",
        "openpyxl>=3.1.0",
        "pandas>=2.0.0",
        "pyarrow>=14.0.0",
        "PyQt6>=6.6.0",
        "anthropic>=0.25.0",
        "openai>=1.12.0",
        "google-generativeai>=0.8.0",
        "pyyaml>=6.0",
        "python-docx>=1.1.0",
        "markdown>=3.5",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
        "tqdm>=4.66.0",
    ],
    extras_require={
        "dev": ["pytest>=7.4.0", "pytest-qt", "black", "flake8"],
    },
    entry_points={
        "console_scripts": [
            "insight-fabric-analyze=power_bi_analysis.cli:main",
            "insight-fabric-rdl-analyze=power_bi_analysis.rdl_cli:main",
            "insight-fabric-configure=power_bi_analysis.config:configure_interactive",
            "insight-fabric-gui=power_bi_analysis.gui.main_window:main",
            "insight-fabric-compare=power_bi_analysis.compare_cli:main",
        ],
    },
)