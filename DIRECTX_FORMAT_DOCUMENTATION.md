# DirectX .x Format Export Documentation

## Overview

The Container Geometry Analyzer now exports **DirectX .x format** in addition to STL and HXX formats. DirectX .x is a widely-supported 3D model format created by Microsoft.

**Format**: DirectX .x ASCII (text-based)
**Extension**: `.x`
**Purpose**: 3D visualization, game engines, general 3D applications

---

## Quick Facts

| Property | Value |
|----------|-------|
| **Format Version** | xof 0303txt 0032 (DirectX 9) |
| **Encoding** | ASCII (human-readable) |
| **Mesh Type** | Triangle mesh with normals |
| **Typical Size** | 1-3 MB (similar to HXX) |
| **Vertices** | 5,000 - 10,000 (typical) |
| **Faces** | 10,000 - 20,000 triangles |

---

## Generated Files

When you run the analyzer, you now get **4 output files**:

```
my_container.csv  (input)
    ↓
[Analysis]
    ↓
├── my_container_model_TIMESTAMP.stl  (triangle mesh - 3D printing)
├── my_container_model_TIMESTAMP.hxx  (hex mesh - FEA/CFD)
├── my_container_model_TIMESTAMP.x    (DirectX - visualization) ← NEW!
└── ContainerReport_TIMESTAMP.pdf      (analysis report)
```

---

## Example Output (2ml Tube)

```
📐 DirectX .x Export:
   Filename: output_model_20251119_175602.x
   Vertices: 7,297
   Faces: 14,448
   Angular resolution: 48
   Vertical layers: 151
   Volume: 2.991 ml (approx)
   Format: DirectX .x ASCII
```

---

## File Format

### DirectX .x Structure

```
xof 0303txt 0032                 ← Header (DirectX 9 ASCII format)

Mesh ContainerMesh {             ← Mesh object begins
  7297;                          ← Number of vertices

  3.168826;0.000000;0.000000;,   ← Vertex coordinates (x;y;z;)
  3.141716;0.413615;0.000000;,
  ...

  14448;                         ← Number of faces

  3;0,1,2;,                      ← Face definition (3 vertices)
  3;0,2,3;,
  ...

  MeshNormals {                  ← Normals section
    14448;                       ← Number of normals (one per face)

    0.000000;0.000000;-1.000000;,  ← Normal vector (x;y;z;)
    0.000000;0.000000;-1.000000;,
    ...

    14448;                       ← Normal indices
    3;0,0,0;,                    ← Three normals (same for flat face)
    3;1,1,1;,
    ...
  }
}
```

---

## Compatible Software

### Native Support (Can open .x files directly)

| Software | Type | Notes |
|----------|------|-------|
| **3D Viewer (Windows)** | Built-in | Windows 10/11 default viewer |
| **MeshLab** | Open-source | File → Import → DirectX .x |
| **Blender** | 3D modeling | Via DirectX importer addon |
| **Autodesk 3ds Max** | Professional 3D | Native import |
| **Autodesk Maya** | Professional 3D | Via plugin |
| **Unity** | Game engine | Legacy format (requires converter) |
| **Open3D** | Python library | Can read .x files |

### Conversion Tools

```bash
# Using meshio (Python)
pip install meshio
python -c "import meshio; meshio.read('container.x').write('container.obj')"

# Using Blender (command-line)
blender --background --python import_x.py

# Using assimp (Open Asset Import Library)
assimp export container.x container.obj
```

---

## Comparison: STL vs HXX vs DirectX .x

| Feature | STL | HXX | DirectX .x |
|---------|-----|-----|------------|
| **Mesh Type** | Surface triangles | Volume hexahedra | Surface triangles |
| **Normals** | ❌ No | ❌ No | ✅ Yes |
| **File Size** | 100-500 KB | 1-5 MB | 1-3 MB |
| **3D Printing** | ✅ Best | ❌ No | ⚠️ Possible |
| **FEA/CFD** | ❌ No | ✅ Best | ❌ No |
| **Visualization** | ✅ Good | ⚠️ Limited | ✅ Excellent |
| **Game Engines** | ⚠️ Limited | ❌ No | ✅ Good |
| **Widespread Support** | ✅ Universal | ⚠️ Technical | ✅ Very good |

**When to use each:**
- **STL**: 3D printing, CAD, universal compatibility
- **HXX**: FEA/CFD simulations, scientific computing
- **DirectX .x**: Visualization, presentations, game engines

---

## Advantages of DirectX .x

### 1. **Includes Normals**
Unlike STL, DirectX .x includes surface normals:
- ✅ Better rendering (smooth shading)
- ✅ Lighting calculations work correctly
- ✅ Better appearance in viewers

### 2. **Human-Readable**
ASCII text format:
- ✅ Can inspect with text editor
- ✅ Easy to debug
- ✅ Can manually edit if needed

### 3. **Widely Supported**
Microsoft legacy format:
- ✅ Windows built-in support
- ✅ Many 3D modeling tools
- ✅ Convertible to other formats

### 4. **Extensible**
Can contain additional data:
- Materials (colors, textures)
- Animation data
- Hierarchy information

---

## Usage Examples

### 1. View in Windows 3D Viewer

```powershell
# Windows 10/11
start container_model_TIMESTAMP.x
# Opens in default 3D viewer
```

### 2. View in MeshLab

```bash
meshlab container_model_TIMESTAMP.x
```

**MeshLab Steps:**
1. File → Import Mesh → Select `.x` file
2. Render → Show Normals (verify normals)
3. Filters → Remeshing → Simplification (optional)
4. File → Export → Choose format

### 3. Convert to OBJ Format

```python
import meshio

# Read DirectX .x file
mesh = meshio.read("container.x")

# Export to OBJ (for Blender, Unity, etc.)
mesh.write("container.obj")

# Export to other formats
mesh.write("container.ply")   # PLY format
mesh.write("container.gltf")  # GLTF (modern web format)
```

### 4. Load in Python (Open3D)

```python
import open3d as o3d

# Read DirectX .x file
mesh = o3d.io.read_triangle_mesh("container.x")

# Compute vertex normals
mesh.compute_vertex_normals()

# Visualize
o3d.visualization.draw_geometries([mesh])

# Get mesh info
print(f"Vertices: {len(mesh.vertices)}")
print(f"Triangles: {len(mesh.triangles)}")
print(f"Has normals: {mesh.has_vertex_normals()}")
```

---

## Mesh Details

### Vertex Layout

**Revolution surface** with closed bottom:
- Sidewall vertices: Profile rotated around Z-axis
- Bottom ring: Circular edge at z=0
- Bottom center: Single vertex at (0,0,0)

### Face Layout

**Triangle mesh**:
- Sidewall: 2 triangles per quad (profile × angular resolution)
- Bottom cap: Fan triangulation from center point

**Example (48 angular divisions, 151 vertical points):**
```
Sidewall triangles: 150 layers × 48 sectors × 2 triangles = 14,400
Bottom cap triangles: 48 sectors = 48
Total: 14,448 triangles
```

### Normal Calculation

**Face normals** (per-face shading):
```python
def calculate_normal(v0, v1, v2):
    edge1 = v1 - v0
    edge2 = v2 - v0
    normal = cross(edge1, edge2)
    return normalize(normal)
```

Each triangle gets its own normal vector, computed from edge cross-product.

---

## File Size Analysis

### 2ml Tube Example

```
Vertices: 7,297
Faces: 14,448
Normals: 14,448

File size breakdown:
- Header: ~50 bytes
- Vertices: 7,297 × 45 bytes = 328 KB
- Faces: 14,448 × 25 bytes = 361 KB
- Normals (vectors): 14,448 × 45 bytes = 650 KB
- Normals (indices): 14,448 × 15 bytes = 217 KB
Total: ~1.6 MB
```

**Compression potential:**
- Binary .x format: ~50% smaller
- GLTF (compressed): ~70% smaller

---

## Customization

### Mesh Resolution

Edit `container_geometry_analyzer_gui_v3_11_8.py`, line 1339:

```python
# Default (balanced):
angular_res = 48  # 7.5° per sector

# High resolution (smoother):
angular_res = 96  # 3.75° per sector

# Low resolution (smaller file):
angular_res = 24  # 15° per sector
```

**Impact on file size:**

| Angular Res | Vertices | Faces | File Size |
|-------------|----------|-------|-----------|
| 24 | ~3,650 | ~7,200 | 0.8 MB |
| 48 | ~7,300 | ~14,400 | 1.6 MB |
| 96 | ~14,600 | ~28,800 | 3.2 MB |

---

## Technical Specifications

### DirectX .x Format Version

**xof 0303txt 0032** means:
- `xof`: X Object File
- `03`: Major version 3
- `03`: Minor version 3
- `txt`: ASCII text format (vs `bin` for binary)
- `0032`: Format version (32-bit)

This is the **DirectX 9 format**, which has the widest compatibility.

### Coordinate System

**Right-handed coordinate system:**
```
Y (up)
|
|
+---- X (right)
/
Z (forward/depth)
```

Container orientation:
- **X-Y plane**: Cross-section (circular)
- **Z-axis**: Height (vertical)
- **Z=0**: Bottom (closed)
- **Z=max**: Top (open)

---

## Validation

### Visual Inspection

```python
import open3d as o3d

mesh = o3d.io.read_triangle_mesh("container.x")

# Check if normals exist
print(f"Has normals: {mesh.has_vertex_normals()}")

# Check mesh integrity
print(f"Is watertight: {mesh.is_watertight()}")  # Should be False (open top)
print(f"Is manifold: {mesh.is_edge_manifold()}")

# Visualize with normals
mesh.compute_vertex_normals()
o3d.visualization.draw_geometries([mesh], mesh_show_wireframe=True)
```

### Volume Check

```python
# Compare DirectX volume with expected
V_directx = 2.991  # ml (from export log)
V_expected = 3.000  # ml (from CSV data)

error = abs(V_directx - V_expected) / V_expected * 100
print(f"Volume error: {error:.2f}%")  # ~0.3%
```

---

## Limitations

### What DirectX .x Does NOT Include

- ❌ **Materials/Colors**: Our export is geometry-only
- ❌ **Textures**: No UV mapping
- ❌ **Animation**: Static mesh only
- ❌ **Hierarchy**: Single mesh object

**Note**: These can be added manually in 3D modeling software if needed.

### Known Issues

1. **Unity Support**: Unity deprecated .x import. Use converter to FBX/OBJ
2. **Binary Format**: We export ASCII only (easier to debug)
3. **File Size**: Larger than binary formats (but human-readable)

---

## Conversion Examples

### To Blender

```bash
# Import in Blender
1. File → Import → DirectX (.x)
2. Select container.x
3. Adjust import settings if needed
4. File → Export → FBX/OBJ/GLTF
```

### To Unity

```bash
# Convert to FBX first
1. Open Blender
2. File → Import → DirectX (.x)
3. File → Export → FBX
4. Drag FBX into Unity Assets
```

### To Unreal Engine

```bash
# Use FBX pipeline
1. Convert .x → FBX (via Blender)
2. Import FBX into Unreal
3. Create material in Unreal
```

---

## References

### DirectX .x Format
- Official spec: https://docs.microsoft.com/en-us/windows/win32/direct3d9/dx9-graphics-reference-x-file-format
- Template reference: https://docs.microsoft.com/en-us/windows/win32/direct3d9/dx9-graphics-reference-x-file-format-templates

### Software Documentation
- MeshLab: https://www.meshlab.net/
- Open3D: http://www.open3d.org/docs/release/
- meshio: https://github.com/nschloe/meshio

---

**Document Version**: 1.0
**Software Version**: v3.11.9
**Last Updated**: 2025-11-19
**Format**: DirectX .x ASCII (xof 0303txt 0032)
