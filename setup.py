from setuptools import find_packages, setup
from pathlib import Path

README = Path(__file__).with_name("README.md").read_text(encoding="utf-8")

setup(
    name="swcol",
    version="0.0.11",  # bump when changing requirements
    description="Switch: Electricity Planning Model applied to Colombia",
    package_dir={"": "app"},
    packages=find_packages(where="app"),
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/Greater-Gold/switch-colombia",
    author="Juan José Dorado",
    author_email="juanjosedoradom@gmail.com",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",   # <-- match your license
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "numpy",
        "pandas",
        "matplotlib",
        "plotly>=5.0",
        "nbformat>=4.2",
        "kaleido",
        "geopandas>=0.14",
        "tqdm>=4.66",
        "ipywidgets",
        "ipykernel",
    ],
    python_requires=">=3.9",
    include_package_data=True,
)
