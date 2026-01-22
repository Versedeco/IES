# Blender IES Generator Plugin

A Blender plugin that generates IES (Illuminating Engineering Society) photometric files by sampling light distribution using Cycles rendering.

## Installation

1. Copy the `BlenderIESGenerator` folder to your Blender addons directory:
   - Windows: `%APPDATA%\Blender Foundation\Blender\{version}\scripts\addons\`
   - macOS: `~/Library/Application Support/Blender/{version}/scripts/addons/`
   - Linux: `~/.config/blender/{version}/scripts/addons/`

2. Open Blender and go to Edit → Preferences → Add-ons
3. Search for "IES Generator"
4. Enable the addon by checking the checkbox

## Usage

### Basic Workflow

1. **Select luminaire object** - Select any part of your light fixture assembly
2. **Analyze Luminaire** - Click to verify lights are detected correctly
3. **Initialize Environment** - Set up black field rendering environment
4. **Select quality preset** - Choose based on desired accuracy vs. time
5. **Generate IES File** - Start the sampling process

### Quality Presets

- **Quick Test**: 30°×45° steps, 256 samples (~5 min)
- **Low**: 10°×15° steps, 512 samples (~15 min)
- **Medium**: 5°×10° steps, 1024 samples (~90 min) - Recommended
- **High**: 2.5°×5° steps, 2048 samples (~6 hours)
- **Ultra**: 1°×2° steps, 4096 samples (~24+ hours)

## Technical Details

### Measurement Method

The plugin uses a white diffuse board (1.5m × 1.5m) positioned at sampling points on a sphere around the luminaire. The camera renders the board from between the light and board, measuring the luminance to calculate candela values.

### Key Fix - Board Orientation

**Problem**: Previous implementations used `-Z` tracking, causing the board's back face to point toward the light source, resulting in incorrect (dark) measurements.

**Solution**: The plugin now uses `Z` tracking in the `position_board_and_camera()` function (line 209), ensuring the board's front face (+Z normal) points toward the light source for proper illumination measurement.

```python
# CORRECT - Front face points toward light
board.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
```

### Conversion Constants

- **Blender Power to Lumens**: `Lumens = Power × 4.30` (from test documentation)
- **Luminance to Candela**: `Candela = Luminance × π × radius²`

### Environment Requirements

- Render Engine: Cycles
- Color Management: Raw (gamma 1.0, exposure 0.0)
- World: Pure black (strength 0.0)
- File Format: OpenEXR (32-bit RGB)

## File Output

The plugin generates standard IESNA:LM-63-2002 format files with:
- Type C photometric data
- Metric units (meters)
- Full spherical sampling (0-180° vertical, 0-360° horizontal)
- Custom headers with generation metadata

## Limitations

- Only supports Blender light objects (not emission shaders)
- Requires manual environment setup for accurate results
- Long generation times for high quality settings
- Cannot cancel during individual render (only between samples)

## Support

For issues or questions, please refer to the project repository.
