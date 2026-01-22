# Changelog

## Version 1.0.0 - Initial Release

### Critical Fix: White Board Orientation

**Problem:**
Previous implementations (or theoretical bugs) used `-Z` tracking for the measurement board, causing the board's back face to point toward the light source. This resulted in incorrect (dark/black) measurements because the back face of a plane does not reflect light properly.

**Solution:**
The plugin now uses `Z` tracking in the `position_board_and_camera()` function at line 209:

```python
# CORRECT - Front face (+Z normal) points toward light
board.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()

# INCORRECT (what it should NOT be):
# board.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
```

**Impact:**
- Ensures proper illumination measurement
- Board front face (+Z normal) now correctly faces the light source
- Resolves white/black rendering issue
- Enables accurate candela value calculation

### Features

- Modal operator for non-blocking UI during generation
- Multi-object luminaire detection (Collections, parent-child relationships)
- Configurable quality presets (Quick to Ultra)
- Spherical sampling with customizable radius and center offset
- IES file generation in IESNA:LM-63-2002 format
- Manual environment initialization for black field rendering
- Progress tracking with console output
- Automatic luminaire size and center calculation

### Technical Specifications

- **Measurement Method**: White diffuse board (1.5m × 1.5m)
- **Material**: Pure white Diffuse BSDF (color=1,1,1, roughness=1.0)
- **Conversion**: Blender Power × 4.30 = Lumens
- **Sampling**: Spherical coordinates (theta: 0-180°, phi: 0-360°)
- **File Format**: IESNA:LM-63-2002 Type C photometric data

### Requirements

- Blender 3.0 or later
- Cycles render engine
- Black field environment (Raw color management, gamma 1.0)

### Known Limitations

- Only supports Blender light objects (not emission shaders)
- Long generation times for high quality settings
- Cannot cancel during individual render (only between samples)

