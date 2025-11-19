# Container Geometry Analyzer

A sophisticated Python-based scientific tool for analyzing container geometry from volume-height measurement data, generating watertight 3D models, and producing professional PDF reports.

![Version](https://img.shields.io/badge/version-3.11.8-blue)
![Python](https://img.shields.io/badge/python-3.7+-blue)
![License](https://img.shields.io/badge/license-TBD-green)

## 🚀 Quick Start

### GUI Mode (No Command Line Required)
```bash
python src/container_geometry_analyzer_gui_v3_11_8.py
```

### CLI Mode with Output Directory Selection
```bash
# Analyze with custom output directory
python src/container_geometry_analyzer_gui_v3_11_8.py data.csv -o ./results

# Show help
python src/container_geometry_analyzer_gui_v3_11_8.py --help
```

### Portable Executable (Air-Gapped Environments)
```bash
# Windows
build_executable.bat

# Linux/macOS
./build_executable.sh

# Then run the standalone executable
./dist/ContainerGeometryAnalyzer/ContainerGeometryAnalyzer.exe
```

## ✨ Key Features

- **Multi-Shape Detection**: Recognizes cylinders, frustums, cones, and sphere caps
- **Multi-derivative Transition Detection**: Intelligent segmentation using combined 1st and 2nd derivatives
- **Adaptive SNR-Based Thresholding**: Automatic sensitivity adjustment based on data quality
- **Watertight STL Generation**: Guaranteed closed 3D meshes for 3D printing or CAD
- **Professional PDF Reports**: Comprehensive multi-page reports with statistics and visualizations
- **Multiple Export Formats**:
  - STL (Standard Tessellation Language) - for 3D printing
  - HXX (Hexahedral VTK) - for finite element analysis
  - DirectX .x - for visualization and gaming engines
- **Dual-Mode Operation**: Both GUI (Tkinter) and CLI interfaces
- **Air-Gapped Compatible**: Create standalone .exe for offline use

## 📊 Performance Specifications

### Processing Speed
- **Data Loading & Validation**: ~50 ms
- **Area Computation**: ~30 ms
- **Transition Detection**: ~100-150 ms (improved method; legacy: ~80-100 ms)
- **Profile Generation & Smoothing**: ~60 ms
- **3D Model Generation**: ~200-400 ms (depends on profile resolution)
- **PDF Report Generation**: ~500-800 ms
- **Total Analysis Time**: 1-2 seconds for typical containers (50-200 data points)

### Memory Requirements
- **Minimum**: 256 MB
- **Recommended**: 512 MB - 1 GB
- **Matplotlib Plots**: ~50-100 MB per visualization (automatically cleaned up)

### Data Capacity
- **Maximum Data Points**: 10,000+ (tested up to 50,000)
- **CSV File Size**: Practical limit ~10 MB
- **Output File Sizes**:
  - STL: 2-10 MB (depends on profile resolution)
  - PDF: 5-15 MB (with high-resolution plots)

### Accuracy
- **Transition Detection**: ~85-90% accuracy on complex shapes (improved method)
- **Geometric Fitting**: R² > 0.95 for well-behaved data
- **Volume Preservation**: < 2% error vs theoretical volume

## ⚠️ Limitations

### Shape Support
- ✅ **Supported**:
  - Cylinders
  - Frustums (conical tapers)
  - **Sphere caps** (spherical bottoms - common in lab containers)
  - Cones
- ❌ **Not Supported**:
  - Full spheres (only caps are supported)
  - Ellipsoids, irregular shapes, non-axisymmetric containers

### Data Requirements
- **Minimum Data Points**: 12 (recommended: 50+)
- **Required Columns**: Must contain "height" and "volume" in CSV headers (case-insensitive)
- **Fixed Units**: Assumes mm for height, ml for volume
- **Single Container**: Processes one container per analysis

### Geometric Assumptions
- **Circular Cross-Section**: Only works for rotationally symmetric containers
- **2D Axisymmetric Profile**: 3D model generated from 2D profile
- **Smooth Transitions**: Abrupt geometry changes require fine data resolution

### Algorithm Constraints
- **Transition Detection**: Works best with ≥ 3 segments; may miss subtle shape changes
- **Noise Sensitivity**: Adaptive thresholding reduces but cannot eliminate noise effects
- **Extreme Aspect Ratios**: Very tall/narrow or short/wide containers may require parameter tuning

### Software Dependencies
- **Optional**: All dependencies degrade gracefully
  - Without trimesh: No 3D model export
  - Without reportlab: No PDF generation
  - Without tkinter: CLI mode only
  - Without matplotlib: No visualization

## 📦 Installation

### Option 1: Standard Installation
```bash
# Install dependencies
pip install pandas numpy scipy matplotlib reportlab trimesh

# Run the application
python src/container_geometry_analyzer_gui_v3_11_8.py
```

### Option 2: Development Installation
```bash
# Install in development mode with all dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/

# Run benchmarks
python tests/benchmark_transition_detection.py
```

### Option 3: Portable Executable (Recommended for Air-Gapped)
```bash
# Windows
build_executable.bat

# Linux/macOS
./build_executable.sh
```

The portable executable includes all dependencies and requires no Python installation on the target machine.

## 📁 Project Structure

```
container-geometry-analyzer/
├── README.md                          # This file
├── src/
│   └── container_geometry_analyzer_gui_v3_11_8.py  # Main application
├── tests/
│   ├── test_transition_detection.py   # Unit tests (20+)
│   ├── benchmark_transition_detection.py
│   ├── visualize_algorithm_comparison.py
│   ├── transition_detection_improvements.py
│   └── generate_test_data.py
├── data/
│   ├── sample_2ml_tube_geometry_corrected.csv
│   ├── simulated_container_eppi_50uL.csv
│   └── test_data/                     # 20+ test datasets
├── doc/                               # Detailed documentation
│   ├── ALGORITHM_ANALYSIS_COMPREHENSIVE.md
│   ├── TRANSITION_DETECTION_ANALYSIS.md
│   ├── TEST_RESULTS_SUMMARY.md
│   ├── TEST_SUITE_DOCUMENTATION.md
│   ├── EXPORT_FORMATS_SUMMARY.md
│   ├── HXX_FORMAT_DOCUMENTATION.md
│   ├── DIRECTX_FORMAT_DOCUMENTATION.md
│   ├── CLAUDE.md                     # AI Assistant guide
│   └── [other documentation]
├── build_exe.spec                     # PyInstaller specification
├── build_executable.bat               # Windows build script
├── build_executable.sh                # Linux/macOS build script
├── requirements.txt                   # Core dependencies
├── requirements-dev.txt               # Development dependencies
├── setup.py                           # Package configuration
└── _old/                              # Obsolete generated files

```

## 🔧 Configuration

### Input CSV Format
Required columns (case-insensitive):
- Height column (e.g., "Height (mm)", "height_mm")
- Volume column (e.g., "Volume (ml)", "volume_ml")

Example CSV:
```csv
Height (mm),Volume (ml)
0.0,0.0
0.634,0.02
1.268,0.04
2.34,0.12
...
```

### Algorithm Parameters

Key parameters in `src/container_geometry_analyzer_gui_v3_11_8.py`:

```python
DEFAULT_PARAMS = {
    'transition_detection_method': 'legacy',  # or 'improved'
    'use_adaptive_threshold': True,           # SNR-based adjustment
    'percentile': 90,                         # Detection sensitivity
    'variance_threshold': 0.14,               # Segment validation
    'angular_resolution': 48,                 # STL mesh quality (higher = more faces)
}
```

**Method Selection**:
- `'improved'`: Multi-derivative + adaptive (recommended for real-world data)
- `'legacy'`: Savitzky-Golay filter (faster, better for clean synthetic data)

## 💾 Output Filenames

Output files use format: `{input_basename}-{YYYYMMDD_HHMMSS}-{TYPE}.{ext}`

Example for input `sample.csv`:
- `sample-20251119_143022-STL.stl`
- `sample-20251119_143022-HXX.hxx`
- `sample-20251119_143022-DirectX.x`
- `sample-20251119_143022-PDF.pdf`

This format ensures:
- ✅ Multiple analyses don't overwrite each other
- ✅ Clear file type identification
- ✅ Chronological sorting in file explorers
- ✅ Easy batch processing with timestamps

## 🧪 Testing & Validation

### Run Unit Tests
```bash
python tests/test_transition_detection.py
```

Tests included:
- Geometric function validation (20+ tests)
- Synthetic data (perfect cylinders, frustums, multi-segment)
- Edge cases (noise, sparse data, step changes)
- Algorithm comparison (improved vs legacy)
- Real-world container data

### Run Performance Benchmarks
```bash
python tests/benchmark_transition_detection.py
```

Benchmarks:
- 8 synthetic test cases with known ground truth
- Real sample data analysis
- Accuracy and timing measurements
- CSV export of results

### Generate Visualizations
```bash
python tests/visualize_algorithm_comparison.py
```

Generates:
- Derivative comparison plots
- Adaptive threshold demonstrations
- Method comparison visualizations

## 📚 Documentation

Detailed documentation is available in the `doc/` directory:

| Document | Purpose |
|----------|---------|
| [TRANSITION_DETECTION_ANALYSIS.md](doc/TRANSITION_DETECTION_ANALYSIS.md) | Algorithm details and theory |
| [TEST_RESULTS_SUMMARY.md](doc/TEST_RESULTS_SUMMARY.md) | Test execution results and metrics |
| [EXPORT_FORMATS_SUMMARY.md](doc/EXPORT_FORMATS_SUMMARY.md) | 3D export format specifications |
| [HXX_FORMAT_DOCUMENTATION.md](doc/HXX_FORMAT_DOCUMENTATION.md) | Hexahedral mesh format details |
| [DIRECTX_FORMAT_DOCUMENTATION.md](doc/DIRECTX_FORMAT_DOCUMENTATION.md) | DirectX .x format specifications |
| [TEST_SUITE_DOCUMENTATION.md](doc/TEST_SUITE_DOCUMENTATION.md) | Testing framework and test cases |
| [ALGORITHM_ANALYSIS_COMPREHENSIVE.md](doc/ALGORITHM_ANALYSIS_COMPREHENSIVE.md) | Comprehensive algorithm analysis |
| [CLAUDE.md](doc/CLAUDE.md) | AI Assistant guide and development guidelines |
| [CONTRIBUTING.md](doc/CONTRIBUTING.md) | Contribution guidelines |

## 🏗️ Building Portable Executable

### For Windows
```bash
build_executable.bat
```

This creates:
- Single executable: `dist\ContainerGeometryAnalyzer.exe`
- Complete distribution: `dist\ContainerGeometryAnalyzer\`

### For Linux/macOS
```bash
./build_executable.sh
```

This creates:
- Executable: `dist/ContainerGeometryAnalyzer/ContainerGeometryAnalyzer`

### Usage in Air-Gapped Environment
1. Copy the `dist/ContainerGeometryAnalyzer/` folder to the target machine
2. No Python installation required on target machine
3. Run normally: `ContainerGeometryAnalyzer.exe data.csv -o output`

## 🔧 Development

### Setup Development Environment
```bash
# Clone repository
git clone <repository-url>
cd container-geometry-analyzer

# Install dependencies
pip install -r requirements-dev.txt

# Install in development mode
pip install -e ".[dev]"

# Run all tests
python tests/test_transition_detection.py
python tests/benchmark_transition_detection.py
python tests/visualize_algorithm_comparison.py
```

### Code Structure
- **Core Algorithm**: Lines 198-511 in `src/container_geometry_analyzer_gui_v3_11_8.py`
- **3D Generation**: Lines 1051-1491
- **PDF Reporting**: Lines 1524+
- **GUI**: Lines 2027-2157
- **CLI**: Lines 2159+

### Modifying the Application
See [doc/CLAUDE.md](doc/CLAUDE.md) for:
- Detailed code walkthrough
- Common modification patterns
- Algorithm tuning guidelines
- Testing strategies

## 📊 Validation Evidence

### Algorithm Accuracy
- Improved method: 85-90% accuracy on complex shapes (+30% vs legacy)
- Geometric fitting: R² > 0.95 for well-behaved data
- See: [doc/TEST_RESULTS_SUMMARY.md](doc/TEST_RESULTS_SUMMARY.md)

### Performance Metrics
- Processing: 1-2 seconds for typical containers
- STL generation: 200-400 ms
- PDF creation: 500-800 ms
- See: [doc/ALGORITHM_ANALYSIS_COMPREHENSIVE.md](doc/ALGORITHM_ANALYSIS_COMPREHENSIVE.md)

### Test Coverage
- 20+ unit tests covering all major functions
- 8 synthetic test cases with ground truth
- 20+ edge case datasets
- See: [doc/TEST_SUITE_DOCUMENTATION.md](doc/TEST_SUITE_DOCUMENTATION.md)

## ⚙️ System Requirements

### Minimum
- **OS**: Windows 7+, macOS 10.9+, Linux (any modern distro)
- **Python**: 3.7 or later
- **RAM**: 256 MB
- **Disk**: 500 MB (for application + dependencies)

### Recommended
- **Python**: 3.9 or later
- **RAM**: 1 GB
- **Disk**: 2 GB (for development with test data)

### Portable Executable
- **No Python installation required**
- **Self-contained with all dependencies**
- **One-time ~200-400 MB download**

## 🤝 Contributing

Contributions are welcome! See [doc/CONTRIBUTING.md](doc/CONTRIBUTING.md) for guidelines.

## 📝 License

TBD - See LICENSE file when added

## 👨‍💻 Author

**Marco Horstmann**

## 📞 Support

For issues, questions, or suggestions:
1. Check existing documentation in `doc/` directory
2. Review test cases in `tests/` directory
3. Consult [doc/CLAUDE.md](doc/CLAUDE.md) for technical details
4. Submit issues on GitHub

## 🔄 Version History

- **v3.11.8** (Current)
  - Output directory selection support
  - New filename format with timestamps and file types
  - Portable .exe support
  - Comprehensive documentation reorganization
  - Command-line argument parsing with argparse
  - GUI improvements for path selection

- **v3.11.7-v3.11.3**
  - Improved transition detection algorithms
  - PDF report enhancements
  - Export format additions (HXX, DirectX)
  - Comprehensive test suite

- **Earlier versions**
  - Core segmentation and STL export functionality

## 🎯 Future Roadmap

Potential enhancements:
- [ ] Batch processing mode for multiple containers
- [ ] Ellipsoidal shape support
- [ ] Interactive parameter tuning GUI
- [ ] Database integration for result storage
- [ ] Real-time visualization during analysis
- [ ] REST API for integration with other systems
- [ ] Container library (standard lab containers)

---

**For detailed technical information, see the documentation in the `doc/` directory.**
