# Project Structure Guide

Container Geometry Analyzer v3.11.8 - Complete Directory Organization

## 📦 Top-Level Organization

```
container-geometry-analyzer/
├── README.md                              # 🎯 START HERE - Main project overview
├── STRUCTURE.md                           # This file - Directory organization guide
├── setup.py                               # Package installation configuration
├── requirements.txt                       # Core dependencies
├── requirements-dev.txt                   # Development dependencies
├── pyproject.toml                         # Project metadata (PEP 518)
├── .gitignore                             # Git ignore rules
├── .pre-commit-config.yaml                # Pre-commit hooks configuration
│
├── build_exe.spec                         # PyInstaller specification for .exe
├── build_executable.bat                   # 🪟 Windows build script
├── build_executable.sh                    # 🐧 Linux/macOS build script
│
├── src/                                   # 🎯 Source code directory
│   └── container_geometry_analyzer_gui_v3_11_8.py  # Main application (2300+ lines)
│
├── tests/                                 # 🧪 Testing & validation directory
│   ├── test_transition_detection.py       # Unit tests (20+ tests)
│   ├── benchmark_transition_detection.py  # Performance benchmarks
│   ├── visualize_algorithm_comparison.py  # Visualization tools
│   ├── run_comprehensive_tests.py         # Test runner
│   ├── transition_detection_improvements.py # Reference implementation
│   └── generate_test_data.py              # Test data generation
│
├── data/                                  # 📊 Data files directory
│   ├── sample_2ml_tube_geometry_corrected.csv     # Sample data
│   ├── simulated_container_eppi_50uL.csv          # Sample data
│   ├── centrifuge_tube_*.csv                      # Sample data
│   └── test_data/                         # 20+ test datasets
│       ├── cylinder_*.csv                 # Cylindrical containers
│       ├── frustum_*.csv                  # Conical frustums
│       ├── cone_*.csv                     # Cone shapes
│       ├── sphere_cap_*.csv               # Spherical bottoms
│       └── composite_*.csv                # Multi-segment shapes
│
├── doc/                                   # 📚 Documentation directory
│   ├── INDEX.md                           # 📑 Documentation index (START HERE for docs)
│   ├── README.md                          # Original project README
│   ├── CLAUDE.md                          # AI Assistant development guide
│   ├── CONTRIBUTING.md                    # Contribution guidelines
│   │
│   ├── Algorithm & Analysis/
│   │   ├── ALGORITHM_ANALYSIS_COMPREHENSIVE.md    # Complete algorithm analysis
│   │   ├── TRANSITION_DETECTION_ANALYSIS.md       # Transition detection methods
│   │   └── EDGE_CASES_ANALYSIS.md                 # Edge case handling
│   │
│   ├── Testing & Validation/
│   │   ├── TEST_SUITE_DOCUMENTATION.md           # Testing framework docs
│   │   ├── TEST_RESULTS_SUMMARY.md               # Test results & metrics
│   │   └── data_generation_report.md             # Test data generation
│   │
│   ├── Output Formats/
│   │   ├── EXPORT_FORMATS_SUMMARY.md             # All export formats
│   │   ├── HXX_FORMAT_DOCUMENTATION.md           # HXX format details
│   │   ├── HXX_SUMMARY.md                        # HXX summary
│   │   └── DIRECTX_FORMAT_DOCUMENTATION.md       # DirectX .x format
│   │
│   ├── User Guides/
│   │   ├── IFU.md                                # Instructions for use
│   │   ├── IFU_SUMMARY.md                        # IFU summary
│   │   ├── IFU_UPDATE_GUIDE.md                   # Update guide
│   │   └── Extracted Container Dimensions.md    # Analysis results
│   │
│   └── Implementation/
│       └── IMPROVEMENTS_IMPLEMENTED.md           # Improvements list
│
├── _old/                                  # 🗂️ Obsolete/generated files
│   ├── ContainerReport_*.pdf              # Generated PDF reports
│   ├── test_results.json                  # Test result JSON
│   └── [other generated outputs]
│
└── dist/ (generated)                      # 📦 Distribution directory (after build)
    └── ContainerGeometryAnalyzer/         # Built executable
        └── ContainerGeometryAnalyzer.exe  # Windows standalone .exe
        └── ContainerGeometryAnalyzer      # Linux/macOS standalone
```

## 📝 File Descriptions

### Root Configuration Files
- **README.md** - Main project documentation with quick start and features
- **STRUCTURE.md** - This file, describing the project organization
- **setup.py** - Package setup and installation configuration
- **requirements.txt** - Core runtime dependencies (pandas, numpy, scipy, etc.)
- **requirements-dev.txt** - Development dependencies (pytest, pyinstaller, etc.)
- **pyproject.toml** - Modern Python project metadata (PEP 518)
- **.gitignore** - Git ignore rules for version control
- **.pre-commit-config.yaml** - Pre-commit hooks for code quality

### Build Configuration
- **build_exe.spec** - PyInstaller specification file for creating .exe
- **build_executable.bat** - Windows batch script for building executable
- **build_executable.sh** - Bash script for Linux/macOS executable building

### Source Code (`src/`)
- **container_geometry_analyzer_gui_v3_11_8.py** - Main application (~2300 lines)
  - Lines 1-86: Imports and configuration
  - Lines 88-169: AnalysisJob class for tracking
  - Lines 171-220: Utility functions (including new generate_output_filename)
  - Lines 222-340: Core geometric functions
  - Lines 341-511: Transition detection algorithms
  - Lines 512-700: Segmentation and fitting
  - Lines 700-1050: Profile generation
  - Lines 1051-1491: 3D model export (STL, HXX, DirectX)
  - Lines 1524+: PDF report generation
  - Lines 1700+: Visualization tools
  - Lines 2027-2157: GUI launch function
  - Lines 2159+: CLI with argparse

### Tests (`tests/`)
- **test_transition_detection.py** - 20+ unit tests
  - TestGeometricFunctions - Volume calculations
  - TestSyntheticData - Perfect and noisy data
  - TestEdgeCases - Boundary conditions
  - TestAdaptiveThreshold - SNR-based thresholds
  - TestRealWorldScenarios - Actual container data
  - TestComparisonMetrics - Legacy vs improved

- **benchmark_transition_detection.py** - Performance benchmarking
  - 8 synthetic test cases
  - Real sample data analysis
  - Accuracy and timing metrics
  - CSV export of results

- **visualize_algorithm_comparison.py** - Visualization tools
  - Derivative comparisons
  - Threshold demonstrations
  - Method comparisons
  - PNG exports

- **run_comprehensive_tests.py** - Test runner
  - Runs all test suites
  - Generates reports

- **transition_detection_improvements.py** - Reference implementation
  - Multiple detection methods
  - Diagnostic tools
  - Comparison utilities

- **generate_test_data.py** - Test data generation
  - Synthetic container generation
  - Noise addition
  - Data validation

### Data (`data/`)
- **Sample CSVs** - User-provided or standard container data
  - sample_2ml_tube_geometry_corrected.csv
  - simulated_container_eppi_50uL.csv
  - centrifuge_tube_*.csv

- **test_data/** - 20+ CSV files for testing
  - Cylinders: small, medium, large, fine/sparse sampling
  - Frustums: narrow-to-wide, expanding beaker
  - Cones: centrifuge tip, pipette tip
  - Spherical caps: flask bottom, vial bottom
  - Composites: centrifuge, eppendorf, flask combinations
  - Noise variants: high noise, simulated error

### Documentation (`doc/`)
- **INDEX.md** - Documentation index (start here)
- **Core Guides**
  - README.md - Original project README
  - CLAUDE.md - AI Assistant guide
  - CONTRIBUTING.md - Contribution guidelines

- **Technical Analysis**
  - ALGORITHM_ANALYSIS_COMPREHENSIVE.md - Deep algorithmic analysis
  - TRANSITION_DETECTION_ANALYSIS.md - Transition detection methods
  - EDGE_CASES_ANALYSIS.md - Edge case handling

- **Testing**
  - TEST_SUITE_DOCUMENTATION.md - Testing framework
  - TEST_RESULTS_SUMMARY.md - Test results and metrics
  - data_generation_report.md - Test data generation

- **Export Formats**
  - EXPORT_FORMATS_SUMMARY.md - Overview of all formats
  - HXX_FORMAT_DOCUMENTATION.md - Hexahedral mesh format
  - HXX_SUMMARY.md - HXX format summary
  - DIRECTX_FORMAT_DOCUMENTATION.md - DirectX .x format

- **User Guides**
  - IFU.md - Full Instructions for Use
  - IFU_SUMMARY.md - Quick reference
  - IFU_UPDATE_GUIDE.md - Documentation update guide

- **Results**
  - Extracted Container Dimensions.md - Analysis results

### Obsolete/Generated (`_old/`)
- **ContainerReport_*.pdf** - Generated PDF reports from previous runs
- **test_results.json** - Test execution results
- Other generated output files that are not part of the source

### Distribution (`dist/` - after build)
- **ContainerGeometryAnalyzer/** - Complete standalone distribution
  - Windows: ContainerGeometryAnalyzer.exe
  - Linux/macOS: ContainerGeometryAnalyzer executable
  - All dependencies bundled

## 🎯 Key Directories for Different Roles

### For Users
```
README.md                          # Quick start
doc/IFU.md                        # Instructions
data/                             # Sample data
build_executable.bat/.sh          # Build standalone
```

### For Developers
```
src/                              # Main code
tests/                            # Unit tests
doc/CLAUDE.md                     # Dev guide
doc/ALGORITHM_ANALYSIS*           # Algorithm details
requirements-dev.txt              # Dev dependencies
```

### For CI/CD
```
setup.py                          # Install config
requirements*.txt                 # Dependencies
tests/                            # Automated tests
build_exe.spec                    # .exe creation
```

### For Documentation
```
doc/INDEX.md                      # Doc index (start)
doc/                              # All documentation
README.md                         # Main README
```

## 📊 File Statistics

### Code Files
- Main application: 1 file (~2300 lines)
- Test files: 7 files (~2000 lines total)
- Total code: ~4500 lines

### Data Files
- Sample CSVs: 3 files
- Test datasets: 20+ files (in test_data/)
- Total data points: 1000+ across all test cases

### Documentation
- Documentation files: 20+ markdown files
- Total documentation: 15,000+ lines
- Comprehensive coverage of all aspects

## 🔄 Workflow Examples

### Running the Application
```bash
# GUI mode
python src/container_geometry_analyzer_gui_v3_11_8.py

# CLI mode
python src/container_geometry_analyzer_gui_v3_11_8.py data/sample_2ml_tube_geometry_corrected.csv -o ./output
```

### Building Executable
```bash
# Windows
build_executable.bat

# Linux/macOS
./build_executable.sh
```

### Running Tests
```bash
# All unit tests
python tests/test_transition_detection.py

# Benchmarks
python tests/benchmark_transition_detection.py

# Visualizations
python tests/visualize_algorithm_comparison.py
```

### Development Workflow
```bash
# Setup
pip install -e ".[dev]"

# Make changes to src/
vim src/container_geometry_analyzer_gui_v3_11_8.py

# Run tests
python tests/test_transition_detection.py

# Commit and push
git add -A
git commit -m "description"
git push
```

## 📈 Growth & Maintenance

### Adding New Features
1. Modify `src/container_geometry_analyzer_gui_v3_11_8.py`
2. Add tests to `tests/test_transition_detection.py`
3. Update documentation in `doc/`
4. Update version in `src/container_geometry_analyzer_gui_v3_11_8.py` line 2

### Adding Test Data
1. Create CSV file in `data/test_data/`
2. Add to `tests/generate_test_data.py` if generated
3. Document in `doc/data_generation_report.md`

### Documenting Changes
1. Update relevant `doc/*.md` files
2. Update version history in README.md
3. Update `doc/IMPROVEMENTS_IMPLEMENTED.md`

## 🎓 Learning Path

1. **Read**: [README.md](README.md) - Overview
2. **Explore**: [doc/INDEX.md](doc/INDEX.md) - Documentation index
3. **Learn**: [doc/IFU.md](doc/IFU.md) - How to use
4. **Understand**: [doc/TRANSITION_DETECTION_ANALYSIS.md](doc/TRANSITION_DETECTION_ANALYSIS.md) - Algorithms
5. **Develop**: [doc/CLAUDE.md](doc/CLAUDE.md) - Code details
6. **Contribute**: [doc/CONTRIBUTING.md](doc/CONTRIBUTING.md) - Guidelines

## 📞 Quick Navigation

| Goal | Starting Point |
|------|----------------|
| Use the software | [README.md](README.md) |
| Understand algorithms | [doc/ALGORITHM_ANALYSIS_COMPREHENSIVE.md](doc/ALGORITHM_ANALYSIS_COMPREHENSIVE.md) |
| Run tests | [tests/](tests/) |
| Build executable | [build_executable.bat](build_executable.bat) or [build_executable.sh](build_executable.sh) |
| See test results | [doc/TEST_RESULTS_SUMMARY.md](doc/TEST_RESULTS_SUMMARY.md) |
| Develop features | [doc/CLAUDE.md](doc/CLAUDE.md) |
| Export formats | [doc/EXPORT_FORMATS_SUMMARY.md](doc/EXPORT_FORMATS_SUMMARY.md) |
| All documentation | [doc/INDEX.md](doc/INDEX.md) |

---

**Last Updated**: 2025-11-19
**Version**: 3.11.8
**Maintainers**: Container Geometry Analyzer Team
