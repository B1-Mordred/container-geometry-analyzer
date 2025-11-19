# Container Geometry Analyzer  
### Volume–Height Analysis • Segment Detection • STL Generation • PDF Reporting  
Version **3.11.8 (FIXED)**

## Overview
The **Container Geometry Analyzer** is a Python-based analysis tool that reconstructs 3D geometry of laboratory containers from **Volume–Height calibration data**.  
It automatically detects geometric segments, creates a smooth radius profile, validates reconstructed volume accuracy, and exports:

- **Watertight STL models**  
- **Comprehensive PDF reports**  
- **Interactive GUI**  
- **Command-line mode**  

## Key Features
### Analysis & Geometry Reconstruction
- Automatic cylinder/frustum detection  
- Radius estimation from differential volume  
- Smooth Hermite spline transitions  
- Gaussian smoothing  
- Volume preservation validation  

### Outputs
#### STL Model
- Bottom always closed  
- Watertight  
- Automatic angular resolution  
- Fixed normals  

#### PDF Report
- Executive summary  
- Segment detection  
- Fit quality  
- Volume error  
- Radius profile plots  
- Cross-section analysis  
- Processing configuration  

## Installation
### Requirements
- Python 3.9–3.13  
- Packages:
```
pip install pandas numpy scipy matplotlib trimesh reportlab
```

## Usage
### GUI
```
python container_geometry_analyzer_gui_v3_11_8_FIXED.py
```

### CLI
```
python container_geometry_analyzer_gui_v3_11_8_FIXED.py data.csv
```

## Output Files
### STL
```
<inputname>_model_<timestamp>.stl
```

### PDF
- Summary  
- Segment table  
- Fit quality  
- Radius vs height  
- Volume error  
- Configuration  

## Temporary File Handling
- Plots stored in system temp directory  
- Not removed until PDF is finalized  

## Known Limitations
- Very noisy data reduces accuracy  
- Very sparse datasets may produce approximate fits  

## Version History
### 3.11.8 (FIXED)
- Fixed premature plot deletion (PDF error)  
- Ensured stable temp file handling  
- Improved export directory handling  
- Enhanced logging  

### 3.11.7
- Production-ready  
- STL bottom closure  
- Improved temp directory handling  

## Support
For further enhancements or integrations (HXX formats, robotics systems, pipeline automation), support is available.
