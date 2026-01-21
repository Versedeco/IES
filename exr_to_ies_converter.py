#!/usr/bin/env python3
"""
EXR to IES Converter
从Blender烘焙的EXR光照分布生成IES光度文件

主要功能：
1. 自动计算测量距离（基于灯具尺寸）
2. 创建和配置测量球体
3. 烘焙光照分布到EXR
4. 从EXR转换为IES格式
5. 支持多种灯具参数和配置

⚠️ 注意：此脚本必须在Blender内部运行
- bpy 和 mathutils 是Blender专用模块
- 在普通Python环境中会显示导入错误，这是正常的

作者：EXR to IES Project
日期：2026-01-21
版本：1.0
"""

# Blender专用模块（仅在Blender中可用）
import bpy  # type: ignore
from mathutils import Vector  # type: ignore

# 标准库
import numpy as np
from pathlib import Path
from datetime import datetime

# 导入辐射瓦特转换器
try:
    from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter
except ImportError:
    print("⚠️  警告：无法导入 ProductsParametersToRadiantWatts，将使用简化计算")
    LampSpecsToRadiantConverter = None


class LuminaireParameters:
    """灯具参数类 - 用于描述灯具的完整信息"""

    def __init__(self,
                 # 基本信息
                 name="Custom Luminaire",
                 manufacturer="Unknown",
                 catalog_number="",
                 description="",

                 # 光学参数
                 lumens=1000.0,
                 source_type="led",
                 color_temp=4000,
                 cri=80,

                 # 物理尺寸（米）
                 width=0.15,
                 length=0.15,
                 height=0.10,

                 # 配光特性
                 beam_angle=None,      # 光束角（度）
                 field_angle=None,     # 截止角（度）
                 photometric_type=1,   # 1=C平面, 2=B平面, 3=A平面

                 # 可选：电功率（如果提供，可用于验证）
                 electrical_watts=None):

        self.name = name
        self.manufacturer = manufacturer
        self.catalog_number = catalog_number
        self.description = description

        self.lumens = lumens
        self.source_type = source_type
        self.color_temp = color_temp
        self.cri = cri

        self.width = width
        self.length = length
        self.height = height

        self.beam_angle = beam_angle
        self.field_angle = field_angle
        self.photometric_type = photometric_type

        self.electrical_watts = electrical_watts

    def get_max_dimension(self):
        """获取灯具最大尺寸"""
        return max(self.width, self.length, self.height)

    def __str__(self):
        """字符串表示"""
        return (f"灯具: {self.name}\n"
                f"制造商: {self.manufacturer}\n"
                f"流明: {self.lumens} lm\n"
                f"光源: {self.source_type}\n"
                f"色温: {self.color_temp} K\n"
                f"尺寸: {self.width:.3f}×{self.length:.3f}×{self.height:.3f} m")


class EXRToIESConverter:
    """EXR到IES转换器主类"""

    def __init__(self,
                 resolution='high',
                 auto_calculate_distance=True,
                 measurement_distance=None,
                 sphere_density='standard',
                 cycles_samples=256):
        """
        初始化转换器

        Args:
            resolution: EXR分辨率 ('low', 'medium', 'high', 'ultra')
            auto_calculate_distance: 是否自动计算测量距离
            measurement_distance: 手动指定测量距离（米）
            sphere_density: 球体网格密度 ('preview', 'standard', 'fine')
            cycles_samples: Cycles采样数
        """
        # EXR分辨率配置
        self.resolutions = {
            'low': (1024, 512),
            'medium': (2048, 1024),
            'high': (4096, 2048),
            'ultra': (8192, 4096),
        }
        self.resolution = resolution

        # 球体网格密度配置
        self.sphere_densities = {
            'preview': {'segments': 36, 'rings': 18},   # 快速预览
            'standard': {'segments': 72, 'rings': 36},  # 标准（推荐）
            'fine': {'segments': 144, 'rings': 72},     # 精细
        }
        self.sphere_density = sphere_density

        # 测量距离配置
        self.auto_calculate_distance = auto_calculate_distance
        self.measurement_distance = measurement_distance

        # Cycles配置
        self.cycles_samples = cycles_samples

        # IES分辨率配置
        self.ies_resolutions = {
            'coarse': (36, 18),    # 10° 步长
            'standard': (72, 36),   # 5° 步长
            'fine': (144, 72),      # 2.5° 步长
            'ultra': (360, 180),    # 1° 步长
        }

        # 辐射瓦特转换器
        if LampSpecsToRadiantConverter:
            self.lamp_converter = LampSpecsToRadiantConverter()
        else:
            self.lamp_converter = None

    def calculate_luminaire_bounding_sphere(self, luminaire_object):
        """
        计算灯具的最小外接球

        Args:
            luminaire_object: 灯具对象（包含所有子对象）

        Returns:
            center: 外接球中心（世界坐标）
            radius: 外接球半径（米）
        """
        # 收集所有相关对象
        objects = [luminaire_object]
        if luminaire_object.children:
            objects.extend(luminaire_object.children_recursive)

        # 收集所有顶点的世界坐标
        all_vertices = []
        for obj in objects:
            if obj.type == 'MESH':
                for vertex in obj.data.vertices:
                    world_pos = obj.matrix_world @ vertex.co
                    all_vertices.append(world_pos)
            elif obj.type == 'LIGHT':
                # 灯光对象使用其位置
                all_vertices.append(obj.matrix_world.translation)

        if not all_vertices:
            # 如果没有网格，使用对象的包围盒
            bbox = [luminaire_object.matrix_world @ Vector(corner)
                    for corner in luminaire_object.bound_box]
            all_vertices = bbox

        # 转换为numpy数组
        vertices_array = np.array([[v.x, v.y, v.z] for v in all_vertices])

        # 计算中心（所有顶点的平均）
        center = vertices_array.mean(axis=0)
        center_vector = Vector(center)

        # 计算半径（最远顶点的距离）
        distances = np.linalg.norm(vertices_array - center, axis=1)
        radius = distances.max()

        return center_vector, radius

    def calculate_measurement_distance(self, luminaire_object, luminaire_params=None):
        """
        计算IES测量的最佳距离

        Args:
            luminaire_object: 灯具对象
            luminaire_params: 灯具参数对象（可选）

        Returns:
            distance: 推荐测量距离（米）
            info: 计算信息字典
        """
        # 计算灯具外接球
        center, radius = self.calculate_luminaire_bounding_sphere(luminaire_object)

        # 基于尺寸的推荐距离（IES标准：5倍直径）
        size_based_distance = radius * 2.0 * 5.0

        # 应用约束
        min_absolute = 1.0   # 最小1米
        max_absolute = 20.0  # 最大20米（实验室限制）

        distance = max(min_absolute, size_based_distance)
        distance = min(max_absolute, distance)

        # 验证远场条件
        angle_error_deg = np.degrees(np.arctan(radius / distance))

        # 编译信息
        info = {
            'luminaire_center': center,
            'luminaire_radius': radius,
            'luminaire_diameter': radius * 2.0,
            'size_based_distance': size_based_distance,
            'final_distance': distance,
            'distance_to_radius_ratio': distance / (radius * 2.0),
            'angle_error_deg': angle_error_deg,
            'meets_far_field': angle_error_deg < 10.0,
            'meets_ies_standard': distance >= radius * 2.0 * 5.0,
        }

        # 检查是否受限制
        if size_based_distance < min_absolute:
            info['limited_by'] = 'minimum'
        elif size_based_distance > max_absolute:
            info['limited_by'] = 'maximum'
            info['warning'] = f"灯具尺寸过大，测量距离受实验室限制在{max_absolute}m"
        else:
            info['limited_by'] = 'size'

        # 如果提供了灯具参数，检查光束角
        if luminaire_params and luminaire_params.beam_angle:
            if luminaire_params.beam_angle < 10:
                info['recommendation'] = "极窄光束，建议使用更高的网格密度（144×72）"

        return distance, info

    def setup_measurement_distance(self, luminaire_object, luminaire_params=None):
        """设置或计算测量距离"""
        if self.measurement_distance is not None:
            # 手动指定的距离，验证是否合理
            distance, info = self.calculate_measurement_distance(luminaire_object, luminaire_params)

            recommended = info['final_distance']

            if self.measurement_distance < recommended * 0.5:
                print(f"⚠️  警告：手动指定的距离 {self.measurement_distance:.2f}m "
                      f"小于推荐值 {recommended:.2f}m")
                print(f"   可能不满足远场条件，结果可能不准确")

            return self.measurement_distance

        elif self.auto_calculate_distance:
            # 自动计算
            distance, info = self.calculate_measurement_distance(luminaire_object, luminaire_params)

            self.measurement_distance = distance

            # 打印详细报告
            print("\n" + "="*70)
            print("  📏 自动计算测量距离")
            print("="*70)
            print(f"灯具外接球半径:  {info['luminaire_radius']:.3f} m")
            print(f"灯具最大直径:    {info['luminaire_diameter']:.3f} m")
            print(f"推荐测量距离:    {distance:.3f} m")
            print(f"距离/直径比:     {info['distance_to_radius_ratio']:.1f}:1")
            print(f"角度误差:        {info['angle_error_deg']:.2f}°")
            print(f"满足远场条件:    {'✅ 是' if info['meets_far_field'] else '❌ 否'}")
            print(f"符合IES标准:     {'✅ 是' if info['meets_ies_standard'] else '⚠️  接近'}")

            if 'warning' in info:
                print(f"⚠️  警告: {info['warning']}")
            if 'recommendation' in info:
                print(f"💡 建议: {info['recommendation']}")

            print("="*70 + "\n")

            return distance

        else:
            raise ValueError("必须指定measurement_distance或启用auto_calculate_distance")

    def calculate_radiant_watts(self, luminaire_params):
        """
        计算辐射瓦数

        Args:
            luminaire_params: 灯具参数对象

        Returns:
            radiant_watts: 辐射瓦特值
            method: 计算方法描述
        """
        if self.lamp_converter is None:
            # 简化计算：假设LED光效为100 lm/W
            radiant_watts = luminaire_params.lumens / 100.0
            method = "简化计算（假设100 lm/W）"
        else:
            radiant_watts, method = self.lamp_converter.calculate_radiant_watts(
                lumens=luminaire_params.lumens,
                source_type=luminaire_params.source_type,
                color_temp=luminaire_params.color_temp
            )

        print(f"\n💡 灯光参数计算")
        print(f"{'='*70}")
        print(f"流明值:         {luminaire_params.lumens} lm")
        print(f"光源类型:       {luminaire_params.source_type}")
        print(f"色温:           {luminaire_params.color_temp} K")
        print(f"辐射瓦数:       {radiant_watts:.3f} W")
        print(f"计算方法:       {method}")
        print(f"{'='*70}\n")

        return radiant_watts, method

    def setup_scene(self):
        """设置Blender场景用于烘焙"""
        scene = bpy.context.scene

        print("🔧 设置Blender场景...")

        # 渲染引擎设置
        scene.render.engine = 'CYCLES'

        # 单位设置
        scene.unit_settings.system = 'METRIC'
        scene.unit_settings.length_unit = 'METERS'
        scene.unit_settings.scale_length = 1.0

        # Cycles设置
        scene.cycles.samples = self.cycles_samples
        scene.cycles.use_denoising = False  # 保持原始数据
        scene.cycles.max_bounces = 4
        scene.cycles.diffuse_bounces = 2
        scene.cycles.glossy_bounces = 2
        scene.cycles.transmission_bounces = 2

        # 尝试使用GPU
        try:
            scene.cycles.device = 'GPU'
            print("  ✅ 已启用GPU加速")
        except:
            print("  ⚠️  GPU不可用，使用CPU")

        # 色彩管理（关键！）
        scene.view_settings.view_transform = 'Raw'
        scene.view_settings.look = 'None'
        scene.sequencer_colorspace_settings.name = 'Linear'

        # EXR输出设置
        scene.render.image_settings.file_format = 'OPEN_EXR'
        scene.render.image_settings.color_depth = '32'
        scene.render.image_settings.exr_codec = 'ZIP'

        # 分辨率
        width, height = self.resolutions[self.resolution]
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.resolution_percentage = 100

        print(f"  ✅ 场景设置完成: {width}x{height}, {self.cycles_samples} samples")

    def create_measurement_sphere(self, luminaire_object, luminaire_params=None):
        """
        创建测量球体

        Args:
            luminaire_object: 灯具对象
            luminaire_params: 灯具参数对象（可选）

        Returns:
            sphere: 球体对象
        """
        # 设置测量距离
        distance = self.setup_measurement_distance(luminaire_object, luminaire_params)

        # 确定球心位置
        center_vec, _ = self.calculate_luminaire_bounding_sphere(luminaire_object)
        center = (center_vec.x, center_vec.y, center_vec.z)

        # 获取球体网格密度
        density = self.sphere_densities[self.sphere_density]
        segments = density['segments']
        rings = density['rings']

        print(f"🌐 创建测量球体...")
        print(f"  中心: ({center[0]:.3f}, {center[1]:.3f}, {center[2]:.3f}) m")
        print(f"  半径: {distance:.3f} m")
        print(f"  网格: {segments}×{rings} ({segments * (rings-2) + segments*2} 面)")

        # 创建UV球体
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=segments,
            ring_count=rings,
            radius=distance,
            location=center
        )

        sphere = bpy.context.active_object
        sphere.name = "IES_Measurement_Sphere"

        # 翻转法线（使内表面朝向灯具）
        bpy.context.view_layer.objects.active = sphere
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.flip_normals()
        bpy.ops.object.mode_set(mode='OBJECT')

        print(f"  ✅ 测量球体创建完成")

        return sphere

    def setup_measurement_material(self, sphere_object):
        """
        为测量球体设置材质

        Args:
            sphere_object: 球体对象

        Returns:
            material: 材质对象
            image: 烘焙用图像
        """
        print("🎨 设置测量材质...")

        # 创建材质
        mat = bpy.data.materials.new(name="IES_Measurement_Material")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # 漫反射节点（纯白色）
        diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
        diffuse.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
        diffuse.inputs['Roughness'].default_value = 1.0
        diffuse.location = (0, 0)

        # 创建烘焙图像
        width, height = self.resolutions[self.resolution]
        image = bpy.data.images.new(
            name="IES_Bake_Image",
            width=width,
            height=height,
            alpha=False,
            float_buffer=True  # 32位浮点
        )

        # 图像纹理节点
        image_node = nodes.new(type='ShaderNodeTexImage')
        image_node.image = image
        image_node.location = (-300, 0)

        # 输出节点
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (300, 0)

        # 连接
        links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])

        # 应用材质
        if sphere_object.data.materials:
            sphere_object.data.materials[0] = mat
        else:
            sphere_object.data.materials.append(mat)

        # 选中图像节点（烘焙目标）
        nodes.active = image_node

        print(f"  ✅ 测量材质设置完成")

        return mat, image

    def set_light_power(self, luminaire_object, radiant_watts):
        """
        设置灯具的光源功率

        Args:
            luminaire_object: 灯具对象
            radiant_watts: 辐射瓦特值

        Returns:
            light_objects: 设置的灯光对象列表
        """
        # 查找灯具中的所有灯光对象
        light_objects = []

        # 检查自身
        if luminaire_object.type == 'LIGHT':
            light_objects.append(luminaire_object)

        # 检查子对象
        for child in luminaire_object.children_recursive:
            if child.type == 'LIGHT':
                light_objects.append(child)

        if not light_objects:
            print("  ⚠️  警告：未在灯具中找到灯光对象")
            return []

        # 设置功率
        for light_obj in light_objects:
            light_obj.data.energy = radiant_watts
            print(f"  ✅ 已设置灯光 '{light_obj.name}' 强度: {radiant_watts:.3f} W")

        return light_objects

    def bake_light_distribution(self, sphere_object, output_exr_path):
        """
        烘焙光照分布到EXR

        Args:
            sphere_object: 测量球体对象
            output_exr_path: 输出EXR路径
        """
        scene = bpy.context.scene

        # 确保球体被选中和激活
        bpy.ops.object.select_all(action='DESELECT')
        sphere_object.select_set(True)
        bpy.context.view_layer.objects.active = sphere_object

        # 烘焙设置
        scene.cycles.bake_type = 'COMBINED'
        scene.render.bake.use_pass_direct = True
        scene.render.bake.use_pass_indirect = False
        scene.render.bake.use_pass_color = False
        scene.render.bake.use_pass_emit = False
        scene.render.bake.margin = 0

        print(f"\n🔥 开始烘焙光照分布...")
        print(f"  采样数: {self.cycles_samples}")
        print(f"  分辨率: {self.resolutions[self.resolution][0]}x{self.resolutions[self.resolution][1]}")
        print(f"  预计时间: 3-5分钟（取决于硬件）")
        print(f"  请稍候...\n")

        # 执行烘焙
        bpy.ops.object.bake(type='COMBINED')

        # 保存图像
        image = bpy.data.images.get("IES_Bake_Image")
        if image:
            output_path = Path(output_exr_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            image.filepath_raw = str(output_path)
            image.file_format = 'OPEN_EXR'
            image.save()
            print(f"✅ EXR已保存: {output_path}")

            # 显示文件大小
            file_size = output_path.stat().st_size / (1024 * 1024)
            print(f"   文件大小: {file_size:.1f} MB")
        else:
            raise RuntimeError("烘焙图像未找到")

    def read_exr_data(self, exr_path):
        """
        读取EXR文件

        Args:
            exr_path: EXR文件路径

        Returns:
            data: numpy数组 [height, width, 3] (RGB)
        """
        print(f"\n📖 读取EXR文件: {exr_path}")

        # 使用Blender加载EXR
        image = bpy.data.images.load(str(exr_path))

        width = image.size[0]
        height = image.size[1]

        # 获取像素数据
        pixels = np.array(image.pixels[:])

        # 重塑为 [height, width, 4] (RGBA)
        pixels = pixels.reshape((height, width, 4))

        # 只取RGB通道
        rgb = pixels[:, :, :3]

        # 翻转Y轴（Blender图像坐标系）
        rgb = np.flipud(rgb)

        print(f"  ✅ EXR读取完成: {width}x{height}")
        print(f"  值域: [{rgb.min():.6f}, {rgb.max():.6f}] W/m²")

        # 卸载图像
        bpy.data.images.remove(image)

        return rgb

    def uv_to_spherical(self, u, v):
        """UV坐标转球坐标"""
        theta = v * 180.0  # 垂直角 0-180°
        phi = u * 360.0    # 水平角 0-360°
        return theta, phi

    def spherical_to_uv(self, theta, phi):
        """球坐标转UV坐标"""
        u = phi / 360.0
        v = theta / 180.0
        return u, v

    def sample_exr_at_angles(self, exr_data, theta, phi, interpolation='bilinear'):
        """
        在指定球坐标角度采样EXR数据

        Args:
            exr_data: EXR数据数组 [height, width, 3]
            theta: 垂直角（度）
            phi: 水平角（度）
            interpolation: 插值方法 ('nearest', 'bilinear')

        Returns:
            value: 采样值（辐照度，W/m²）
        """
        # 转换为UV坐标
        u, v = self.spherical_to_uv(theta, phi)

        # 转换为像素坐标
        height, width = exr_data.shape[:2]

        if interpolation == 'nearest':
            x = int(round(u * (width - 1)))
            y = int(round(v * (height - 1)))

            # 边界检查
            x = np.clip(x, 0, width - 1)
            y = np.clip(y, 0, height - 1)

            # 采样RGB并转换为辐照度
            rgb = exr_data[y, x, :]

        else:  # bilinear
            x_float = u * (width - 1)
            y_float = v * (height - 1)

            x0 = int(np.floor(x_float))
            x1 = min(x0 + 1, width - 1)
            y0 = int(np.floor(y_float))
            y1 = min(y0 + 1, height - 1)

            # 插值权重
            wx = x_float - x0
            wy = y_float - y0

            # 双线性插值
            rgb = ((1 - wx) * (1 - wy) * exr_data[y0, x0, :] +
                   wx * (1 - wy) * exr_data[y0, x1, :] +
                   (1 - wx) * wy * exr_data[y1, x0, :] +
                   wx * wy * exr_data[y1, x1, :])

        # 转换为辐照度（光度学加权平均）
        # 使用CIE 1931标准：R=0.2126, G=0.7152, B=0.0722
        irradiance = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

        return irradiance

    def irradiance_to_candela_per_klm(self, irradiance, lumens):
        """
        辐照度转换为坎德拉每千流明

        Args:
            irradiance: 辐照度 (W/m²)
            lumens: 总流明值

        Returns:
            cd_per_klm: 坎德拉每千流明 (cd/klm)
        """
        # 辐照度转发光强度（考虑距离平方反比）
        intensity = irradiance * (self.measurement_distance ** 2)

        # 转换为cd/klm
        cd_per_klm = (intensity / lumens) * 1000.0

        return cd_per_klm

    def generate_ies_angles(self, ies_resolution='standard'):
        """
        生成IES采样角度

        Args:
            ies_resolution: IES分辨率

        Returns:
            horizontal_angles: 水平角列表
            vertical_angles: 垂直角列表
        """
        n_phi, n_theta = self.ies_resolutions[ies_resolution]

        horizontal_angles = np.linspace(0, 360, n_phi)
        vertical_angles = np.linspace(0, 180, n_theta)

        return horizontal_angles, vertical_angles

    def convert_exr_to_ies_data(self, exr_data, lumens, ies_resolution='standard'):
        """
        从EXR数据转换为IES光强数据

        Args:
            exr_data: EXR数据数组
            lumens: 总流明值
            ies_resolution: IES分辨率

        Returns:
            candela_values: 光强矩阵 [n_phi, n_theta] (cd/klm)
            h_angles: 水平角列表
            v_angles: 垂直角列表
        """
        print(f"\n🔄 开始EXR到IES数据转换...")

        # 生成采样角度
        h_angles, v_angles = self.generate_ies_angles(ies_resolution)
        n_phi = len(h_angles)
        n_theta = len(v_angles)

        print(f"  IES分辨率: {n_phi} × {n_theta} ({ies_resolution})")
        print(f"  采样点总数: {n_phi * n_theta}")

        # 采样并转换
        candela_values = np.zeros((n_phi, n_theta))

        for i, phi in enumerate(h_angles):
            for j, theta in enumerate(v_angles):
                irradiance = self.sample_exr_at_angles(exr_data, theta, phi)
                cd_per_klm = self.irradiance_to_candela_per_klm(irradiance, lumens)
                candela_values[i, j] = cd_per_klm

        print(f"  ✅ 采样完成")
        print(f"  坎德拉值域: [{candela_values.min():.2f}, {candela_values.max():.2f}] cd/klm")

        return candela_values, h_angles, v_angles

    def write_ies_file(self, output_path, luminaire_params, candela_values,
                      horizontal_angles, vertical_angles):
        """
        写入IES文件

        Args:
            output_path: 输出路径
            luminaire_params: 灯具参数对象
            candela_values: 光强矩阵 [n_phi, n_theta]
            horizontal_angles: 水平角列表
            vertical_angles: 垂直角列表
        """
        n_horizontal = len(horizontal_angles)
        n_vertical = len(vertical_angles)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            # 文件头
            f.write("IESNA:LM-63-2002\n")
            f.write(f"[MANUFAC] {luminaire_params.manufacturer}\n")
            f.write(f"[LUMCAT] {luminaire_params.catalog_number or 'Generated_from_EXR'}\n")
            f.write(f"[LUMINAIRE] {luminaire_params.description or luminaire_params.name}\n")
            f.write(f"[LAMPCAT] {luminaire_params.source_type.upper()}\n")
            f.write(f"[LAMP] {luminaire_params.lumens:.0f}lm {luminaire_params.color_temp}K CRI{luminaire_params.cri}\n")
            f.write(f"[ISSUEDATE] {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"[BALLASTCAT] Electronic\n")
            f.write(f"[OTHER] Generated by EXR to IES Converter\n")
            f.write("TILT=NONE\n")

            # 光度数据行（10个值）
            f.write(f"1 {luminaire_params.lumens:.1f} 1.0 {n_horizontal} {n_vertical} "
                   f"{luminaire_params.photometric_type} 2 "
                   f"{luminaire_params.width:.3f} {luminaire_params.length:.3f} {luminaire_params.height:.3f}\n")

            # 水平角列表
            for angle in horizontal_angles:
                f.write(f"{angle:.1f} ")
            f.write("\n")

            # 垂直角列表
            for angle in vertical_angles:
                f.write(f"{angle:.1f} ")
            f.write("\n")

            # 光强数据（按φ优先，每行10个数值）
            count = 0
            for phi_idx in range(n_horizontal):
                for theta_idx in range(n_vertical):
                    cd_value = candela_values[phi_idx, theta_idx]
                    f.write(f"{cd_value:.2f} ")
                    count += 1
                    if count % 10 == 0:
                        f.write("\n")

            # 确保最后有换行
            if count % 10 != 0:
                f.write("\n")

        print(f"\n✅ IES文件已生成: {output_path}")

        # 显示文件信息
        file_size = output_path.stat().st_size / 1024
        print(f"   文件大小: {file_size:.1f} KB")
        print(f"   流明值: {luminaire_params.lumens:.0f} lm")
        print(f"   分辨率: {n_horizontal}×{n_vertical}")

    def process_full_workflow(self,
                             luminaire_object,
                             luminaire_params,
                             output_exr_path,
                             output_ies_path,
                             ies_resolution='standard'):
        """
        完整处理流程：从灯具到IES

        Args:
            luminaire_object: Blender灯具对象
            luminaire_params: 灯具参数对象（LuminaireParameters）
            output_exr_path: EXR输出路径
            output_ies_path: IES输出路径
            ies_resolution: IES分辨率
        """
        print("\n" + "="*70)
        print("  🚀 EXR to IES 完整转换流程")
        print("="*70)
        print(f"\n{luminaire_params}\n")

        try:
            # 1. 计算辐射瓦数
            radiant_watts, method = self.calculate_radiant_watts(luminaire_params)

            # 2. 设置场景
            self.setup_scene()

            # 3. 设置灯光功率
            self.set_light_power(luminaire_object, radiant_watts)

            # 4. 创建测量球体
            sphere = self.create_measurement_sphere(luminaire_object, luminaire_params)

            # 5. 设置材质
            mat, image = self.setup_measurement_material(sphere)

            # 6. 烘焙
            self.bake_light_distribution(sphere, output_exr_path)

            # 7. 读取EXR
            exr_data = self.read_exr_data(output_exr_path)

            # 8. 转换为IES数据
            candela_values, h_angles, v_angles = self.convert_exr_to_ies_data(
                exr_data, luminaire_params.lumens, ies_resolution
            )

            # 9. 写入IES文件
            self.write_ies_file(
                output_ies_path,
                luminaire_params,
                candela_values,
                h_angles,
                v_angles
            )

            print("\n" + "="*70)
            print("  ✅ 转换完成！")
            print("="*70)
            print(f"\n输出文件：")
            print(f"  EXR: {output_exr_path}")
            print(f"  IES: {output_ies_path}")
            print()

            return True

        except Exception as e:
            print(f"\n❌ 转换过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("EXR to IES Converter")
    print("请在Blender中作为模块导入使用")
    print("\n使用示例：")
    print("  from exr_to_ies_converter import EXRToIESConverter, LuminaireParameters")
    print("  converter = EXRToIESConverter()")
    print("  params = LuminaireParameters(lumens=1000, ...)")
    print("  converter.process_full_workflow(light_object, params, 'out.exr', 'out.ies')")
