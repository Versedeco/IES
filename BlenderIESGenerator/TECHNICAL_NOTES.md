# Technical Notes: Board Orientation Fix

## The Problem in Detail

When measuring light distribution, we position a white diffuse board on a sphere around the light source. The board needs to face the light source to properly reflect and measure the illumination.

### Coordinate System in Blender

In Blender:
- **+Z axis** points "up" from a surface (the normal vector)
- **-Z axis** points "down" into a surface (the back face)

### The Issue with `-Z` Tracking

When using `direction.to_track_quat('-Z', 'Y')`:
```
Light Source (center)
        ↓
        ↓  Light rays traveling outward
        ↓
    [  Board  ]  ← Board positioned on sphere
    Back face (-Z) pointing toward light
    Front face (+Z) pointing away from light
    
Result: Board back face "sees" the light, but doesn't reflect properly
        → Dark/black measurements
```

### The Fix with `Z` Tracking

When using `direction.to_track_quat('Z', 'Y')`:
```
Light Source (center)
        ↓
        ↓  Light rays traveling outward
        ↓
    [  Board  ]  ← Board positioned on sphere
    Front face (+Z) pointing toward light
    Back face (-Z) pointing away from light
    
Result: Board front face "sees" the light and reflects properly
        → Bright/white measurements with accurate values
```

## Code Location

**File**: `BlenderIESGenerator/__init__.py`  
**Function**: `position_board_and_camera()`  
**Line**: 209

```python
def position_board_and_camera(board, camera, sphere_center, radius, theta, phi):
    # ... position calculation ...
    
    # Direction vector from board to light source center
    direction = sphere_center - board_pos
    direction.normalize()
    
    # KEY FIX: Use 'Z' to align +Z axis (front normal) with direction
    board.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    #                                              ^^^
    #                                              This 'Z' is critical!
```

## Why This Matters

1. **Measurement Accuracy**: Only the front face of the diffuse board properly reflects light according to Lambert's cosine law

2. **Physically Correct**: In real photometric measurements, the sensor/board always faces the light source

3. **IES Data Quality**: Incorrect orientation leads to near-zero candela values, making the IES file useless

## Testing the Fix

To verify the fix works:

1. Create a simple point light in Blender
2. Position a board at distance R from the light
3. Render with board using `Z` tracking vs `-Z` tracking
4. Compare luminance values:
   - `Z` tracking: Should show bright white (values near 1.0)
   - `-Z` tracking: Should show dark/black (values near 0.0)

## Mathematical Flow

```
Light Power (Watts)
    ↓ × 4.30 (Blender conversion)
Lumens
    ↓ Sample at positions
Luminance (cd/m²) from rendered board
    ↓ × π (Lambert's law)
Illuminance (lux)
    ↓ × r² (inverse square law)
Candela (cd) → IES file
```

The board orientation affects the luminance measurement, which propagates through the entire calculation chain.

## References

- Blender Coordinate System: https://docs.blender.org/manual/en/latest/modeling/introduction.html
- Quaternion Tracking: https://docs.blender.org/api/current/mathutils.html#mathutils.Vector.to_track_quat
- Lambert's Cosine Law: Illuminance = Luminance × π (for perfectly diffuse surface)
- IES LM-63-2002: Standard file format for photometric data

