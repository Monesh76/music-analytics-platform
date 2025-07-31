#!/usr/bin/env python3
"""
Setup file for Dataflow pipeline dependencies.
"""

from setuptools import setup, find_packages

setup(
    name='music-analytics-pipeline',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'apache-beam[gcp]==2.54.0',
        'google-cloud-pubsub==2.18.4',
        'google-cloud-bigquery==3.11.4',
        'google-cloud-storage==2.10.0',
        'pydantic==1.10.13',
        'structlog==23.1.0'
    ],
    python_requires='>=3.9',
) 