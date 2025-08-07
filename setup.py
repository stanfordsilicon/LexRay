#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for CLDR Date Skeleton Converter
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="cldr-date-skeleton-converter",
    version="1.0.0",
    author="LexRay Team",
    description="A sophisticated bilingual date format analyzer for CLDR skeleton patterns",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lexray/cldr-date-skeleton-converter",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Internationalization",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "cldr-converter=src.cli.main:main",
        ],
    },
    package_data={
        "": ["*.md", "*.txt"],
    },
    include_package_data=True,
    zip_safe=False,
) 