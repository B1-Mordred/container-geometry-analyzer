# Container Geometry Analyzer

## Overview

The **Container Geometry Analyzer** is a Python-based tool designed to analyze the geometry of a container using volume-height data. It processes CSV files containing these measurements to perform a detailed geometric analysis, generate a smooth 2D profile, create a watertight 3D model (STL), and produce a comprehensive PDF report summarizing the findings. The tool can be operated through a simple Graphical User Interface (GUI) or via the Command-Line Interface (CLI).

## Features

*   **CSV Data Processing**: Loads and validates volume-height data from a `.csv` file.
*   **Geometric Segmentation**: Automatically segments the container's profile into cylinders and frustums (truncated cones) based on the data.
*   **Smooth Profile Generation**: Creates a C¹ continuous 2D profile of the container using Hermite cubic splines for smooth transitions between geometric segments.
*   **3D Model Export**: Generates a watertight 3D mesh of the container in `.stl` format, suitable for 3D printing and CAD applications. The model features a guaranteed closed bottom for manifold geometry.
*   **Comprehensive PDF Reporting**: Produces a detailed, multi-page PDF report including an executive summary, processing statistics, geometric segment analysis, and visualizations.
*   **Data Visualization**: Generates multiple plots to visualize the analysis, including volume profiles, radius comparisons, and cross-sectional area analysis.
*   **Dual-Mode Operation**: Can be run using a user-friendly GUI (via Tkinter) or directly from the command line for scripting and automation.

## Dependencies

The script relies on several open-source Python libraries.

*   `pandas`
*   `numpy`
*   `scipy`
*   `matplotlib`
*   `reportlab`
*   `trimesh`
*   `tkinter` (usually included with standard Python installations)

## Getting Started

### Prerequisites

*   Python 3.6 or higher.
*   `pip` for installing packages.

### Installation

1.  Clone or download the repository/script.
2.  Install the required libraries using pip.
    ```bash
    pip install pandas numpy scipy matplotlib reportlab trimesh
    ```

### Input Data Format

The tool requires a CSV file as input. The file must contain at least two columns: one for height and one for volume. The script will automatically detect columns with "height" and "volume" in their names (case-insensitive).

Example `data.csv`:
```csv
Height (mm),Volume (ml)
0,0
10,5.2
20,10.5
30,15.8
...
```

## Usage

You can run the analyzer in two ways:

### 1. GUI Mode

To use the graphical interface, run the script without any command-line arguments.

```bash
python container_geometry_analyzer_gui_v3_11_8.py
```

This will launch a window with a button to "Select Volume-Height CSV". Click the button, choose your input file, and the analysis will start automatically. Results and generated file paths will be displayed in a message box upon completion.

### 2. CLI Mode

For automation or batch processing, you can run the script from the command line, providing the path to the input CSV file as an argument.

```bash
python container_geometry_analyzer_gui_v3_11_8.py /path/to/your/data.csv
```

The script will print progress and summary information to the console. The output files (PDF report and STL model) will be saved in the same directory where the script is executed.

## Output Files

Upon successful analysis, the script generates the following files:

1.  **PDF Report (`ContainerReport_[timestamp].pdf`)**: A detailed report containing:
    *   Executive Summary with key metrics.
    *   Job execution details (timing, steps, warnings).
    *   Statistical analysis of height, volume, and cross-sectional area.
    *   A table of detected geometric segments and their properties.
    *   Visualizations of the container's profile and analysis data.
2.  **STL Model (`[basename]_model_[timestamp].stl`)**: A watertight 3D model of the container with a closed bottom, ready for use in 3D software.

## Author

*   Marco Horstmann

## License


