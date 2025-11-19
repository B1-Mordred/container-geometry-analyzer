# CLAUDE.md - AI Assistant Guide for Container Geometry Analyzer

**Last Updated**: 2025-11-19
**Version**: 3.11.8
**Author**: Marco Horstmann

## Project Overview

The **Container Geometry Analyzer** is a sophisticated Python-based scientific tool designed to analyze container geometry from volume-height measurement data. The tool performs geometric analysis, generates smooth 3D models, and produces comprehensive PDF reports.

### Primary Purpose
- Analyze laboratory containers (tubes, vials, etc.) from volume-height CSV data
- Automatically segment container geometry into cylinders and frustums
- Generate watertight 3D STL models for CAD/3D printing
- Produce professional PDF reports with statistical analysis and visualizations

### Key Features
1. **Geometric Segmentation**: Automatically detects cylinders and frustums using adaptive algorithms
2. **Smooth Profile Generation**: Creates C¹ continuous profiles using Hermite cubic splines
3. **3D Model Export**: Generates watertight STL meshes with guaranteed closed bottoms
4. **PDF Reporting**: Comprehensive multi-page reports with statistics and visualizations
5. **Dual-Mode Operation**: GUI (Tkinter) and CLI interfaces

## Codebase Structure

### File Organization
```
container-geometry-analyzer/
├── container_geometry_analyzer_gui_v3_11_8.py  # Main application (single file)
├── README.md                                    # User documentation
├── CLAUDE.md                                    # This file (AI assistant guide)
├── sample_2ml_tube_geometry_corrected.csv      # Sample input data
├── simulated_container_eppi_50uL.csv           # Sample input data
└── ContainerReport_*.pdf                        # Generated output files
```

### Architecture Pattern: Single-File Modular Design

The application uses a **single-file architecture** with functional modules organized by responsibility:

#### 1. Core Analysis Pipeline (Lines 198-547)
- `load_data_csv()`: CSV loading and validation
- `compute_areas()`: Cross-sectional area calculation from dV/dh
- `segment_and_fit_optimized()`: Main segmentation and geometric fitting
- `find_optimal_transitions()`: Adaptive transition detection using Savitzky-Golay filtering
- `create_enhanced_profile()`: Smooth profile generation with Hermite splines

#### 2. Geometric Functions (Lines 187-196)
- `volume_cylinder()`: Cylinder volume calculation (V = πr²h)
- `volume_frustum()`: Truncated cone volume (V = πh/3(r₁² + r² + r₁r))
- `hermite_spline_transition()`: C¹ continuous transitions between segments

#### 3. 3D Model Generation (Lines 573-680)
- `export_stl_watertight()`: STL mesh generation with guaranteed closed bottom
- Uses trimesh library for manifold mesh operations
- Fan triangulation from center for bottom cap

#### 4. Reporting & Visualization (Lines 682-1183)
- `generate_enhanced_pdf_report()`: Multi-page PDF with ReportLab
- `generate_comprehensive_plots()`: 6-panel matplotlib visualization
- Executive summary, statistics, segment analysis, and configuration details

#### 5. Job Tracking (Lines 88-169)
- `AnalysisJob` class: Tracks execution metrics, errors, warnings, and outputs
- Provides structured reporting and debugging information

#### 6. User Interfaces (Lines 1185-1316)
- `launch_enhanced_gui()`: Tkinter-based GUI
- CLI mode via command-line arguments

## Key Technologies & Dependencies

### Required Dependencies
```python
# Scientific Computing
pandas >= 1.3.0          # Data manipulation
numpy >= 1.21.0          # Numerical operations
scipy >= 1.7.0           # Scientific algorithms (curve_fit, filters, interpolation)

# Visualization
matplotlib >= 3.4.0      # Plotting and visualization

# 3D Modeling
trimesh >= 3.9.0         # Watertight STL mesh generation

# PDF Generation
reportlab >= 3.6.0       # Professional PDF reports

# GUI (Usually pre-installed)
tkinter                  # Standard Python GUI library
```

### Optional Dependencies
All dependencies are technically optional - the application degrades gracefully:
- Without trimesh: No STL export
- Without reportlab: No PDF generation
- Without tkinter: CLI mode only

## Development Workflows

### Setup Development Environment
```bash
# Clone repository
git clone <repository-url>
cd container-geometry-analyzer

# Install dependencies
pip install pandas numpy scipy matplotlib reportlab trimesh

# Verify installation
python container_geometry_analyzer_gui_v3_11_8.py --help
```

### Running the Application

#### GUI Mode
```bash
python container_geometry_analyzer_gui_v3_11_8.py
```

#### CLI Mode
```bash
python container_geometry_analyzer_gui_v3_11_8.py path/to/data.csv
```

### Input Data Format
CSV files must contain:
- **Height column**: Any column name containing "height" (case-insensitive)
- **Volume column**: Any column name containing "volume" (case-insensitive)

Example:
```csv
Height (mm),Volume (ml)
0.0,0.0
0.634,0.02
1.268,0.04
...
```

### Output Files
Generated in the current working directory:
1. **STL Model**: `{basename}_model_{timestamp}.stl`
2. **PDF Report**: `ContainerReport_{timestamp}.pdf`

## Code Conventions & Patterns

### 1. Functional Programming Style
- Pure functions with clear inputs/outputs
- Minimal side effects
- Functions organized by single responsibility

### 2. Comprehensive Error Handling
```python
try:
    # Operation
except Exception as e:
    logger.error(f"Error message: {e}")
    if job:
        job.add_error(f"Error context: {str(e)}")
    raise RuntimeError(f"Context-specific error: {str(e)}")
```

### 3. Job Tracking Pattern
```python
job = AnalysisJob(input_file)
job.complete_step('Step Name', duration)
job.add_warning('Warning message')
job.add_error('Error message')
job.add_output_file(filepath, 'FILE_TYPE')
job.finalize()
summary = job.get_summary()
```

### 4. Logging Standards
```python
logger.info("✅ Success message with emoji prefix")
logger.warning("⚠️  Warning message with emoji prefix")
logger.error("❌ Error message with emoji prefix")
logger.debug("Debug information (verbose only)")
```

### 5. Parameter Configuration
All algorithm parameters centralized at top of file:
- `DEFAULT_PARAMS`: Segmentation and processing parameters
- `GEOMETRIC_CONSTRAINTS`: Physical/mathematical constraints

### 6. Naming Conventions
- **Functions**: `snake_case` with descriptive verb phrases
- **Classes**: `PascalCase` (e.g., `AnalysisJob`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_PARAMS`)
- **Variables**: `snake_case` with context (e.g., `df_areas`, `z_profile`, `r_profile`)

### 7. Type Hints
Partial type hinting used for key functions:
```python
def function_name(param: Type, optional: Optional[Type] = None) -> ReturnType:
```

### 8. Documentation Style
Docstrings follow concise descriptive format:
```python
def function_name(params):
    """Brief description of function purpose and behavior."""
```

## Algorithm Details

### Geometric Segmentation Algorithm
1. **Area Computation**: Calculate cross-sectional areas from dV/dh
2. **Transition Detection**: Use Savitzky-Golay filter to find inflection points
3. **Segment Validation**: Ensure minimum points per segment and variance thresholds
4. **Geometric Fitting**: Fit cylinders and frustums to each segment using scipy.optimize.curve_fit
5. **Model Selection**: Choose best fit based on error minimization

### Smooth Profile Generation
1. **Segment Profiles**: Generate point arrays for each geometric segment
2. **Hermite Transitions**: Create C¹ continuous transitions between segments
3. **Gaussian Smoothing**: Apply final smoothing (sigma=0.8) for profile refinement
4. **Safety Clamping**: Ensure radii stay within physical bounds

### STL Export Strategy
1. **Revolution Surface**: Generate vertices by rotating profile around z-axis
2. **Sidewall Mesh**: Create triangulated faces between angular slices
3. **Bottom Cap**: ALWAYS add closed bottom at z=0 using fan triangulation from center
4. **Mesh Validation**: Use trimesh.fix_normals() and fill_holes() for manifold mesh

## Testing Strategy

### Current State
⚠️ **No automated tests currently exist**

### Recommended Testing Approach

#### 1. Unit Tests (Recommended)
```python
# Test geometric functions
def test_volume_cylinder():
    assert volume_cylinder(h=10, r=5) == pytest.approx(np.pi * 25 * 10)

def test_volume_frustum():
    # Test cases for frustum calculations
    pass

# Test data validation
def test_load_data_csv_invalid_columns():
    with pytest.raises(ValueError):
        load_data_csv('invalid.csv')
```

#### 2. Integration Tests
- Test full pipeline with known sample data
- Verify output file generation
- Validate volume accuracy within tolerance

#### 3. Validation Tests
- Test with various container shapes (cylinders, cones, complex)
- Verify STL watertightness
- Check PDF generation completeness

### Testing Sample Data
Use provided samples:
- `sample_2ml_tube_geometry_corrected.csv`: Standard 2ml tube
- `simulated_container_eppi_50uL.csv`: Small volume container

## Common Development Tasks

### Adding a New Geometric Shape

1. **Add volume function**:
```python
def volume_shape_name(h, param1, param2, ...):
    """Calculate volume for new shape."""
    return calculated_volume
```

2. **Update segmentation**:
Modify `segment_and_fit_optimized()` to attempt new shape fit

3. **Update profile generation**:
Add case to `create_enhanced_profile()` for new shape

4. **Update reporting**:
Add shape name to `generate_enhanced_pdf_report()` segment table

### Modifying Segmentation Parameters

Edit `DEFAULT_PARAMS` dictionary:
```python
DEFAULT_PARAMS = {
    'min_points': 12,           # Minimum points per segment
    'sg_window': 9,             # Savitzky-Golay window size
    'percentile': 80,           # Transition detection threshold
    'variance_threshold': 0.15, # Segment variance validation
    # ... other parameters
}
```

### Customizing PDF Reports

1. **Add sections**: Insert new sections in `generate_enhanced_pdf_report()`
2. **Modify styles**: Edit `ParagraphStyle` objects for formatting
3. **Add visualizations**: Create new plots in `generate_comprehensive_plots()`

### Improving STL Quality

Adjust in `export_stl_watertight()`:
- `angular_res`: Number of faces around circumference (default: 48)
- Profile point density: Modify `num_points` in profile generation

## AI Assistant Guidelines

### When Analyzing This Codebase

1. **Understand the Scientific Context**
   - This is a geometric analysis tool, not a general-purpose application
   - Mathematical accuracy is critical
   - Physical constraints must be respected (positive volumes, radii, etc.)

2. **Preserve Algorithmic Integrity**
   - Don't modify core algorithms without thorough understanding
   - Segmentation logic is carefully tuned
   - Volume calculations must remain mathematically correct

3. **Maintain Report Quality**
   - PDF reports are professional deliverables
   - Don't remove statistics or visualizations without good reason
   - Keep consistent formatting and style

### When Making Changes

#### DO:
- ✅ Add comprehensive error handling
- ✅ Improve logging and debugging output
- ✅ Add input validation
- ✅ Optimize performance while maintaining accuracy
- ✅ Add type hints for better IDE support
- ✅ Create unit tests for new functionality
- ✅ Update documentation in README.md and CLAUDE.md
- ✅ Follow existing naming conventions

#### DON'T:
- ❌ Change mathematical formulas without verification
- ❌ Remove safety checks or constraints
- ❌ Break backward compatibility with CSV format
- ❌ Modify STL bottom cap logic (must always be closed)
- ❌ Remove verbose logging (critical for debugging)
- ❌ Skip job tracking for new operations

### Common Modification Requests

#### "Add support for new file format"
1. Create new loader function similar to `load_data_csv()`
2. Ensure output format matches DataFrame structure: `['Height_mm', 'Volume_mm3', 'Volume_ml']`
3. Update GUI file dialog to accept new extension
4. Add error handling for format-specific issues

#### "Improve segmentation accuracy"
1. Analyze failure cases with test data
2. Consider adjusting `DEFAULT_PARAMS` values
3. May need to modify `find_optimal_transitions()` algorithm
4. Always validate with multiple test cases
5. Document parameter changes in comments

#### "Add new visualization to PDF"
1. Create plotting function in matplotlib
2. Save to temporary file using `tempfile.NamedTemporaryFile()`
3. Import as `Image()` in PDF story
4. Clean up temp file after PDF generation
5. Add description and context in report text

#### "Export to different 3D format"
1. Use trimesh's export capabilities: `mesh.export(filename, file_type='format')`
2. Supported: OBJ, PLY, OFF, STL, GLTF, etc.
3. Ensure format supports manifold meshes
4. Update job tracking to record new output type

### Performance Considerations

1. **Large Datasets**: Application handles ~100-1000 data points efficiently
2. **Memory Usage**: Matplotlib plots can consume significant memory; ensure `plt.close('all')` after plotting
3. **STL Resolution**: Higher `angular_res` increases file size exponentially
4. **PDF Generation**: Temporary plot files must be cleaned up to avoid disk bloat

### Known Limitations

1. **Single Container Analysis**: Processes one container at a time (no batch mode)
2. **2D Axisymmetric Only**: Assumes circular cross-sections (no oval or irregular shapes)
3. **Manual Column Detection**: Relies on column names containing "height" and "volume"
4. **Fixed Units**: Assumes mm for height, ml for volume
5. **No Undo**: GUI doesn't support re-running with different parameters

### Version History Context

- **v3.11.8**: Current version with tempfile fixes and enhanced logging
- **v3.11.7**: Added comprehensive PDF reporting
- **v3.11.3**: Fixed temporary directory handling
- Earlier versions: Core segmentation and STL export functionality

## Git Development Workflow

### Branch Strategy
- Main branch: Stable releases
- Feature branches: `feature/description`
- Bug fixes: `bugfix/description`
- AI assistant branches: `claude/*` (auto-generated)

### Commit Guidelines
```bash
# Descriptive commit messages
git commit -m "Add: New geometric shape support for ellipsoids"
git commit -m "Fix: STL bottom cap triangulation orientation"
git commit -m "Update: Improve segmentation accuracy for small volumes"
git commit -m "Docs: Add testing guidelines to CLAUDE.md"
```

### Before Committing
1. Test with sample CSV files
2. Verify STL files are watertight
3. Check PDF generation completes
4. Review logs for warnings/errors
5. Update version number if needed

## Debugging Tips

### Enable Verbose Logging
Already enabled by default. Check console output for:
- ✅ Success indicators
- ⚠️ Warnings
- ❌ Errors

### Common Issues

**Issue**: "No height/volume column found"
- **Solution**: Ensure CSV has columns with "height" and "volume" in names

**Issue**: "STL not watertight"
- **Solution**: Check for NaN values in profile, ensure sufficient data points

**Issue**: "Segmentation produces too many/few segments"
- **Solution**: Adjust `percentile` and `variance_threshold` in DEFAULT_PARAMS

**Issue**: "PDF generation fails"
- **Solution**: Check matplotlib plot creation, verify tempfile cleanup

**Issue**: "Volume accuracy error too high"
- **Solution**: Review data quality, check for measurement errors in CSV

## External Resources

### Mathematical Background
- **Hermite Splines**: https://en.wikipedia.org/wiki/Cubic_Hermite_spline
- **Savitzky-Golay Filter**: https://en.wikipedia.org/wiki/Savitzky%E2%80%93Golay_filter
- **Frustum Volume**: https://mathworld.wolfram.com/ConicalFrustum.html

### Library Documentation
- **Trimesh**: https://trimsh.org/
- **ReportLab**: https://www.reportlab.com/docs/reportlab-userguide.pdf
- **SciPy Optimization**: https://docs.scipy.org/doc/scipy/reference/optimize.html

### Related Topics
- Geometric segmentation algorithms
- 3D mesh manifold properties
- Axisymmetric surface modeling
- Laboratory automation workflows

---

## Quick Reference Card

### File Structure
```
Single file: container_geometry_analyzer_gui_v3_11_8.py
├── Imports & Configuration (Lines 1-86)
├── Job Tracking (Lines 88-169)
├── Utilities (Lines 171-196)
├── Core Pipeline (Lines 198-547)
├── STL Export (Lines 573-680)
├── PDF Reporting (Lines 682-1046)
├── Visualization (Lines 1048-1183)
└── Entry Points (Lines 1185-1316)
```

### Key Functions to Know
| Function | Purpose | Critical? |
|----------|---------|-----------|
| `load_data_csv()` | Data import | ✅ Yes |
| `compute_areas()` | dV/dh calculation | ✅ Yes |
| `segment_and_fit_optimized()` | Core algorithm | ✅ Yes |
| `create_enhanced_profile()` | Smooth profile | ✅ Yes |
| `export_stl_watertight()` | 3D model | ⚠️ Important |
| `generate_enhanced_pdf_report()` | Reporting | ⚠️ Important |

### Parameter Tuning Quick Guide
```python
# More sensitive segmentation (more segments):
DEFAULT_PARAMS['percentile'] = 70  # Lower = more sensitive

# Require more points per segment:
DEFAULT_PARAMS['min_points'] = 15  # Higher = stricter

# Smoother transitions:
DEFAULT_PARAMS['hermite_tension'] = 0.5  # Lower = smoother

# Higher quality STL:
DEFAULT_PARAMS['angular_resolution'] = 60  # Higher = more faces
```

---

**For Questions or Issues**: Review this guide first, then check README.md for user-facing documentation.

**Last Updated**: 2025-11-19 by AI Assistant (Claude)
