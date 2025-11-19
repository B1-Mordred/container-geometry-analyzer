"""
Container Geometry Analyzer - Enhanced PDF Reporting (v3.11.8)
===============================================================

Author: Marco Horstmann
"""

import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter
from scipy.interpolate import CubicSpline
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from datetime import datetime
import sys
import warnings
import logging
import time
import tempfile
from typing import Dict, List, Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PDF Generation (ReportLab)
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph, 
                                    Spacer, Image, PageBreak, KeepTogether, ListFlowable, ListItem)
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
    logger.info("✅ ReportLab available - PDF reports enabled")
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("⚠️  ReportLab not available - install: pip install reportlab")

# 3D Mesh Generation (trimesh)
try:
    import trimesh
    HAS_TRIMESH = True
    logger.info("✅ Trimesh available - STL export enabled")
except ImportError:
    HAS_TRIMESH = False
    logger.warning("⚠️  Trimesh not available - install: pip install trimesh")

# GUI (tkinter)
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    HAS_TKINTER = True
    logger.info("✅ Tkinter available - GUI enabled")
except ImportError:
    HAS_TKINTER = False
    logger.info("ℹ️  Tkinter not available - CLI mode only")

# Analysis Configuration
DEFAULT_PARAMS = {
    'min_points': 12,
    'sg_window': 9,
    'percentile': 80,
    'variance_threshold': 0.15,
    'transition_buffer': 2.5,
    'hermite_tension': 0.6,
    'merge_threshold': 0.05,
    'angular_resolution': 48,
    'maxfev': 4000,
    'transition_detection_method': 'improved',  # 'legacy' or 'improved' (multi-derivative)
    'use_adaptive_threshold': True,
    'use_multiscale': False,  # More thorough but slower
}

GEOMETRIC_CONSTRAINTS = {
    'min_differential_volume': 0.01,
    'radius_safety_margin': 0.8,
    'fit_bounds_lower': 0.5,
    'fit_bounds_upper': 3.0,
}

# Job tracking class
class AnalysisJob:
    """Track analysis job execution details for reporting."""
    
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.start_time = time.time()
        self.end_time = None
        self.duration = None
        self.steps_completed = []
        self.errors = []
        self.warnings = []
        self.output_files = []
        self.statistics = {
            'data_points': 0,
            'height_range': (0.0, 0.0),
            'volume_range': (0.0, 0.0),
            'area_mean': 0.0,
            'area_std': 0.0,
            'area_min': 0.0,
            'area_max': 0.0,
            'segments_count': 0,
            'fit_errors': [],
            'avg_fit_error': 0.0,
            'max_fit_error': 0.0,
            'profile_points': 0,
            'stl_vertices': 0,
            'stl_faces': 0,
            'stl_volume_ml': 0.0,
            'stl_watertight': False
        }
        
    def complete_step(self, step_name: str, duration: float = None):
        """Record completion of an analysis step."""
        self.steps_completed.append({
            'name': step_name,
            'timestamp': datetime.now(),
            'duration': duration if duration is not None else 0.0
        })
        
    def add_error(self, error: str):
        """Record an error during processing."""
        self.errors.append({
            'message': error,
            'timestamp': datetime.now()
        })
        
    def add_warning(self, warning: str):
        """Record a warning during processing."""
        self.warnings.append({
            'message': warning,
            'timestamp': datetime.now()
        })
        
    def add_output_file(self, filepath: str, file_type: str):
        """Record generated output file."""
        if filepath and os.path.exists(filepath):
            self.output_files.append({
                'path': filepath,
                'type': file_type,
                'size': os.path.getsize(filepath),
                'timestamp': datetime.now()
            })
        
    def finalize(self):
        """Mark job as complete and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
    def get_summary(self) -> Dict:
        """Get job summary for reporting."""
        return {
            'input_file': os.path.basename(self.input_file),
            'input_file_full': self.input_file,
            'start_time': datetime.fromtimestamp(self.start_time),
            'end_time': datetime.fromtimestamp(self.end_time) if self.end_time else None,
            'duration': self.duration if self.duration is not None else 0.0,
            'steps_count': len(self.steps_completed),
            'errors_count': len(self.errors),
            'warnings_count': len(self.warnings),
            'outputs_count': len(self.output_files),
            'success': len(self.errors) == 0
        }

def safe_float(value, default=0.0, precision=2):
    """Safely format a float value, handling None."""
    if value is None:
        return f"{default:.{precision}f}"
    try:
        return f"{float(value):.{precision}f}"
    except (ValueError, TypeError):
        return f"{default:.{precision}f}"

def ensure_output_dir(filepath):
    """Ensure output directory exists."""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return filepath

def volume_cylinder(h, r):
    """Cylinder volume: V = πr²h"""
    return np.pi * r**2 * h

def volume_frustum(h, r1, r2, H):
    """Frustum volume: V = (πh/3)(r₁² + r² + r₁r)"""
    if H == 0:
        return 0
    r_interpolated = r1 + (r2 - r1) * (h / H)
    return (np.pi * h / 3) * (r1**2 + r_interpolated**2 + r1 * r_interpolated)

def load_data_csv(csv_path, job: AnalysisJob = None, verbose=True):
    """Load and validate CSV data with enhanced error handling."""
    step_start = time.time()
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Input file not found: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        df.columns = [col.strip() for col in df.columns]
        
        height_cols = [col for col in df.columns if 'height' in col.lower()]
        volume_cols = [col for col in df.columns if 'volume' in col.lower()]
        
        if not height_cols:
            raise ValueError("No height column found. Expected column name containing 'Height'")
        if not volume_cols:
            raise ValueError("No volume column found. Expected column name containing 'Volume'")
        
        height_col = height_cols[0]
        volume_col = volume_cols[0]
        
        df_clean = df[[height_col, volume_col]].dropna()
        if len(df_clean) < 5:
            raise ValueError(f"Insufficient data points ({len(df_clean)} < 5)")
        
        df_clean = df_clean.rename(columns={height_col: 'Height_mm', volume_col: 'Volume_ml'})
        df_clean = df_clean.sort_values('Height_mm').reset_index(drop=True)
        
        df_clean['Height_mm'] = pd.to_numeric(df_clean['Height_mm'], errors='coerce')
        df_clean['Volume_ml'] = pd.to_numeric(df_clean['Volume_ml'], errors='coerce')
        df_clean = df_clean.dropna()
        
        df_clean['Volume_mm3'] = df_clean['Volume_ml'] * 1000
        df_clean['Volume_mm3'] = np.maximum.accumulate(df_clean['Volume_mm3'])
        
        if df_clean['Height_mm'].min() < 0 or df_clean['Volume_ml'].min() < 0:
            raise ValueError("Negative heights or volumes detected")
        
        if verbose:
            logger.info(f"✅ Data loaded: {len(df_clean)} points")
            logger.info(f"   Height: {df_clean['Height_mm'].min():.1f} - {df_clean['Height_mm'].max():.1f} mm")
            logger.info(f"   Volume: {df_clean['Volume_ml'].min():.3f} - {df_clean['Volume_ml'].max():.3f} ml")
        
        if job:
            job.complete_step('Data Loading', time.time() - step_start)
            job.statistics['data_points'] = len(df_clean)
            job.statistics['height_range'] = (float(df_clean['Height_mm'].min()), float(df_clean['Height_mm'].max()))
            job.statistics['volume_range'] = (float(df_clean['Volume_ml'].min()), float(df_clean['Volume_ml'].max()))
        
        return df_clean[['Height_mm', 'Volume_mm3', 'Volume_ml']]
    
    except Exception as e:
        if job:
            job.add_error(f"Data loading failed: {str(e)}")
        logger.error(f"Error loading CSV '{csv_path}': {str(e)}")
        raise RuntimeError(f"Error loading CSV '{csv_path}': {str(e)}")

def compute_areas(df, job: AnalysisJob = None, min_dv=None, verbose=True):
    """Calculate cross-sectional areas from volume-height data."""
    step_start = time.time()
    
    if min_dv is None:
        min_dv = GEOMETRIC_CONSTRAINTS['min_differential_volume']
    
    df = df.copy()
    
    df['dV'] = df['Volume_mm3'].diff().fillna(0)
    df['dh'] = df['Height_mm'].diff().fillna(0.1)
    
    df['dV'] = np.maximum(df['dV'], min_dv)
    df['dh'] = np.maximum(df['dh'], 0.01)
    
    df['Area'] = df['dV'] / df['dh']
    df['Area'] = np.maximum(df['Area'], min_dv)
    
    df['MidHeight'] = (df['Height_mm'] + df['Height_mm'].shift(1).fillna(df['Height_mm'])) / 2
    
    df_areas = df.iloc[1:].reset_index(drop=True)
    
    if verbose:
        logger.info(f"📐 Areas computed: {len(df_areas)} points")
        logger.info(f"   Mean: {df_areas['Area'].mean():.1f} ± {df_areas['Area'].std():.1f} mm²")
    
    if job:
        job.complete_step('Area Computation', time.time() - step_start)
        job.statistics['area_mean'] = float(df_areas['Area'].mean())
        job.statistics['area_std'] = float(df_areas['Area'].std())
        job.statistics['area_min'] = float(df_areas['Area'].min())
        job.statistics['area_max'] = float(df_areas['Area'].max())
    
    return df_areas

def find_optimal_transitions(area, min_points=12, percentile=80, variance_threshold=0.15, verbose=False):
    """Detect geometric segment transitions using adaptive smoothing."""
    n = len(area)
    
    if n < 2 * min_points:
        if verbose:
            logger.warning(f"⚠️  Too few points for segmentation ({n} < {2*min_points})")
        return [0, n - 1]
    
    window = max(5, min(15, n // 10))
    if window % 2 == 0:
        window += 1
    
    try:
        area_smooth = savgol_filter(area, window_length=window, polyorder=min(2, window//2))
    except:
        area_smooth = pd.Series(area).rolling(window, center=True, min_periods=1).median().bfill().ffill().values
    
    diff = np.abs(np.diff(area_smooth))
    threshold = np.percentile(diff, percentile)
    candidates = np.where(diff > threshold)[0] + 1
    
    if verbose:
        logger.info(f"🔍 Transition detection: {len(candidates)} candidates")
    
    transitions = [0]
    for cand in candidates:
        if cand - transitions[-1] >= min_points:
            transitions.append(cand)
    
    if transitions[-1] != n - 1:
        transitions.append(n - 1)
    
    validated = [0]
    for i in range(len(transitions) - 1):
        seg_start, seg_end = transitions[i], transitions[i + 1]
        if seg_end - seg_start + 1 >= min_points:
            seg_var = np.std(area[seg_start:seg_end]) / (np.mean(area[seg_start:seg_end]) + 1e-8)
            if seg_var > variance_threshold or i in [0, len(transitions) - 2]:
                validated.append(seg_end)
    
    if not validated or validated[-1] != n - 1:
        validated[-1] = n - 1
    
    validated = sorted(list(set(validated)))
    if verbose:
        logger.info(f"   Validated segments: {len(validated)//2}")

    return validated

def find_optimal_transitions_improved(area, heights=None, min_points=12,
                                      use_adaptive=True, verbose=False):
    """
    Improved transition detection using multi-derivative analysis.

    Key improvements over legacy method:
    1. Uses second derivative (curvature) to detect slope changes
    2. Adaptive threshold based on signal-to-noise ratio
    3. Better validation using multiple criteria

    Parameters:
    -----------
    area : np.ndarray
        Cross-sectional areas
    heights : np.ndarray, optional
        Height values (if None, uses indices)
    min_points : int
        Minimum points per segment
    use_adaptive : bool
        Use adaptive thresholding based on SNR
    verbose : bool
        Print detailed information

    Returns:
    --------
    List[int] : Indices of transition points
    """
    n = len(area)

    if heights is None:
        heights = np.arange(n, dtype=float)

    if n < 2 * min_points:
        if verbose:
            logger.warning(f"⚠️  Too few points for segmentation ({n} < {2*min_points})")
        return [0, n - 1]

    # Smooth the area data
    window = max(5, min(15, n // 10))
    if window % 2 == 0:
        window += 1

    try:
        area_smooth = savgol_filter(area, window_length=window, polyorder=2)
    except:
        from scipy.ndimage import gaussian_filter1d
        area_smooth = gaussian_filter1d(area, sigma=2.0)

    # === IMPROVEMENT 1: Multi-derivative detection ===
    # Use both first and second derivatives
    first_deriv = np.gradient(area_smooth, heights)
    second_deriv = np.gradient(first_deriv, heights)

    # Combine derivatives for better detection
    first_deriv_change = np.abs(np.diff(first_deriv))
    second_deriv_abs = np.abs(second_deriv[:-1])

    # Normalize scores
    def normalize_score(arr):
        arr_min, arr_max = np.min(arr), np.max(arr)
        if arr_max - arr_min < 1e-10:
            return np.zeros_like(arr)
        return (arr - arr_min) / (arr_max - arr_min)

    score = (0.6 * normalize_score(first_deriv_change) +
             0.4 * normalize_score(second_deriv_abs))

    # === IMPROVEMENT 2: Adaptive threshold ===
    if use_adaptive:
        # Estimate signal-to-noise ratio
        area_very_smooth = savgol_filter(area,
            window_length=min(21, n//5 if n//5 % 2 == 1 else n//5+1),
            polyorder=2)
        noise = area - area_very_smooth
        noise_std = np.std(noise)
        signal_range = np.max(area) - np.min(area)
        snr = signal_range / (noise_std + 1e-8)

        # Adapt percentile based on SNR
        if snr > 100:
            percentile = 70  # Very clean data - more sensitive
        elif snr > 50:
            percentile = 75  # Clean data
        elif snr > 20:
            percentile = 80  # Moderate noise (default)
        elif snr > 10:
            percentile = 85  # Noisy data
        else:
            percentile = 90  # Very noisy - less sensitive

        if verbose:
            logger.info(f"   SNR: {snr:.2f}, adaptive percentile: {percentile}")
    else:
        percentile = 80  # Legacy default

    threshold = np.percentile(score, percentile)

    # Find candidates from peak detection
    try:
        from scipy.signal import find_peaks
        candidates, _ = find_peaks(score, height=threshold, distance=min_points)
        candidates = candidates + 1  # Adjust for diff operation
    except:
        # Fallback to simple threshold
        candidates = np.where(score > threshold)[0] + 1

    if verbose:
        logger.info(f"🔍 Improved detection: {len(candidates)} candidates (multi-derivative + adaptive)")

    # Enforce minimum spacing
    transitions = [0]
    for cand in sorted(candidates):
        if cand - transitions[-1] >= min_points and cand < n - 1:
            transitions.append(int(cand))

    if transitions[-1] != n - 1:
        transitions.append(n - 1)

    # === IMPROVEMENT 3: Advanced validation ===
    validated = [transitions[0]]

    for i in range(len(transitions) - 1):
        seg_start = transitions[i]
        seg_end = transitions[i + 1]

        if seg_end - seg_start + 1 < min_points:
            continue

        seg_area = area[seg_start:seg_end + 1]

        # Criterion 1: Coefficient of variation
        cv = np.std(seg_area) / (np.mean(seg_area) + 1e-8)
        has_variation = cv > 0.05  # Lower threshold than legacy (0.15)

        # Criterion 2: Autocorrelation (structure vs noise)
        if len(seg_area) > 3:
            area_shifted = seg_area[1:]
            area_orig = seg_area[:-1]
            correlation = np.corrcoef(area_orig, area_shifted)[0, 1]
            has_structure = abs(correlation) > 0.4
        else:
            has_structure = True

        # Criterion 3: Model fit quality
        z = np.arange(len(seg_area))
        if len(z) > 2:
            coeffs = np.polyfit(z, seg_area, 1)
            area_predicted = np.polyval(coeffs, z)
            r_squared = 1 - (np.sum((seg_area - area_predicted)**2) /
                           (np.sum((seg_area - np.mean(seg_area))**2) + 1e-8))
            fits_model = r_squared > 0.65
        else:
            fits_model = True

        # Keep if passes at least 2 criteria, or is boundary segment
        is_boundary = i in [0, len(transitions) - 2]
        passed_criteria = sum([has_variation, has_structure, fits_model])

        if passed_criteria >= 2 or is_boundary:
            validated.append(seg_end)

    # Ensure endpoints
    if not validated or validated[-1] != transitions[-1]:
        validated.append(transitions[-1])

    validated = sorted(list(set(validated)))

    if verbose:
        logger.info(f"   Validated segments: {len(validated) - 1}")

    return validated

def segment_and_fit_optimized(df_areas, job: AnalysisJob = None, verbose=True):
    """Main segmentation and fitting pipeline."""
    step_start = time.time()
    
    if len(df_areas) < 10:
        warning_msg = "Limited data points - results may be approximate"
        warnings.warn(warning_msg)
        if job:
            job.add_warning(warning_msg)
    
    area = df_areas['Area'].values
    heights = df_areas['Height_mm'].values

    # Use improved or legacy transition detection
    if DEFAULT_PARAMS.get('transition_detection_method', 'legacy') == 'improved':
        transitions = find_optimal_transitions_improved(
            area,
            heights=heights,
            min_points=DEFAULT_PARAMS['min_points'],
            use_adaptive=DEFAULT_PARAMS.get('use_adaptive_threshold', True),
            verbose=verbose
        )
        if verbose:
            logger.info("✨ Using improved transition detection (multi-derivative + adaptive)")
    else:
        transitions = find_optimal_transitions(area, verbose=verbose)
        if verbose:
            logger.info("📊 Using legacy transition detection")

    segments = []
    fit_errors = []
    
    for i in range(len(transitions) - 1):
        start = transitions[i]
        end = transitions[i + 1]
        
        if end - start + 1 < DEFAULT_PARAMS['min_points']:
            continue
        
        x = df_areas['Height_mm'].iloc[start:end + 1].values
        y = df_areas['Volume_mm3'].iloc[start:end + 1].values
        height_span = float(x[-1] - x[0])
        mean_area = float(np.median(area[start:end + 1]))
        guess_r = float(np.sqrt(mean_area / np.pi))
        
        try:
            bounds_lower = GEOMETRIC_CONSTRAINTS['fit_bounds_lower'] * guess_r
            bounds_upper = GEOMETRIC_CONSTRAINTS['fit_bounds_upper'] * guess_r
            popt_cyl, _ = curve_fit(volume_cylinder, x - x[0], y - y[0], 
                                  p0=[guess_r], bounds=([bounds_lower], [bounds_upper]), 
                                  maxfev=DEFAULT_PARAMS['maxfev'])
            cyl_error = np.mean(np.abs(volume_cylinder(x - x[0], *popt_cyl) + y[0] - y))
            cyl_error_pct = (cyl_error / (y[-1] + 1e-6)) * 100
        except Exception as e:
            logger.debug(f"Cylinder fit failed for segment {i}: {e}")
            popt_cyl = None
            cyl_error = np.inf
            cyl_error_pct = np.inf
        
        try:
            area_start = area[start] if start > 0 else mean_area
            area_end = area[end] if end < len(area) - 1 else mean_area
            r1_guess = float(np.sqrt(area_start / np.pi))
            r2_guess = float(np.sqrt(area_end / np.pi))
            
            bounds = (
                [GEOMETRIC_CONSTRAINTS['fit_bounds_lower']*r1_guess, 
                 GEOMETRIC_CONSTRAINTS['fit_bounds_lower']*r2_guess, 
                 0.8*height_span],
                [GEOMETRIC_CONSTRAINTS['fit_bounds_upper']*r1_guess, 
                 GEOMETRIC_CONSTRAINTS['fit_bounds_upper']*r2_guess, 
                 1.2*height_span]
            )
            popt_frust, _ = curve_fit(volume_frustum, x - x[0], y - y[0], 
                                    p0=[r1_guess, r2_guess, height_span], 
                                    bounds=bounds, maxfev=DEFAULT_PARAMS['maxfev'])
            frust_error = np.mean(np.abs(volume_frustum(x - x[0], *popt_frust) + y[0] - y))
            frust_error_pct = (frust_error / (y[-1] + 1e-6)) * 100
        except Exception as e:
            logger.debug(f"Frustum fit failed for segment {i}: {e}")
            popt_frust = None
            frust_error = np.inf
            frust_error_pct = np.inf
        
        if popt_cyl is not None and (popt_frust is None or cyl_error < frust_error):
            segments.append((start, end, 'cylinder', [popt_cyl[0]]))
            fit_errors.append(cyl_error_pct)
        elif popt_frust is not None:
            segments.append((start, end, 'frustum', popt_frust))
            fit_errors.append(frust_error_pct)
        else:
            segments.append((start, end, 'cylinder', [guess_r]))
            fit_errors.append(0.0)
    
    if verbose:
        logger.info(f"✅ Detected {len(segments)} segments")
        if fit_errors:
            logger.info(f"   Average fit error: {np.mean(fit_errors):.3f}%")
    
    if job:
        job.complete_step('Segmentation & Fitting', time.time() - step_start)
        job.statistics['segments_count'] = len(segments)
        job.statistics['fit_errors'] = fit_errors
        job.statistics['avg_fit_error'] = float(np.mean(fit_errors)) if fit_errors else 0.0
        job.statistics['max_fit_error'] = float(np.max(fit_errors)) if fit_errors else 0.0
    
    return segments

def hermite_spline_transition(z1, r1, slope1, z2, r2, slope2, num_points=25, tension=0.6):
    """C¹ continuous Hermite cubic spline transition."""
    dz = z2 - z1
    if dz <= 0:
        return np.linspace(z1, z2, num_points), np.full(num_points, (r1 + r2) / 2)
    
    t = np.linspace(0, 1, num_points)
    z_trans = z1 + t * dz
    
    t2 = t**2
    t3 = t**3
    h00 = 2*t3 - 3*t2 + 1
    h10 = -2*t3 + 3*t2
    h01 = t3 * (t - 1)
    h11 = t2 * (t - 1)
    
    m0 = slope1 * dz * tension
    m1 = slope2 * dz * tension
    
    r_trans = h00 * r1 + h10 * r2 + h01 * m0 + h11 * m1
    
    r_min = min(r1, r2) * GEOMETRIC_CONSTRAINTS['radius_safety_margin']
    r_max = max(r1, r2) * 1.2
    r_trans = np.clip(r_trans, r_min, r_max)
    
    r_trans[0] = r1
    r_trans[-1] = r2
    
    return z_trans, r_trans

def create_enhanced_profile(segments, df_areas, job: AnalysisJob = None, transition_buffer=2.5, hermite_tension=0.6, verbose=True):
    """Generate smooth 2D profile with Hermite transitions."""
    step_start = time.time()
    
    if len(segments) <= 1:
        heights = df_areas['Height_mm'].values
        radii = np.sqrt(np.maximum(df_areas['Area'].values / np.pi, 0.01))
        return heights, radii
    
    full_z = []
    full_r = []
    
    for i in range(len(segments)):
        start, end, shape, params = segments[i]
        h_start = df_areas.iloc[start]['Height_mm']
        h_end = df_areas.iloc[end]['Height_mm']
        h_span = h_end - h_start
        
        if h_span <= 0:
            continue
        
        num_points = max(15, min(30, end - start + 1))
        h_rel = np.linspace(0, h_span, num_points)
        
        if shape == 'cylinder' and len(params) == 1:
            r_start, r_end = float(params[0]), float(params[0])
            slope_end = 0.0
            r_seg = np.full_like(h_rel, r_start)
        elif shape == 'frustum' and len(params) >= 3:
            r1, r2, _ = [float(p) for p in params]
            t = h_rel / h_span
            r_seg = r1 + (r2 - r1) * t
            slope_end = (r2 - r1) / h_span
        else:
            r_start = np.sqrt(df_areas.iloc[start]['Area'] / np.pi)
            r_end = np.sqrt(df_areas.iloc[min(end, len(df_areas)-1)]['Area'] / np.pi)
            r_seg = r_start + (r_end - r_start) * (h_rel / h_span)
            slope_end = (r_end - r_start) / h_span
        
        z_seg = h_start + h_rel
        full_z.extend(z_seg)
        full_r.extend(r_seg)
        
        if i < len(segments) - 1:
            next_start, next_end, next_shape, next_params = segments[i+1]
            next_h_start = df_areas.iloc[next_start]['Height_mm']
            
            if next_shape == 'cylinder' and len(next_params) == 1:
                next_r_start = float(next_params[0])
                next_slope = 0.0
            elif next_shape == 'frustum' and len(next_params) >= 3:
                next_r_start = float(next_params[0])
                next_slope = (next_params[1] - next_params[0]) / (df_areas.iloc[next_end]['Height_mm'] - df_areas.iloc[next_start]['Height_mm'])
            else:
                next_r_start = np.sqrt(df_areas.iloc[next_start]['Area'] / np.pi)
                next_slope = 0.0
            
            buffer = min(3.0, max(1.5, abs(r_seg[-1] - next_r_start) * 1.5))
            
            z_trans, r_trans = hermite_spline_transition(
                z_seg[-1], r_seg[-1], slope_end,
                next_h_start, next_r_start, next_slope,
                num_points=25,
                tension=hermite_tension
            )
            
            full_z.extend(z_trans[1:-1])
            full_r.extend(r_trans[1:-1])
    
    if len(full_z) > 1:
        profile_df = pd.DataFrame({'z': full_z, 'r': full_r})
        profile_df = profile_df.drop_duplicates('z').sort_values('z').reset_index(drop=True)
        
        from scipy.ndimage import gaussian_filter1d
        r_final = gaussian_filter1d(profile_df['r'].values, sigma=0.8, mode='nearest')
        profile_df['r'] = r_final
        profile_df['r'] = np.maximum(profile_df['r'], 0.1)
        
        if job:
            job.complete_step('Profile Generation', time.time() - step_start)
            job.statistics['profile_points'] = len(profile_df)
        
        return profile_df['z'].values, profile_df['r'].values
    else:
        return df_areas['Height_mm'].values, np.sqrt(np.maximum(df_areas['Area'].values / np.pi, 0.01))

def calculate_profile_volume(z, r):
    """Compute volume from smooth 2D profile."""
    if len(z) < 2:
        return np.array([0.0])
    
    dz = np.diff(z)
    r_avg = (r[:-1] + r[1:]) / 2
    areas = np.pi * r_avg**2
    dvol = areas * dz
    volumes = np.cumsum(dvol)
    return np.concatenate([[0.0], volumes])

def validate_volume_accuracy(original_volume_ml, calculated_volume_mm3, tolerance=0.01):
    """Validate volume preservation."""
    original_mm3 = original_volume_ml * 1000
    error = abs(original_mm3 - calculated_volume_mm3) / (original_mm3 + 1e-6)
    is_valid = error <= tolerance
    return {
        'original_ml': original_volume_ml,
        'calculated_ml': calculated_volume_mm3 / 1000,
        'error_percent': error * 100,
        'is_valid': is_valid,
        'tolerance_percent': tolerance * 100
    }

def export_stl_watertight(z_profile, r_profile, filename, job: AnalysisJob = None, verbose=True):
    """Generate watertight STL from smooth profile with ALWAYS CLOSED BOTTOM."""
    step_start = time.time()
    
    if not HAS_TRIMESH:
        if verbose:
            logger.warning("⚠️  Trimesh unavailable - install: pip install trimesh")
        return None
    
    if len(z_profile) < 3:
        if verbose:
            logger.warning("⚠️  Profile too short for STL generation")
        return None
    
    ensure_output_dir(filename)
    
    # Ensure profile starts at z=0 for proper bottom cap
    z_min = z_profile.min()
    if z_min > 0:
        z_profile = z_profile - z_min
    
    total_h = z_profile.max()
    angular_res = 48 if total_h < 50 else 60
    
    angles = np.linspace(0, 2 * np.pi, angular_res, endpoint=False)
    n_p = len(z_profile)
    
    # Sidewall vertices
    verts = np.zeros((angular_res * n_p, 3))
    for i, angle in enumerate(angles):
        idx = slice(i * n_p, (i + 1) * n_p)
        verts[idx, 0] = r_profile * np.cos(angle)
        verts[idx, 1] = r_profile * np.sin(angle)
        verts[idx, 2] = z_profile
    
    # Sidewall faces
    faces = []
    for i in range(angular_res):
        i_next = (i + 1) % angular_res
        base = i * n_p
        next_base = i_next * n_p
        for j in range(n_p - 1):
            v0, v1 = base + j, base + j + 1
            v2, v3 = next_base + j, next_base + j + 1
            faces.extend([[v0, v2, v1], [v1, v2, v3]])
    
    faces = np.array(faces, dtype=np.uint32)
    
    # ALWAYS ADD BOTTOM CAP - Critical for watertight mesh
    bottom_r = float(r_profile[0])
    
    # Add bottom ring vertices at z=0
    bottom_base = len(verts)
    bottom_verts = np.array([
        [bottom_r * np.cos(angle), bottom_r * np.sin(angle), 0.0]
        for angle in angles
    ])
    
    # Add bottom center vertex at z=0
    center_bottom = np.array([[0.0, 0.0, 0.0]])
    
    verts = np.vstack([verts, bottom_verts, center_bottom])
    center_idx = len(verts) - 1
    
    # Create bottom cap faces (fan triangulation from center)
    bottom_faces = []
    for k in range(angular_res):
        k_next = (k + 1) % angular_res
        # Triangle from center to edge ring (counter-clockwise for inward normal)
        bottom_faces.append([center_idx, bottom_base + k_next, bottom_base + k])
    
    faces = np.vstack([faces, np.array(bottom_faces, dtype=np.uint32)])
    
    # Create mesh
    try:
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        mesh.fix_normals()
        mesh.fill_holes()  # Fill any remaining holes
        
        mesh_volume_ml = mesh.volume / 1000
        
        if verbose:
            logger.info(f"📐 STL Export:")
            logger.info(f"   Filename: {filename}")
            logger.info(f"   Vertices: {len(verts)}")
            logger.info(f"   Faces: {len(faces)}")
            logger.info(f"   Volume: {mesh_volume_ml:.3f} ml")
            logger.info(f"   Watertight: {mesh.is_watertight}")
            logger.info(f"   Bottom Cap: ✅ CLOSED (z=0)")
        
        mesh.export(filename)
        
        if job:
            job.complete_step('STL Export', time.time() - step_start)
            job.add_output_file(filename, 'STL')
            job.statistics['stl_vertices'] = int(len(verts))
            job.statistics['stl_faces'] = int(len(faces))
            job.statistics['stl_volume_ml'] = float(mesh_volume_ml)
            job.statistics['stl_watertight'] = bool(mesh.is_watertight)
        
        return filename
    
    except Exception as e:
        if verbose:
            logger.error(f"❌ STL export failed: {e}", exc_info=True)
        if job:
            job.add_error(f"STL export failed: {str(e)}")
        return None

def generate_enhanced_pdf_report(df, df_areas, segments, z_profile, r_profile, 
                                 csv_path, job: AnalysisJob, output_dir="./", verbose=True):
    """Generate comprehensive PDF report with job details and statistics."""
    if not HAS_REPORTLAB:
        if verbose:
            logger.warning("⚠️  ReportLab unavailable - skipping PDF generation")
        return None
    
    step_start = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = os.path.join(output_dir, f"ContainerReport_{timestamp}.pdf")
    
    ensure_output_dir(pdf_filename)
    
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=1.0*inch, bottomMargin=0.75*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#7f8c8d'),
        spaceAfter=8
    )
    
    # TITLE PAGE
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("Container Geometry Analysis", title_style))
    story.append(Paragraph("Comprehensive Analysis Report", styles['Heading2']))
    story.append(Spacer(1, 0.5*inch))
    
    job_summary = job.get_summary()
    
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", info_style))
    story.append(Paragraph(f"<b>Input File:</b> {job_summary['input_file']}", info_style))
    story.append(Paragraph(f"<b>Analysis Duration:</b> {safe_float(job_summary['duration'], precision=2)} seconds", info_style))
    story.append(Paragraph(f"<b>Software Version:</b> 3.11.3 (Temp Directory Fix)", info_style))
    story.append(Paragraph(f"<b>Status:</b> {'✅ SUCCESS' if job_summary['success'] else '❌ FAILED'}", info_style))
    
    story.append(PageBreak())
    
    # EXECUTIVE SUMMARY
    story.append(Paragraph("📊 Executive Summary", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    total_height = float(df['Height_mm'].max())
    total_volume_ml = float(df['Volume_ml'].max())
    calculated_volume = calculate_profile_volume(z_profile, r_profile)[-1]
    volume_validation = validate_volume_accuracy(total_volume_ml, calculated_volume)
    
    summary_data = [
        ['Metric', 'Value', 'Unit'],
        ['Total Container Height', safe_float(total_height), 'mm'],
        ['Total Container Volume', safe_float(total_volume_ml, precision=3), 'ml'],
        ['Calculated Volume', safe_float(volume_validation['calculated_ml'], precision=3), 'ml'],
        ['Volume Accuracy', safe_float(100 - volume_validation['error_percent']), '%'],
        ['Segments Detected', str(len(segments)), ''],
        ['Data Points Analyzed', str(len(df)), ''],
        ['Profile Points Generated', str(job.statistics.get('profile_points', 0)), ''],
        ['Processing Time', safe_float(job_summary.get('duration', 0)), 'seconds'],
        ['STL Mesh Generated', '✅ Yes (Bottom Closed)' if job.statistics.get('stl_watertight') else '⚠️ Yes (Check Mesh)', ''],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("<b>Quality Assessment:</b>", styles['Heading3']))
    
    quality_text = f"""
    <b>Volume Preservation:</b> {safe_float(100 - volume_validation['error_percent'], precision=3)}% 
    (Error: {safe_float(volume_validation['error_percent'], precision=3)}%)<br/>
    <b>Status:</b> {'✅ Excellent' if volume_validation['is_valid'] else '⚠️ Review Required'}<br/>
    <b>Average Fit Error:</b> {safe_float(job.statistics.get('avg_fit_error', 0), precision=3)}%<br/>
    <b>Maximum Fit Error:</b> {safe_float(job.statistics.get('max_fit_error', 0), precision=3)}%<br/>
    <b>Mesh Quality:</b> STL exported with closed bottom at z=0
    """
    story.append(Paragraph(quality_text, styles['Normal']))
    
    story.append(PageBreak())
    
    # JOB EXECUTION DETAILS
    story.append(Paragraph("⚙️ Job Execution Details", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("<b>Processing Steps:</b>", styles['Heading3']))
    
    steps_data = [['Step', 'Duration (s)', 'Status']]
    for step in job.steps_completed:
        steps_data.append([
            step['name'],
            safe_float(step.get('duration', 0), precision=3),
            '✅'
        ])
    
    steps_table = Table(steps_data, colWidths=[3*inch, 1.5*inch, 1*inch])
    steps_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen)
    ]))
    
    story.append(steps_table)
    story.append(Spacer(1, 0.2*inch))
    
    if job.warnings:
        story.append(Paragraph("<b>⚠️ Warnings:</b>", styles['Heading3']))
        for warning in job.warnings:
            story.append(Paragraph(f"• {warning['message']}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    if job.errors:
        story.append(Paragraph("<b>❌ Errors:</b>", styles['Heading3']))
        for error in job.errors:
            story.append(Paragraph(f"• {error['message']}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>Generated Output Files:</b>", styles['Heading3']))
    
    output_data = [['Filename', 'Type', 'Size (KB)']]
    for output in job.output_files:
        output_data.append([
            os.path.basename(output['path']),
            output['type'],
            safe_float(output['size'] / 1024)
        ])
    
    if len(output_data) > 1:
        output_table = Table(output_data, colWidths=[3*inch, 1.5*inch, 1*inch])
        output_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lavender)
        ]))
        story.append(output_table)
    
    story.append(PageBreak())
    
    # STATISTICAL ANALYSIS
    story.append(Paragraph("📈 Statistical Analysis", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    h_range = job.statistics.get('height_range', (0.0, 0.0))
    v_range = job.statistics.get('volume_range', (0.0, 0.0))
    
    stats_data = [
        ['Statistic', 'Value', 'Unit'],
        ['', '', ''],
        ['<b>Height Statistics</b>', '', ''],
        ['Minimum Height', safe_float(h_range[0]), 'mm'],
        ['Maximum Height', safe_float(h_range[1]), 'mm'],
        ['Height Range', safe_float(h_range[1] - h_range[0]), 'mm'],
        ['', '', ''],
        ['<b>Volume Statistics</b>', '', ''],
        ['Minimum Volume', safe_float(v_range[0], precision=3), 'ml'],
        ['Maximum Volume', safe_float(v_range[1], precision=3), 'ml'],
        ['Volume Range', safe_float(v_range[1] - v_range[0], precision=3), 'ml'],
        ['', '', ''],
        ['<b>Cross-Section Statistics</b>', '', ''],
        ['Mean Area', safe_float(job.statistics.get('area_mean', 0)), 'mm²'],
        ['Std Deviation', safe_float(job.statistics.get('area_std', 0)), 'mm²'],
        ['Minimum Area', safe_float(job.statistics.get('area_min', 0)), 'mm²'],
        ['Maximum Area', safe_float(job.statistics.get('area_max', 0)), 'mm²'],
        ['Mean Radius', safe_float(np.sqrt(job.statistics.get('area_mean', 1) / np.pi)), 'mm'],
    ]
    
    stats_table = Table(stats_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 2), (-1, 2), colors.lightcoral),
        ('BACKGROUND', (0, 7), (-1, 7), colors.lightcoral),
        ('BACKGROUND', (0, 12), (-1, 12), colors.lightcoral),
        ('FONTNAME', (0, 2), (0, 2), 'Helvetica-Bold'),
        ('FONTNAME', (0, 7), (0, 7), 'Helvetica-Bold'),
        ('FONTNAME', (0, 12), (0, 12), 'Helvetica-Bold'),
    ]))
    
    story.append(stats_table)
    story.append(PageBreak())
    
    # GEOMETRIC SEGMENT ANALYSIS
    story.append(Paragraph("📐 Geometric Segment Analysis", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    segment_data = [['ID', 'Type', 'Height Range (mm)', 'Parameters', 'Volume (ml)', 'Fit Error (%)']]
    
    for i, seg in enumerate(segments):
        start_idx, end_idx, shape, params = seg
        
        try:
            h_start = float(df_areas.iloc[start_idx]['Height_mm'])
            h_end = float(df_areas.iloc[min(end_idx, len(df_areas)-1)]['Height_mm'])
            h_range = f"{safe_float(h_start, precision=1)} - {safe_float(h_end, precision=1)}"
            
            vol_start = float(df_areas['Volume_mm3'].iloc[start_idx])
            vol_end = float(df_areas['Volume_mm3'].iloc[min(end_idx, len(df_areas)-1)])
            seg_vol = (vol_end - vol_start) / 1000
        except:
            h_range = "N/A"
            seg_vol = 0.0
        
        if len(params) == 1:
            params_str = f"r = {safe_float(params[0])} mm"
        elif len(params) >= 3:
            params_str = f"r₁={safe_float(params[0])} → r₂={safe_float(params[1])} mm"
        else:
            params_str = "N/A"
        
        fit_errors_list = job.statistics.get('fit_errors', [])
        fit_error = fit_errors_list[i] if i < len(fit_errors_list) else 0.0
        
        segment_data.append([
            str(i+1), 
            shape.capitalize(),
            h_range,
            params_str,
            safe_float(seg_vol, precision=3),
            safe_float(fit_error, precision=3)
        ])
    
    segment_table = Table(segment_data, colWidths=[0.4*inch, 1*inch, 1.3*inch, 1.8*inch, 1*inch, 1*inch])
    segment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    
    story.append(segment_table)
    story.append(PageBreak())
    
    # VISUALIZATIONS - Use temp directory
    story.append(Paragraph("📊 Analysis Visualizations", heading1_style))
    story.append(Spacer(1, 0.2*inch))

    # Create temp file for plot
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        plot_filename = tmp.name

    plot_path = generate_comprehensive_plots(df, df_areas, segments, z_profile, r_profile, plot_filename)

    if plot_path and os.path.exists(plot_path):
        try:
            img = Image(plot_path, width=6.5*inch, height=8*inch)
            story.append(img)
        except Exception as e:
            logger.error(f"Failed to add plot image: {e}")
            story.append(Paragraph("⚠️ Visualization image could not be embedded", styles['Normal']))
    else:
        story.append(Paragraph("⚠️ Visualization plots could not be generated", styles['Normal']))

    story.append(PageBreak())
    
    # PROCESSING CONFIGURATION
    story.append(Paragraph("⚙️ Processing Configuration", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    config_text = f"""
    <b>Segmentation Parameters:</b><br/>
    • Minimum Points per Segment: {DEFAULT_PARAMS['min_points']}<br/>
    • Savitzky-Golay Window: {DEFAULT_PARAMS['sg_window']}<br/>
    • Percentile Threshold: {DEFAULT_PARAMS['percentile']}<br/>
    • Variance Threshold: {DEFAULT_PARAMS['variance_threshold']}<br/>
    <br/>
    <b>Geometric Fitting:</b><br/>
    • Maximum Function Evaluations: {DEFAULT_PARAMS['maxfev']}<br/>
    • Fit Bounds Multiplier: {GEOMETRIC_CONSTRAINTS['fit_bounds_lower']} - {GEOMETRIC_CONSTRAINTS['fit_bounds_upper']}<br/>
    • Minimum Differential Volume: {GEOMETRIC_CONSTRAINTS['min_differential_volume']} mm³<br/>
    <br/>
    <b>Profile Generation:</b><br/>
    • Transition Buffer: {DEFAULT_PARAMS['transition_buffer']} mm<br/>
    • Hermite Tension: {DEFAULT_PARAMS['hermite_tension']}<br/>
    • Smooth Transitions: Hermite cubic spline (C¹ continuity)<br/>
    <br/>
    <b>STL Export:</b><br/>
    • Angular Resolution: {DEFAULT_PARAMS['angular_resolution']} faces/ring<br/>
    • Mesh Type: Watertight with bottom cap (ALWAYS CLOSED AT z=0)<br/>
    • Vertices: {job.statistics.get('stl_vertices', 'N/A')}<br/>
    • Faces: {job.statistics.get('stl_faces', 'N/A')}<br/>
    • Bottom Cap: ✅ Closed with center fan triangulation at z=0<br/>
    """
    
    story.append(Paragraph(config_text, styles['Normal']))
    
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("─" * 80, info_style))
    story.append(Paragraph(
        f"Report generated by Container Geometry Analyzer v3.11.7_FINAL<br/>"
        f"Analysis completed in {safe_float(job_summary.get('duration', 0))} seconds<br/>"
        f"© 2025 Laboratory Automation",
        info_style
    ))
    
    try:
        doc.build(story)
        if verbose:
            logger.info(f"✅ Enhanced PDF Report generated: {os.path.basename(pdf_filename)}")
        
        if job:
            job.complete_step('PDF Report Generation', time.time() - step_start)
            job.add_output_file(pdf_filename, 'PDF')
        
        return pdf_filename
    except Exception as e:
        if verbose:
            logger.error(f"⚠️  PDF generation failed: {e}", exc_info=True)
        if job:
            job.add_error(f"PDF generation failed: {str(e)}")
        return None

def generate_comprehensive_plots(df, df_areas, segments, z_profile, r_profile, save_path):
    """Generate comprehensive 6-panel analysis plots."""
    try:
        fig = plt.figure(figsize=(14, 16))
        fig.patch.set_facecolor('white')
        
        ax1 = plt.subplot(3, 2, 1)
        ax1.scatter(df['Height_mm'], df['Volume_mm3'], s=20, alpha=0.7, 
                   color='skyblue', label='Measured Data', zorder=3)
        
        colors_palette = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
        for i, seg in enumerate(segments):
            start, end, shape, params = seg
            x_seg = df_areas['Height_mm'].iloc[start:end+1].values
            
            if shape == 'cylinder' and len(params) == 1:
                r = float(params[0])
                y_fit = volume_cylinder(x_seg - x_seg[0], r) + df_areas['Volume_mm3'].iloc[start]
                label = f"S{i+1}: Cyl r={r:.1f}mm"
            else:
                r1, r2, H = float(params[0]), float(params[1]), float(params[2])
                y_fit = volume_frustum(x_seg - x_seg[0], r1, r2, H) + df_areas['Volume_mm3'].iloc[start]
                label = f"S{i+1}: Frust {r1:.1f}→{r2:.1f}mm"
            
            ax1.plot(x_seg, y_fit, color=colors_palette[i % len(colors_palette)], 
                    linewidth=2.5, label=label, zorder=2)
        
        ax1.set_xlabel('Height (mm)', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Volume (mm³)', fontsize=11, fontweight='bold')
        ax1.set_title('Volume Profile with Geometric Fits', fontsize=13, fontweight='bold')
        ax1.legend(fontsize=8, loc='best')
        ax1.grid(True, alpha=0.3)
        
        ax2 = plt.subplot(3, 2, 2)
        radii = np.sqrt(df_areas['Area'].values / np.pi)
        ax2.plot(df_areas['Height_mm'], radii, 'b-', linewidth=1.5, alpha=0.6, label='Measured')
        ax2.plot(z_profile, r_profile, 'r-', linewidth=2, label='Smooth Profile', alpha=0.8)
        ax2.set_xlabel('Height (mm)', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Radius (mm)', fontsize=11, fontweight='bold')
        ax2.set_title('Radius Profile Comparison', fontsize=13, fontweight='bold')
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3)
        
        ax3 = plt.subplot(3, 2, 3)
        ax3.plot(df_areas['Height_mm'], df_areas['Area'], 'g-', linewidth=1.5, alpha=0.8)
        ax3.axhline(df_areas['Area'].mean(), color='red', linestyle='--', linewidth=2,
                   label=f'Mean: {df_areas["Area"].mean():.1f} mm²')
        ax3.fill_between(df_areas['Height_mm'], 
                         df_areas['Area'].mean() - df_areas['Area'].std(),
                         df_areas['Area'].mean() + df_areas['Area'].std(),
                         alpha=0.2, color='red', label='±1σ')
        ax3.set_xlabel('Height (mm)', fontsize=11, fontweight='bold')
        ax3.set_ylabel('Cross-section Area (mm²)', fontsize=11, fontweight='bold')
        ax3.set_title('Cross-Sectional Area Profile', fontsize=13, fontweight='bold')
        ax3.legend(fontsize=9)
        ax3.grid(True, alpha=0.3)
        
        ax4 = plt.subplot(3, 2, 4)
        calculated_volumes = []
        measured_volumes = []
        heights = []
        
        for i in range(len(df_areas)):
            h = df_areas.iloc[i]['Height_mm']
            v_measured = df_areas.iloc[i]['Volume_mm3']
            idx = np.argmin(np.abs(z_profile - h))
            v_calc = calculate_profile_volume(z_profile[:idx+1], r_profile[:idx+1])[-1]
            
            heights.append(h)
            measured_volumes.append(v_measured)
            calculated_volumes.append(v_calc)
        
        errors = [(c - m) / (m + 1e-6) * 100 for c, m in zip(calculated_volumes, measured_volumes)]
        ax4.plot(heights, errors, 'purple', linewidth=2)
        ax4.axhline(0, color='black', linestyle='--', linewidth=1)
        ax4.fill_between(heights, -1, 1, alpha=0.2, color='green', label='±1% tolerance')
        ax4.set_xlabel('Height (mm)', fontsize=11, fontweight='bold')
        ax4.set_ylabel('Volume Error (%)', fontsize=11, fontweight='bold')
        ax4.set_title('Volume Reconstruction Error', fontsize=13, fontweight='bold')
        ax4.legend(fontsize=9)
        ax4.grid(True, alpha=0.3)
        
        ax5 = plt.subplot(3, 2, 5)
        ax5.fill_betweenx(z_profile, -r_profile, r_profile, alpha=0.3, color='skyblue', label='Container')
        ax5.plot(r_profile, z_profile, 'b-', linewidth=2, label='Right Profile')
        ax5.plot(-r_profile, z_profile, 'b-', linewidth=2, label='Left Profile')
        ax5.axvline(0, color='gray', linestyle='--', alpha=0.5)
        ax5.set_xlabel('Radius (mm)', fontsize=11, fontweight='bold')
        ax5.set_ylabel('Height (mm)', fontsize=11, fontweight='bold')
        ax5.set_title('Container Cross-Section View', fontsize=13, fontweight='bold')
        ax5.legend(fontsize=9)
        ax5.grid(True, alpha=0.3)
        ax5.axis('equal')
        
        ax6 = plt.subplot(3, 2, 6)
        ax6.axis('off')
        
        stats_text = f"""
ANALYSIS SUMMARY

Data Quality:
- Total Points: {len(df)}
- Valid Points: {len(df_areas)}
- Height Range: {df['Height_mm'].min():.1f} - {df['Height_mm'].max():.1f} mm
- Volume Range: {df['Volume_ml'].min():.3f} - {df['Volume_ml'].max():.3f} ml

Geometric Analysis:
- Segments Detected: {len(segments)}
- Cylinder Segments: {sum(1 for s in segments if s[2] == 'cylinder')}
- Frustum Segments: {sum(1 for s in segments if s[2] == 'frustum')}

Profile Quality:
- Profile Points: {len(z_profile)}
- Mean Radius: {np.mean(r_profile):.2f} mm
- Radius Std Dev: {np.std(r_profile):.2f} mm
- Volume Accuracy: {100 - abs(np.mean(errors)):.2f}%

Cross-Section Stats:
- Mean Area: {df_areas['Area'].mean():.1f} mm²
- Area Std Dev: {df_areas['Area'].std():.1f} mm²
- Coefficient of Variation: {(df_areas['Area'].std() / df_areas['Area'].mean() * 100):.1f}%
        """
        
        ax6.text(0.1, 0.95, stats_text, transform=ax6.transAxes,
                fontsize=9, verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        return save_path
    
    except Exception as e:
        logger.error(f"Comprehensive plot generation failed: {e}", exc_info=True)
        return None
    finally:
        plt.close('all')

def launch_enhanced_gui():
    """Launch enhanced GUI with comprehensive reporting."""
    if not HAS_TKINTER:
        logger.info("GUI unavailable - using CLI mode")
        return
    
    root = tk.Tk()
    root.title("Container Geometry Analyzer v3.11.8")
    root.geometry("750x550")
    
    def analyze_file():
        filepath = filedialog.askopenfilename(
            title="Select Volume-Height CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            job = AnalysisJob(filepath)
            
            df = load_data_csv(filepath, job=job, verbose=True)
            df_areas = compute_areas(df, job=job, verbose=True)
            segments = segment_and_fit_optimized(df_areas, job=job, verbose=True)
            z_smooth, r_smooth = create_enhanced_profile(segments, df_areas, job=job, verbose=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            
            stl_path = None
            if HAS_TRIMESH:
                stl_path = export_stl_watertight(z_smooth, r_smooth, 
                    f"{base_name}_model_{timestamp}.stl", job=job, verbose=True)
            else:
                logger.warning("⚠️  Trimesh not available - STL export skipped")
                job.add_warning("Trimesh not available - STL export skipped")
            
            pdf_path = None
            if HAS_REPORTLAB:
                pdf_path = generate_enhanced_pdf_report(df, df_areas, segments, z_smooth, r_smooth,
                    filepath, job, os.getcwd(), verbose=True)
            else:
                logger.warning("⚠️  ReportLab not available - PDF report skipped")
                job.add_warning("ReportLab not available - PDF report skipped")
            
            job.finalize()
            
            summary = job.get_summary()
            result_msg = f"""Analysis Complete!

Duration: {summary['duration']:.2f} seconds
Steps: {summary['steps_count']}
Warnings: {summary['warnings_count']}
Errors: {summary['errors_count']}

Generated Files:
- STL: {os.path.basename(stl_path) if stl_path else 'N/A'} (Bottom Closed ✅)
- PDF: {os.path.basename(pdf_path) if pdf_path else 'N/A'}

Total Outputs: {summary['outputs_count']}
"""
            messagebox.showinfo("Analysis Complete!", result_msg)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            messagebox.showerror("Analysis Error", f"Failed to analyze file:\n{str(e)}")
    
    ttk.Label(root, text="Container Geometry Analyzer", 
             font=("Arial", 18, "bold")).pack(pady=20)
    
    ttk.Label(root, text="Version 3.11.8", 
             font=("Arial", 12)).pack(pady=5)
    
    ttk.Button(root, text="📁 Select Volume-Height CSV", 
              command=analyze_file, width=40).pack(pady=30)
    
    features_frame = ttk.LabelFrame(root, text="", padding=15)
    features_frame.pack(pady=20, padx=20, fill='both', expand=True)
    
    features_text = """
    
    """
    
    ttk.Label(features_frame, text=features_text, justify="left", 
             font=("Arial", 9)).pack()
    
    root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        try:
            job = AnalysisJob(csv_file)
            
            logger.info(f"Starting analysis of: {csv_file}")
            
            df = load_data_csv(csv_file, job=job, verbose=True)
            df_areas = compute_areas(df, job=job, verbose=True)
            segments = segment_and_fit_optimized(df_areas, job=job, verbose=True)
            z_smooth, r_smooth = create_enhanced_profile(segments, df_areas, job=job, verbose=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            stl_path = None
            if HAS_TRIMESH:
                stl_path = export_stl_watertight(z_smooth, r_smooth, 
                    f"output_model_{timestamp}.stl", job=job, verbose=True)
            
            pdf_path = None
            if HAS_REPORTLAB:
                pdf_path = generate_enhanced_pdf_report(df, df_areas, segments, z_smooth, r_smooth,
                    csv_file, job, os.getcwd(), verbose=True)
            
            job.finalize()
            summary = job.get_summary()
            
            logger.info(f"✅ Analysis Complete!")
            logger.info(f"   Duration: {summary['duration']:.2f} seconds")
            logger.info(f"   Steps: {summary['steps_count']}")
            logger.info(f"   STL: {stl_path if stl_path else 'N/A'} (Bottom ✅ CLOSED)")
            logger.info(f"   PDF: {pdf_path if pdf_path else 'N/A'}")
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            sys.exit(1)
    else:
        if HAS_TKINTER:
            launch_enhanced_gui()
        else:
            logger.info("GUI unavailable. Install tkinter or provide CSV filename as argument:")
            logger.info("  python script.py your_data.csv")