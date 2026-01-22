"""
Blender IES Generator Plugin
Generates IES photometric files by sampling light distribution using Cycles rendering
"""

bl_info = {
    "name": "IES Generator",
    "author": "Versedeco",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > IES Generator",
    "description": "Generate IES files from Blender lights by sampling sphere",
    "category": "Lighting",
}

import bpy
import bmesh
import math
import mathutils
import os
from datetime import datetime

# Constants from test documentation
ENERGY_TO_LUMENS = 4.30  # Blender Power to Lumens conversion

# Quality presets
QUALITY_PRESETS = {
    'QUICK': {'theta_step': 30, 'phi_step': 45, 'samples': 256, 'desc': 'Quick Test (~5 min)'},
    'LOW': {'theta_step': 10, 'phi_step': 15, 'samples': 512, 'desc': 'Low (~15 min)'},
    'MEDIUM': {'theta_step': 5, 'phi_step': 10, 'samples': 1024, 'desc': 'Medium (~90 min)'},
    'HIGH': {'theta_step': 2.5, 'phi_step': 5, 'samples': 2048, 'desc': 'High (~6 hours)'},
    'ULTRA': {'theta_step': 1, 'phi_step': 2, 'samples': 4096, 'desc': 'Ultra (~24+ hours)'},
}


def spherical_to_cartesian(radius, theta_deg, phi_deg, center=None):
    """Convert spherical coordinates to Cartesian coordinates"""
    theta = math.radians(theta_deg)
    phi = math.radians(phi_deg)
    
    x = radius * math.sin(theta) * math.cos(phi)
    y = radius * math.sin(theta) * math.sin(phi)
    z = radius * math.cos(theta)
    
    relative_pos = mathutils.Vector((x, y, z))
    
    if center:
        return center + relative_pos
    return relative_pos


def get_luminaire_objects(obj):
    """Get all objects that are part of the luminaire assembly"""
    objects = [obj]
    
    # Add all children recursively
    objects.extend(obj.children_recursive)
    
    # Add parent and its children
    if obj.parent:
        objects.append(obj.parent)
        objects.extend(obj.parent.children_recursive)
    
    # Add objects from same collections
    for collection in obj.users_collection:
        for coll_obj in collection.objects:
            if coll_obj.type in ['MESH', 'LIGHT', 'CURVE', 'SURFACE', 'META', 'FONT']:
                if coll_obj not in objects:
                    objects.append(coll_obj)
    
    return list(set(objects))


def calculate_luminaire_size(obj):
    """Calculate bounding box size including all related objects"""
    objects = get_luminaire_objects(obj)
    
    if not objects:
        return 1.0
    
    # Calculate combined bounding box
    min_co = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    max_co = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
    
    for obj in objects:
        if obj.type == 'MESH':
            for vertex in obj.data.vertices:
                world_co = obj.matrix_world @ vertex.co
                min_co.x = min(min_co.x, world_co.x)
                min_co.y = min(min_co.y, world_co.y)
                min_co.z = min(min_co.z, world_co.z)
                max_co.x = max(max_co.x, world_co.x)
                max_co.y = max(max_co.y, world_co.y)
                max_co.z = max(max_co.z, world_co.z)
        elif obj.type == 'LIGHT':
            world_co = obj.matrix_world.translation
            min_co.x = min(min_co.x, world_co.x)
            min_co.y = min(min_co.y, world_co.y)
            min_co.z = min(min_co.z, world_co.z)
            max_co.x = max(max_co.x, world_co.x)
            max_co.y = max(max_co.y, world_co.y)
            max_co.z = max(max_co.z, world_co.z)
    
    size = max_co - min_co
    return max(size.x, size.y, size.z)


def calculate_luminaire_center(obj):
    """Calculate geometric center of luminaire including all related objects"""
    objects = get_luminaire_objects(obj)
    
    if not objects:
        return mathutils.Vector((0, 0, 0))
    
    # Calculate combined bounding box center
    min_co = mathutils.Vector((float('inf'), float('inf'), float('inf')))
    max_co = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
    
    for obj in objects:
        if obj.type == 'MESH':
            for vertex in obj.data.vertices:
                world_co = obj.matrix_world @ vertex.co
                min_co.x = min(min_co.x, world_co.x)
                min_co.y = min(min_co.y, world_co.y)
                min_co.z = min(min_co.z, world_co.z)
                max_co.x = max(max_co.x, world_co.x)
                max_co.y = max(max_co.y, world_co.y)
                max_co.z = max(max_co.z, world_co.z)
        elif obj.type == 'LIGHT':
            world_co = obj.matrix_world.translation
            min_co.x = min(min_co.x, world_co.x)
            min_co.y = min(min_co.y, world_co.y)
            min_co.z = min(min_co.z, world_co.z)
            max_co.x = max(max_co.x, world_co.x)
            max_co.y = max(max_co.y, world_co.y)
            max_co.z = max(max_co.z, world_co.z)
    
    center = (min_co + max_co) / 2
    return center


def create_measurement_board(context):
    """Create a white diffuse board for measurement (1.5m x 1.5m)"""
    # Create mesh
    mesh = bpy.data.meshes.new("IES_MeasurementBoard")
    obj = bpy.data.objects.new("IES_MeasurementBoard", mesh)
    context.collection.objects.link(obj)
    
    # Create 1.5m x 1.5m plane
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.75)
    bm.to_mesh(mesh)
    bm.free()
    
    # Create white diffuse material
    mat = bpy.data.materials.new(name="IES_WhiteDiffuse")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Diffuse BSDF
    diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
    diffuse.inputs['Color'].default_value = (1, 1, 1, 1)  # Pure white
    diffuse.inputs['Roughness'].default_value = 1.0  # Perfect diffuse
    
    # Output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    
    # Link
    mat.node_tree.links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])
    
    # Assign material
    obj.data.materials.append(mat)
    
    return obj


def create_measurement_camera(context):
    """Create camera for measurement"""
    camera_data = bpy.data.cameras.new("IES_MeasurementCamera")
    camera = bpy.data.objects.new("IES_MeasurementCamera", camera_data)
    context.collection.objects.link(camera)
    
    # Set camera to orthographic
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = 2.0
    
    return camera


def position_board_and_camera(board, camera, sphere_center, radius, theta, phi):
    """
    Position measurement board and camera at sampling point
    
    KEY FIX: Uses 'Z' tracking so board's FRONT FACE (+Z normal) points toward light
    Previously used '-Z' which made the BACK FACE point toward light
    """
    # Calculate board position on sphere
    board_pos = spherical_to_cartesian(radius, theta, phi, sphere_center)
    board.location = board_pos
    
    # Calculate direction from board to sphere center (toward light)
    direction = sphere_center - board_pos
    direction.normalize()
    
    # CRITICAL FIX: Use 'Z' instead of '-Z' to make front face point toward light
    # 'Z' means the +Z axis (front face normal) will point in the direction vector
    # '-Z' would mean the -Z axis (back face) would point in the direction vector
    board.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    
    # Position camera between light and board
    camera_distance = radius * 0.3  # 30% of radius from center
    camera_pos = spherical_to_cartesian(camera_distance, theta, phi, sphere_center)
    camera.location = camera_pos
    
    # Point camera at board
    camera_direction = board_pos - camera_pos
    camera.rotation_euler = camera_direction.to_track_quat('-Z', 'Y').to_euler()


def measure_luminance(context, image_path, sample_size=40):
    """Extract luminance from rendered image center region"""
    # Load image
    image = bpy.data.images.load(image_path)
    
    width = image.size[0]
    height = image.size[1]
    
    # Sample center region
    cx = width // 2
    cy = height // 2
    half_size = sample_size // 2
    
    total_luminance = 0
    pixel_count = 0
    
    # Get pixels
    pixels = list(image.pixels)
    
    for y in range(cy - half_size, cy + half_size):
        for x in range(cx - half_size, cx + half_size):
            if 0 <= x < width and 0 <= y < height:
                idx = (y * width + x) * 4
                # Luminance = 0.2126*R + 0.7152*G + 0.0722*B
                r = pixels[idx]
                g = pixels[idx + 1]
                b = pixels[idx + 2]
                luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
                total_luminance += luminance
                pixel_count += 1
    
    # Cleanup
    bpy.data.images.remove(image)
    
    if pixel_count > 0:
        return total_luminance / pixel_count
    return 0


def write_ies_file(filepath, vertical_angles, horizontal_angles, candela_values, total_lumens, sampling_radius):
    """Write IES file in IESNA:LM-63-2002 format"""
    with open(filepath, 'w') as f:
        # Header
        f.write("IESNA:LM-63-2002\n")
        f.write("[TEST] Generated by Blender IES Generator\n")
        f.write(f"[MANUFAC] Blender Export\n")
        f.write(f"[LUMCAT] Blender_Light\n")
        f.write(f"[LUMINAIRE] Blender IES Generated Luminaire\n")
        f.write(f"[LAMP] Blender Light Source\n")
        f.write(f"[MORE] Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n")
        
        # TILT line
        f.write("TILT=NONE\n")
        
        # Photometric data header
        num_lamps = 1
        lumens_per_lamp = total_lumens
        candela_multiplier = 1.0
        num_vertical = len(vertical_angles)
        num_horizontal = len(horizontal_angles)
        photometric_type = 1  # Type C
        units_type = 1  # Meters
        width = 0.0
        length = 0.0
        height = 0.0
        
        # Line 1: lamp parameters
        f.write(f"{num_lamps} {lumens_per_lamp:.1f} {candela_multiplier} "
                f"{num_vertical} {num_horizontal} {photometric_type} "
                f"{units_type} {width:.2f} {length:.2f} {height:.2f}\n")
        
        # Line 2: ballast factor, future use, input watts
        f.write(f"1.00 1.00 {sampling_radius}\n")
        
        # Vertical angles
        for angle in vertical_angles:
            f.write(f"{angle:.1f} ")
        f.write("\n")
        
        # Horizontal angles
        for angle in horizontal_angles:
            f.write(f"{angle:.1f} ")
        f.write("\n")
        
        # Candela values
        for h_idx in range(len(horizontal_angles)):
            for v_idx in range(len(vertical_angles)):
                value = candela_values[v_idx][h_idx]
                f.write(f"{value:.2f}\n")


class IES_PG_Settings(bpy.types.PropertyGroup):
    """Property group for IES generator settings"""
    
    sampling_radius: bpy.props.FloatProperty(
        name="Sampling Radius",
        description="Distance from luminaire center to measurement board",
        default=5.0,
        min=1.0,
        max=100.0,
        unit='LENGTH'
    )
    
    sphere_center_offset: bpy.props.FloatVectorProperty(
        name="Sphere Center Offset",
        description="Offset from auto-calculated luminaire center",
        default=(0.0, 0.0, 0.0),
        subtype='XYZ',
        unit='LENGTH'
    )
    
    quality_preset: bpy.props.EnumProperty(
        name="Quality",
        description="Sampling quality preset",
        items=[
            ('QUICK', 'Quick Test', 'Quick test quality (~5 min)'),
            ('LOW', 'Low', 'Low quality (~15 min)'),
            ('MEDIUM', 'Medium', 'Medium quality (~90 min) - Recommended'),
            ('HIGH', 'High', 'High quality (~6 hours)'),
            ('ULTRA', 'Ultra', 'Ultra quality (~24+ hours)'),
        ],
        default='MEDIUM'
    )
    
    output_path: bpy.props.StringProperty(
        name="Output Path",
        description="Path to save IES file",
        default="//output.ies",
        subtype='FILE_PATH'
    )
    
    progress: bpy.props.FloatProperty(
        name="Progress",
        description="Generation progress",
        default=0.0,
        min=0.0,
        max=100.0,
        subtype='PERCENTAGE'
    )
    
    is_generating: bpy.props.BoolProperty(
        name="Is Generating",
        description="Is currently generating IES file",
        default=False
    )


class IES_OT_AnalyzeLuminaire(bpy.types.Operator):
    """Analyze selected luminaire and detect all lights"""
    bl_idname = "ies.analyze_luminaire"
    bl_label = "Analyze Luminaire"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj:
            self.report({'ERROR'}, "No object selected")
            return {'CANCELLED'}
        
        # Get all related objects
        objects = get_luminaire_objects(obj)
        lights = [o for o in objects if o.type == 'LIGHT']
        
        # Calculate size and center
        size = calculate_luminaire_size(obj)
        center = calculate_luminaire_center(obj)
        
        self.report({'INFO'}, 
                   f"Found {len(lights)} lights in assembly. "
                   f"Size: {size:.2f}m, Center: ({center.x:.2f}, {center.y:.2f}, {center.z:.2f})")
        
        return {'FINISHED'}


class IES_OT_InitializeEnvironment(bpy.types.Operator):
    """Initialize black field environment for IES sampling"""
    bl_idname = "ies.initialize_environment"
    bl_label = "Initialize Sampling Environment"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        
        # Set render engine to Cycles
        scene.render.engine = 'CYCLES'
        
        # Set black field environment
        if not scene.world:
            scene.world = bpy.data.worlds.new("World")
        
        world = scene.world
        world.use_nodes = True
        
        # Set background to pure black
        bg_node = world.node_tree.nodes.get('Background')
        if bg_node:
            bg_node.inputs['Color'].default_value = (0, 0, 0, 1)
            bg_node.inputs['Strength'].default_value = 0.0
        
        # Set color management to Raw
        scene.view_settings.view_transform = 'Raw'
        scene.view_settings.exposure = 0.0
        scene.view_settings.gamma = 1.0
        
        # Set render settings
        scene.render.image_settings.file_format = 'OPEN_EXR'
        scene.render.image_settings.color_mode = 'RGB'
        scene.render.image_settings.color_depth = '32'
        
        self.report({'INFO'}, "Environment initialized for IES sampling")
        return {'FINISHED'}


class IES_OT_Generate(bpy.types.Operator):
    """Generate IES file by sampling light distribution"""
    bl_idname = "ies.generate"
    bl_label = "Generate IES File"
    bl_options = {'REGISTER'}
    
    _timer = None
    _board = None
    _camera = None
    _original_camera = None
    _theta_angles = []
    _phi_angles = []
    _current_theta_idx = 0
    _current_phi_idx = 0
    _candela_values = []
    _total_energy = 0
    _temp_dir = None
    _sphere_center = None
    _sampling_radius = 0
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            settings = context.scene.ies_settings
            
            # Check if cancelled
            if not settings.is_generating:
                self.cancel(context)
                return {'CANCELLED'}
            
            # Process next sample
            if self._current_theta_idx < len(self._theta_angles):
                theta = self._theta_angles[self._current_theta_idx]
                phi = self._phi_angles[self._current_phi_idx]
                
                # Position board and camera
                position_board_and_camera(
                    self._board, self._camera,
                    self._sphere_center, self._sampling_radius,
                    theta, phi
                )
                
                # Render
                temp_file = os.path.join(self._temp_dir, f"sample_{self._current_theta_idx}_{self._current_phi_idx}.exr")
                context.scene.render.filepath = temp_file
                bpy.ops.render.render(write_still=True)
                
                # Measure luminance
                luminance = measure_luminance(context, temp_file)
                
                # Convert to candela
                # Luminance -> Illuminance (×π) -> Intensity (×r²)
                illuminance = luminance * math.pi
                intensity = illuminance * (self._sampling_radius ** 2)
                
                # Store candela value
                self._candela_values[self._current_theta_idx][self._current_phi_idx] = intensity
                
                # Update progress
                total_samples = len(self._theta_angles) * len(self._phi_angles)
                current_sample = self._current_theta_idx * len(self._phi_angles) + self._current_phi_idx + 1
                settings.progress = (current_sample / total_samples) * 100
                
                # Print progress every 10%
                if current_sample % max(1, total_samples // 10) == 0:
                    print(f"Progress: {settings.progress:.1f}% ({current_sample}/{total_samples})")
                
                # Move to next sample
                self._current_phi_idx += 1
                if self._current_phi_idx >= len(self._phi_angles):
                    self._current_phi_idx = 0
                    self._current_theta_idx += 1
                
                return {'RUNNING_MODAL'}
            else:
                # All samples complete
                self.finish_generation(context)
                return {'FINISHED'}
        
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        settings = context.scene.ies_settings
        
        # Validate
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "No object selected")
            return {'CANCELLED'}
        
        # Get all lights
        objects = get_luminaire_objects(obj)
        lights = [o for o in objects if o.type == 'LIGHT']
        
        if not lights:
            self.report({'ERROR'}, "No lights found in luminaire assembly")
            return {'CANCELLED'}
        
        # Store initial energy values
        self._total_energy = sum(light.data.energy for light in lights)
        
        # Get quality preset
        preset = QUALITY_PRESETS[settings.quality_preset]
        theta_step = preset['theta_step']
        phi_step = preset['phi_step']
        samples = preset['samples']
        
        # Set render samples
        context.scene.cycles.samples = samples
        
        # Calculate sphere center
        auto_center = calculate_luminaire_center(obj)
        self._sphere_center = auto_center + mathutils.Vector(settings.sphere_center_offset)
        self._sampling_radius = settings.sampling_radius
        
        # Generate sampling angles
        self._theta_angles = []
        theta = 0
        while theta <= 180:
            self._theta_angles.append(theta)
            theta += theta_step
        if self._theta_angles[-1] != 180:
            self._theta_angles.append(180)
        
        self._phi_angles = []
        phi = 0
        while phi < 360:
            self._phi_angles.append(phi)
            phi += phi_step
        
        # Initialize candela values array
        self._candela_values = [[0.0 for _ in range(len(self._phi_angles))] 
                                for _ in range(len(self._theta_angles))]
        
        # Create measurement equipment
        self._board = create_measurement_board(context)
        self._camera = create_measurement_camera(context)
        
        # Store original camera
        self._original_camera = context.scene.camera
        context.scene.camera = self._camera
        
        # Create temp directory
        import tempfile
        self._temp_dir = tempfile.mkdtemp()
        
        # Initialize indices
        self._current_theta_idx = 0
        self._current_phi_idx = 0
        
        # Set generating flag
        settings.is_generating = True
        settings.progress = 0
        
        # Start timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        print(f"Starting IES generation: {len(self._theta_angles)}×{len(self._phi_angles)} samples")
        
        return {'RUNNING_MODAL'}
    
    def finish_generation(self, context):
        """Complete generation and save IES file"""
        settings = context.scene.ies_settings
        
        # Calculate total lumens
        total_lumens = self._total_energy * ENERGY_TO_LUMENS
        
        # Write IES file
        output_path = bpy.path.abspath(settings.output_path)
        write_ies_file(
            output_path,
            self._theta_angles,
            self._phi_angles,
            self._candela_values,
            total_lumens,
            self._sampling_radius
        )
        
        print(f"IES file saved: {output_path}")
        print(f"Total lumens: {total_lumens:.1f}")
        
        self.report({'INFO'}, f"IES file generated: {output_path}")
        
        # Cleanup
        self.cancel(context)
    
    def cancel(self, context):
        """Cleanup on cancel or finish"""
        settings = context.scene.ies_settings
        settings.is_generating = False
        settings.progress = 0
        
        # Remove timer
        if self._timer:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
            self._timer = None
        
        # Cleanup objects
        if self._board:
            bpy.data.objects.remove(self._board, do_unlink=True)
            self._board = None
        
        if self._camera:
            bpy.data.objects.remove(self._camera, do_unlink=True)
            self._camera = None
        
        # Restore original camera
        if self._original_camera:
            context.scene.camera = self._original_camera
        
        # Cleanup temp files
        if self._temp_dir and os.path.exists(self._temp_dir):
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None


class IES_PT_MainPanel(bpy.types.Panel):
    """Main IES Generator panel"""
    bl_label = "IES Generator"
    bl_idname = "IES_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'IES Generator'
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.ies_settings
        
        # Info
        layout.label(text="Blender IES Generator", icon='LIGHT')
        layout.separator()
        
        # Analyze button
        layout.operator("ies.analyze_luminaire", icon='INFO')
        
        # Status
        if settings.is_generating:
            layout.label(text="Generating...", icon='TIME')
            layout.progress(factor=settings.progress/100, text=f"{settings.progress:.1f}%")


class IES_PT_SamplingPanel(bpy.types.Panel):
    """Sampling parameters panel"""
    bl_label = "Sampling Parameters"
    bl_idname = "IES_PT_sampling_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'IES Generator'
    bl_parent_id = "IES_PT_main_panel"
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.ies_settings
        
        layout.prop(settings, "sampling_radius")
        layout.prop(settings, "sphere_center_offset")


class IES_PT_QualityPanel(bpy.types.Panel):
    """Quality settings panel"""
    bl_label = "Quality Settings"
    bl_idname = "IES_PT_quality_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'IES Generator'
    bl_parent_id = "IES_PT_main_panel"
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.ies_settings
        
        layout.prop(settings, "quality_preset")
        
        # Show preset details
        preset = QUALITY_PRESETS[settings.quality_preset]
        box = layout.box()
        box.label(text=f"Angular steps: {preset['theta_step']}°×{preset['phi_step']}°")
        box.label(text=f"Render samples: {preset['samples']}")
        box.label(text=f"Est. time: {preset['desc']}")
        
        layout.separator()
        layout.operator("ies.initialize_environment", icon='WORLD')


class IES_PT_OutputPanel(bpy.types.Panel):
    """Output settings panel"""
    bl_label = "Output"
    bl_idname = "IES_PT_output_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'IES Generator'
    bl_parent_id = "IES_PT_main_panel"
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.ies_settings
        
        layout.prop(settings, "output_path")
        
        layout.separator()
        
        if settings.is_generating:
            layout.operator("ies.generate", text="Generating...", icon='TIME').enabled = False
        else:
            layout.operator("ies.generate", text="Generate IES File", icon='PLAY')


class IES_PT_HelpPanel(bpy.types.Panel):
    """Help panel"""
    bl_label = "Usage Instructions"
    bl_idname = "IES_PT_help_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'IES Generator'
    bl_parent_id = "IES_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Workflow:", icon='INFO')
        box.label(text="1. Select luminaire object")
        box.label(text="2. Click 'Analyze Luminaire'")
        box.label(text="3. Click 'Initialize Environment'")
        box.label(text="4. Select quality preset")
        box.label(text="5. Click 'Generate IES File'")


# Registration
classes = (
    IES_PG_Settings,
    IES_OT_AnalyzeLuminaire,
    IES_OT_InitializeEnvironment,
    IES_OT_Generate,
    IES_PT_MainPanel,
    IES_PT_SamplingPanel,
    IES_PT_QualityPanel,
    IES_PT_OutputPanel,
    IES_PT_HelpPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.ies_settings = bpy.props.PointerProperty(type=IES_PG_Settings)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.ies_settings


if __name__ == "__main__":
    register()
