"""
Setup script for Container Geometry Analyzer

Install in development mode:
    pip install -e .

Install with development dependencies:
    pip install -e .[dev]
"""

from setuptools import setup, find_packages
import os

# Read version from the main script
version = "3.11.8"

# Read long description from README
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f
                   if line.strip() and not line.startswith('#')]

# Read dev requirements
with open(os.path.join(here, 'requirements-dev.txt'), encoding='utf-8') as f:
    dev_requirements = [line.strip() for line in f
                       if line.strip() and not line.startswith('#')
                       and not line.startswith('-r')]

setup(
    name='container-geometry-analyzer',
    version=version,
    description='Analyze container geometry from volume-height data and generate 3D models',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Marco Horstmann',
    author_email='',  # Add email if desired
    url='https://github.com/yourusername/container-geometry-analyzer',  # Update with actual URL
    license='',  # Add license type when LICENSE file is created

    # Package configuration
    py_modules=['container_geometry_analyzer_gui_v3_11_8'],
    packages=find_packages(),
    include_package_data=True,

    # Dependencies
    install_requires=requirements,
    extras_require={
        'dev': dev_requirements,
    },

    # Python version requirement
    python_requires='>=3.7',

    # Entry points for command-line scripts
    entry_points={
        'console_scripts': [
            'container-analyzer=container_geometry_analyzer_gui_v3_11_8:main',
        ],
    },

    # PyPI classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Visualization',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],

    # Keywords for PyPI
    keywords='geometry analysis container 3d-modeling stl pdf scientific',

    # Project URLs
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/container-geometry-analyzer/issues',
        'Source': 'https://github.com/yourusername/container-geometry-analyzer',
        'Documentation': 'https://github.com/yourusername/container-geometry-analyzer/blob/main/README.md',
    },
)
