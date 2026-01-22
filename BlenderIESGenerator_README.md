# Blender IES Generator Plugin - Installation & Quick Start

## 🎯 What This Plugin Does

Generates IES (Illuminating Engineering Society) photometric files from Blender lights by:
- Positioning a white diffuse board on a sphere around your luminaire
- Rendering the board at multiple angles using Cycles
- Measuring luminance from the renders
- Converting measurements to candela values
- Exporting standard IES format files

## ⚡ Key Feature: Board Orientation Fix

This implementation includes a **critical fix** that ensures the white measurement board faces the light source correctly:

```python
# ✅ CORRECT - Front face points toward light
board.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()

# ❌ INCORRECT - Would make back face point toward light
# board.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
```

**Impact**: This one-character fix is the difference between getting usable IES files and getting all-zero values.

## 📦 Installation

### Step 1: Locate Blender Addons Directory

**Windows:**
```
%APPDATA%\Blender Foundation\Blender\{version}\scripts\addons\
```

**macOS:**
```
~/Library/Application Support/Blender/{version}/scripts/addons/
```

**Linux:**
```
~/.config/blender/{version}/scripts/addons/
```

### Step 2: Copy Plugin

Copy the entire `BlenderIESGenerator` folder to your addons directory.

### Step 3: Enable in Blender

1. Open Blender
2. Go to: **Edit → Preferences → Add-ons**
3. Search for: **"IES Generator"**
4. Check the checkbox to enable it
5. Find the panel in: **3D View → Sidebar (N key) → IES Generator tab**

## 🚀 Quick Start Guide

### 5-Step Workflow

1. **Select your luminaire**
   - Click on any part of your light fixture
   - Works with individual lights or assemblies

2. **Analyze the luminaire**
   - Click "Analyze Luminaire" button
   - Verify that all lights are detected
   - Check the reported size and center

3. **Initialize environment**
   - Click "Initialize Sampling Environment"
   - This sets up: Cycles engine, black world, Raw color management

4. **Choose quality preset**
   - Start with "Quick" for testing (5 minutes)
   - Use "Medium" for production (90 minutes)
   - Higher quality = more samples = longer time

5. **Generate IES file**
   - Click "Generate IES File"
   - Monitor progress in console (10% updates)
   - File saves to specified output path

## 🎚️ Quality Presets Explained

| Preset | Angular Steps | Render Samples | Estimated Time |
|--------|--------------|----------------|----------------|
| Quick  | 30° × 45°    | 256           | ~5 minutes     |
| Low    | 10° × 15°    | 512           | ~15 minutes    |
| Medium | 5° × 10°     | 1024          | ~90 minutes    |
| High   | 2.5° × 5°    | 2048          | ~6 hours       |
| Ultra  | 1° × 2°      | 4096          | ~24+ hours     |

**Recommendation**: Start with Quick for testing, use Medium for most work.

## 📊 Understanding the Output

### IES File Format

The plugin generates IESNA:LM-63-2002 format files containing:
- Candela values at different angles (vertical: 0-180°, horizontal: 0-360°)
- Total lumens (calculated from Blender light power × 4.30)
- Metadata (lumens per lamp, photometric type, units)

### Viewing Your IES File

Open the generated `.ies` file in lighting software such as:
- **DIALux** (free, Windows)
- **AGi32** (commercial)
- **Relux** (free, Windows/Mac)
- **IES Viewer** (various free options available)

## 🔧 Adjusting Parameters

### Sampling Radius
- Default: 5 meters
- Smaller radius = faster renders, but may miss detail
- Larger radius = slower renders, more accurate far-field pattern
- Rule of thumb: Use 5-10× the luminaire size

### Sphere Center Offset
- Adjusts the center point of the sampling sphere
- Use when your luminaire's geometric center doesn't match its optical center
- Example: Floor lamp with shade mostly at top

## ⚠️ Important Notes

### Requirements
- ✅ Blender 3.0 or later
- ✅ Cycles render engine
- ✅ At least one light object in the scene

### Limitations
- ❌ Does not support emission shaders (only light objects)
- ❌ Cannot cancel during individual render (only between samples)
- ❌ All lights must have energy > 0

### Best Practices
1. **Test first**: Always run Quick preset before long generations
2. **Save your work**: Generation cannot be resumed if interrupted
3. **Black field**: Use "Initialize Environment" for accurate results
4. **Monitor console**: Watch for errors or warnings during generation

## 🐛 Troubleshooting

### "No lights found in luminaire assembly"
- Make sure you have at least one light object
- Check that light energy > 0
- Verify light isn't hidden or on disabled layer

### All values in IES file are zero
- Check that "Initialize Environment" was run
- Verify Cycles is the render engine
- Ensure color management is set to "Raw"
- Check that lights have normalize = False

### Generation is very slow
- Start with "Quick" preset for testing
- Close other applications to free up CPU/GPU
- Consider lowering quality preset

### Render appears completely black
- This should not happen with the board orientation fix
- If it does, check world background strength is 0.0
- Verify board material is pure white diffuse

## 📚 Documentation

The `BlenderIESGenerator` folder contains additional documentation:

- **README.md** - Detailed user guide
- **CHANGELOG.md** - Version history and fix details
- **TECHNICAL_NOTES.md** - In-depth technical explanation
- **FIX_COMPARISON.md** - Visual before/after comparison

## 🆘 Getting Help

1. Check the documentation files in the BlenderIESGenerator folder
2. Review the implementation summary (IMPLEMENTATION_SUMMARY.md)
3. Search for similar issues in the repository
4. Open an issue with:
   - Blender version
   - Plugin version
   - Error messages from console
   - Description of the problem

## 🎓 Technical Details

### How It Works

```
1. Create white diffuse board (1.5m × 1.5m)
2. Loop through sampling angles on sphere
   For each angle:
   - Position board on sphere surface
   - Orient board to face inward (toward light)  ← KEY FIX
   - Position camera between board and light
   - Render the board with Cycles
   - Extract luminance from center pixels
   - Convert: Luminance → Illuminance → Candela
3. Write all candela values to IES file
```

### The Critical Fix Explained

The board must face the light to reflect properly:
- **+Z axis** is the front face normal (the side that reflects light)
- **-Z axis** is the back face (doesn't reflect light properly)

By using `'Z'` tracking (not `'-Z'`), we ensure the +Z axis points toward the light source, making the reflective front face face the light.

## 📜 License & Credits

Part of the IES project at https://github.com/Versedeco/IES

Implements the measurement methodology described in the project's test documentation.

---

**Quick Reference**: Select object → Analyze → Initialize → Choose quality → Generate

**First Time?** Start with Quick preset to verify everything works!

