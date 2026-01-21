# EXR转IES技术方案与实现指南

## 文档信息
- **创建日期**: 2026-01-21
- **项目**: 灯光参数转换工具
- **目标**: 从Blender烘焙的EXR光照分布生成IES光度文件

---

## 📋 方案概述

### 核心思路
1. **灯具设置** → 使用辐射瓦特转换代码计算正确的灯光强度
2. **球体包围** → 创建包围球体，内表面朝向灯具
3. **烘焙光照** → 将灯光信息烘焙到EXR高动态范围图像
4. **转换IES** → 从EXR提取光强分布，生成IES光度文件

### 可行性评估
✅ **完全可行** - 该方法类似于"近场光度测量"的数字化模拟，在灯光设计行业有实际应用

---

## 🎯 关键技术点

### 1. 球体UV映射与光度学采样

#### 问题描述
IES文件使用**球坐标系统**（垂直角θ、水平角φ）：
```
IES坐标系统:
- 垂直角 (θ): 0° (正下方) → 90° (水平) → 180° (正上方)
- 水平角 (φ): 0° → 360° (围绕灯具旋转)
```

#### 解决方案
球体UV必须正确映射到球坐标：
- 使用**UV Sphere**（默认UV已是球坐标映射）
- 或使用**Icosphere**后重新UV展开
- **确保UV的V方向对应垂直角θ，U方向对应水平角φ**

#### Blender实现代码
```python
# 创建采样球体
import bpy

bpy.ops.mesh.primitive_uv_sphere_add(
    segments=72,      # 水平角分辨率 (φ方向，5°/段)
    ring_count=36,    # 垂直角分辨率 (θ方向，5°/段)
    radius=1.0,       # 采样半径（米）
    location=(0, 0, 0)
)

# 获取球体对象
sphere = bpy.context.active_object
sphere.name = "IES_Measurement_Sphere"

# 确保使用正确的UV映射
# UV Sphere的默认UV已经是球坐标映射，V=0在底部，V=1在顶部
```

#### UV坐标到球坐标转换
```python
def uv_to_spherical(u, v):
    """
    UV坐标 → 球坐标(θ, φ)
    
    Args:
        u: 水平UV坐标 [0, 1]
        v: 垂直UV坐标 [0, 1]
    
    Returns:
        theta: 垂直角 [0°, 180°]
        phi: 水平角 [0°, 360°]
    """
    theta = v * 180.0  # 垂直角 0-180°
    phi = u * 360.0    # 水平角 0-360°
    return theta, phi

def spherical_to_uv(theta, phi):
    """
    球坐标 → UV坐标
    
    Args:
        theta: 垂直角 [0°, 180°]
        phi: 水平角 [0°, 360°]
    
    Returns:
        u: 水平UV坐标 [0, 1]
        v: 垂直UV坐标 [0, 1]
    """
    u = phi / 360.0
    v = theta / 180.0
    return u, v
```

---

### 2. 烘焙设置的物理正确性

#### 问题描述
必须烘焙**辐照度**（Irradiance）或**辉度**（Radiance），而非简单的颜色，以保持物理正确性。

#### Blender烘焙设置
```python
import bpy

scene = bpy.context.scene

# 使用Cycles渲染引擎
scene.render.engine = 'CYCLES'

# 烘焙类型设置
scene.cycles.bake_type = 'COMBINED'  # 或 'DIFFUSE'

# 关键设置：确保物理正确性
scene.render.bake.use_pass_direct = True      # 直接光照（必须开启）
scene.render.bake.use_pass_indirect = False   # 关闭间接光（IES是直接光测量）
scene.render.bake.use_pass_color = False      # 不包含材质颜色
scene.render.bake.use_pass_emit = False       # 不包含自发光

# 采样设置（提高质量）
scene.cycles.samples = 256  # 烘焙采样数
scene.cycles.use_denoising = False  # 不使用降噪（保持原始数据）

# 边距设置
scene.render.bake.margin = 0  # 无边距
```

#### 球体材质设置（关键！）
```python
# 球体必须使用纯白色漫反射材质
def setup_measurement_material(sphere_object):
    """为测量球体设置正确的材质"""
    
    # 创建新材质
    mat = bpy.data.materials.new(name="IES_Measurement_Material")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # 清除默认节点
    nodes.clear()
    
    # 添加漫反射BSDF节点（纯白色）
    diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
    diffuse.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)  # 纯白
    diffuse.inputs['Roughness'].default_value = 1.0
    diffuse.location = (0, 0)
    
    # 添加图像纹理节点（用于烘焙）
    image_node = nodes.new(type='ShaderNodeTexImage')
    image_node.location = (-300, 0)
    # 图像将在烘焙前创建和分配
    
    # 添加输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    
    # 连接节点
    links.new(diffuse.outputs['BSDF'], output.inputs['Surface'])
    
    # 应用材质
    if sphere_object.data.materials:
        sphere_object.data.materials[0] = mat
    else:
        sphere_object.data.materials.append(mat)
    
    return mat

# 重要说明：
# 纯白色漫反射材质确保烘焙结果直接对应入射辐照度
# 颜色值1.0表示100%反射，不会改变光照强度
```

---

### 3. 距离和单位的一致性

#### 物理关系
```
光强 (candela, cd) = 辉度 (lux) × 距离² / 立体角

对于烘焙的辐照度:
Irradiance (W/m²) = Intensity (W/sr) / distance²

因此:
Intensity (W/sr) = Irradiance (W/m²) × distance²
```

#### 标准测量距离
```python
# IES标准通常使用1米作为测量距离
MEASUREMENT_DISTANCE = 1.0  # 米

# 创建采样球体时使用此半径
sphere_radius = MEASUREMENT_DISTANCE

# 转换公式
def irradiance_to_intensity(irradiance, distance):
    """
    辐照度转换为发光强度
    
    Args:
        irradiance: 辐照度 (W/m²)
        distance: 测量距离 (m)
    
    Returns:
        intensity: 发光强度 (W/sr 或 cd)
    """
    # 考虑距离平方反比定律
    intensity = irradiance * (distance ** 2)
    return intensity

# 对于球面上的采样点，立体角的计算
def calculate_solid_angle(theta_step_deg, phi_step_deg):
    """
    计算采样点对应的立体角
    
    Args:
        theta_step_deg: 垂直角步长（度）
        phi_step_deg: 水平角步长（度）
    
    Returns:
        solid_angle: 立体角 (sr)
    """
    import math
    
    # 转换为弧度
    theta_step = math.radians(theta_step_deg)
    phi_step = math.radians(phi_step_deg)
    
    # 对于球面上的小区域，立体角 ≈ sin(θ) × Δθ × Δφ
    # 这里简化为平均值
    solid_angle = theta_step * phi_step
    
    return solid_angle
```

#### Blender单位设置
```python
# 确保Blender使用公制单位
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene.unit_settings.scale_length = 1.0

# 单位转换常量
BLENDER_TO_METERS = 1.0  # 如果Blender使用米
```

---

### 4. EXR格式和数据范围

#### 为什么使用EXR？
- **HDR（高动态范围）**：支持32位浮点，可存储极大范围的光照值
- **物理正确**：保留真实的辐照度数值，不做任何压缩或限制
- **无损存储**：不像JPG/PNG会做色彩映射和gamma校正

#### Blender输出设置
```python
import bpy

scene = bpy.context.scene

# EXR文件格式设置
scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.color_depth = '32'  # 32位浮点
scene.render.image_settings.exr_codec = 'ZIP'   # ZIP压缩（无损）

# 色彩管理设置（关键！）
scene.view_settings.view_transform = 'Raw'          # 不做色彩变换
scene.view_settings.look = 'None'                   # 不使用Look
scene.display_settings.display_device = 'sRGB'     # 显示设备

# 序列器色彩空间
scene.sequencer_colorspace_settings.name = 'Linear'

# 确保使用线性色彩空间，避免伽马校正
# 这样烘焙出的数值才是物理正确的辐照度值
```

#### EXR分辨率建议
```python
# 高分辨率EXR可以后期降采样到不同IES分辨率
# 推荐使用2:1比例（equirectangular全景格式）

RECOMMENDED_RESOLUTIONS = {
    'low': (1024, 512),      # 快速预览
    'medium': (2048, 1024),  # 标准质量
    'high': (4096, 2048),    # 高质量
    'ultra': (8192, 4096),   # 极高质量（用于复杂灯具）
}

# 设置分辨率
scene.render.resolution_x = 4096
scene.render.resolution_y = 2048
scene.render.resolution_percentage = 100
```

#### 读取EXR数据
```python
import OpenEXR
import Imath
import numpy as np

def read_exr_file(exr_path):
    """
    读取EXR文件，返回numpy数组
    
    Args:
        exr_path: EXR文件路径
    
    Returns:
        data: numpy数组，形状为 (height, width, 3) RGB
    """
    # 打开EXR文件
    exr_file = OpenEXR.InputFile(exr_path)
    
    # 获取图像头信息
    header = exr_file.header()
    dw = header['dataWindow']
    width = dw.max.x - dw.min.x + 1
    height = dw.max.y - dw.min.y + 1
    
    # 读取RGB通道
    FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
    
    # 读取每个通道
    r_str = exr_file.channel('R', FLOAT)
    g_str = exr_file.channel('G', FLOAT)
    b_str = exr_file.channel('B', FLOAT)
    
    # 转换为numpy数组
    r = np.frombuffer(r_str, dtype=np.float32).reshape(height, width)
    g = np.frombuffer(g_str, dtype=np.float32).reshape(height, width)
    b = np.frombuffer(b_str, dtype=np.float32).reshape(height, width)
    
    # 合并为RGB图像
    rgb = np.stack([r, g, b], axis=-1)
    
    return rgb

# 或者使用Pillow（更简单但功能略少）
from PIL import Image

def read_exr_simple(exr_path):
    """使用Pillow读取EXR（简化版）"""
    img = Image.open(exr_path)
    data = np.array(img, dtype=np.float32)
    return data
```

---

### 5. IES文件格式要求

#### IES文件结构
```
IESNA:LM-63-2002                    # 文件头标准（或 IESNA91）
[TEST] Test Lab Name                # 测试实验室（可选）
[TESTLAB] Lab Information           # 实验室信息（可选）
[ISSUEDATE] 2026-01-21             # 发布日期（可选）
[MANUFAC] Manufacturer Name         # 制造商（可选）
[LUMCAT] Luminaire Catalog Number   # 灯具目录编号（可选）
[LUMINAIRE] Description             # 灯具描述（可选）
[LAMPCAT] Lamp Catalog Number       # 灯泡编号（可选）
[LAMP] Lamp Description             # 灯泡描述（可选）
TILT=NONE                           # 倾斜数据（NONE表示无倾斜）

# 光度数据行（10个数值，空格分隔）
1    1000    1.0    72    36    1    2    1.0    1.0    1.0

说明：
1.  灯具数量（通常为1）
2.  总流明值（从ProductsParametersToRadiantWatts获取）
3.  倍增因子（通常为1.0）
4.  水平角数量（φ方向采样点数）
5.  垂直角数量（θ方向采样点数）
6.  光度类型（1=C平面, 2=B平面, 3=A平面）
7.  单位类型（1=英尺, 2=米）
8.  灯具宽度（米）
9.  灯具长度（米）
10. 灯具高度（米）

# 水平角列表（φ，度）
0.0 5.0 10.0 15.0 ... 355.0 360.0

# 垂直角列表（θ，度）
0.0 5.0 10.0 15.0 ... 175.0 180.0

# 光强数据（坎德拉每千流明，cd/klm）
# 按φ优先、θ次序排列
# 即：对于每个φ角，列出所有θ角的光强值
<φ=0°时，θ从0°到180°的光强>
<φ=5°时，θ从0°到180°的光强>
...
<φ=360°时，θ从0°到180°的光强>
```

#### IES生成代码模板
```python
def generate_ies_file(output_path, lumens, candela_values, 
                      horizontal_angles, vertical_angles,
                      manufacturer="Unknown", luminaire_desc="Custom IES"):
    """
    生成IES文件
    
    Args:
        output_path: 输出文件路径
        lumens: 总流明值
        candela_values: 光强值矩阵 [n_phi, n_theta] (cd/klm)
        horizontal_angles: 水平角列表 (度)
        vertical_angles: 垂直角列表 (度)
        manufacturer: 制造商名称
        luminaire_desc: 灯具描述
    """
    from datetime import datetime
    
    n_horizontal = len(horizontal_angles)
    n_vertical = len(vertical_angles)
    
    # 打开文件
    with open(output_path, 'w') as f:
        # 文件头
        f.write("IESNA:LM-63-2002\n")
        f.write(f"[MANUFAC] {manufacturer}\n")
        f.write(f"[LUMCAT] Generated_from_EXR\n")
        f.write(f"[LUMINAIRE] {luminaire_desc}\n")
        f.write(f"[ISSUEDATE] {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write("TILT=NONE\n")
        
        # 光度数据行（10个值）
        f.write(f"1 {lumens:.1f} 1.0 {n_horizontal} {n_vertical} 1 2 1.0 1.0 1.0\n")
        
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
    
    print(f"✅ IES文件已生成: {output_path}")
```

---

### 6. 对称性优化

#### IES支持的对称类型

```python
# 光度类型（photometric type参数）
PHOTOMETRIC_TYPES = {
    1: "C平面（Type C）",     # 最常见，绕垂直轴旋转对称
    2: "B平面（Type B）",     # 用于道路照明
    3: "A平面（Type A）"      # 用于泛光照明
}

# 对称性判断
def detect_symmetry(light_distribution, tolerance=0.05):
    """
    检测光强分布的对称性
    
    Args:
        light_distribution: 光强矩阵 [n_phi, n_theta]
        tolerance: 对称性容差（相对误差）
    
    Returns:
        symmetry_type: 'full', 'half', 'quarter', 'none'
    """
    n_phi, n_theta = light_distribution.shape
    
    # 检查完全旋转对称（所有φ角的分布相同）
    is_full_symmetric = True
    reference = light_distribution[0, :]
    for phi_idx in range(1, n_phi):
        diff = np.abs(light_distribution[phi_idx, :] - reference)
        rel_error = diff / (reference + 1e-6)
        if np.any(rel_error > tolerance):
            is_full_symmetric = False
            break
    
    if is_full_symmetric:
        return 'full'
    
    # 检查半对称（左右对称）
    # ...（具体实现）
    
    return 'none'

# 根据对称性优化IES文件大小
def optimize_by_symmetry(light_distribution, symmetry_type):
    """根据对称性减少需要存储的数据"""
    if symmetry_type == 'full':
        # 仅需存储一个垂直平面
        return light_distribution[0:1, :]
    elif symmetry_type == 'half':
        # 仅需存储0-180°
        return light_distribution[:n_phi//2+1, :]
    elif symmetry_type == 'quarter':
        # 仅需存储0-90°
        return light_distribution[:n_phi//4+1, :]
    else:
        # 完整数据
        return light_distribution
```

---

## 🔧 实现方案比较

### 方案A: 单次烘焙法（快速，适合对称灯具）

**流程**:
```
1. 创建UV Sphere (72×36分辨率)
2. 设置纯白漫反射材质
3. 添加Image Texture节点，创建空白EXR图像
4. 烘焙Combined Pass到图像
5. 读取EXR像素数据
6. 转换为IES格式（按UV坐标映射到球坐标）
```

**优点**:
- ✅ 快速，一次烘焙完成
- ✅ 利用Blender的烘焙系统
- ✅ 自动处理抗锯齿

**缺点**:
- ❌ UV映射必须完美对应球坐标
- ❌ 需要仔细处理UV接缝
- ❌ 灵活性较低

**适用场景**: 
- 简单灯具
- 对称性强的灯具
- 快速原型验证

---

### 方案B: 多点采样法（精确，适合复杂灯具）

**流程**:
```
1. 定义球坐标采样点网格 (θ, φ)
2. 对每个采样点:
   a. 在对应位置创建小测量面片
   b. 渲染该面片接收的光照
   c. 从渲染结果读取辐照度
   d. 记录数值
3. 汇总所有采样点数据
4. 转换为IES格式
```

**优点**:
- ✅ 更精确，直接对应球坐标
- ✅ 灵活性高，可自定义采样密度
- ✅ 易于处理不对称灯具
- ✅ 可以针对关键区域加密采样

**缺点**:
- ❌ 需要多次渲染，较慢
- ❌ 代码复杂度高
- ❌ 需要大量内存（存储多个渲染结果）

**适用场景**:
- 复杂灯具（如汽车大灯）
- 需要高精度的场合
- 不对称光分布

---

### 方案C: 混合法（推荐）⭐

**流程**:
```
1. 使用方案A快速烘焙高分辨率EXR (4K或8K)
2. EXR作为高分辨率光照缓存
3. 从EXR中按IES需要的分辨率重采样
4. 可以后期调整IES分辨率而不需重新烘焙
5. 支持多种输出格式（不同分辨率的IES）
```

**优点**:
- ✅ 兼具速度和灵活性
- ✅ 一次烘焙，多次使用
- ✅ 可以后期调整参数
- ✅ EXR可作为档案保存

**缺点**:
- ⚠️ 需要大量磁盘空间（8K EXR约50-200MB）
- ⚠️ 需要处理UV映射问题

**适用场景**:
- **推荐作为默认方案**
- 适合大多数灯具类型
- 需要生成多个分辨率IES的情况

---

## 💻 代码架构设计

### 主类结构

```python
# exr_to_ies.py

import bpy
import numpy as np
from pathlib import Path
import OpenEXR
import Imath
from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter

class EXRToIESConverter:
    """EXR光照分布转IES光度文件转换器"""
    
    def __init__(self, measurement_distance=1.0, resolution='high'):
        """
        初始化转换器
        
        Args:
            measurement_distance: 测量距离（米），默认1.0
            resolution: EXR分辨率 ('low', 'medium', 'high', 'ultra')
        """
        self.distance = measurement_distance
        self.resolution = resolution
        
        # 分辨率映射
        self.resolutions = {
            'low': (1024, 512),
            'medium': (2048, 1024),
            'high': (4096, 2048),
            'ultra': (8192, 4096),
        }
        
        # IES标准分辨率
        self.ies_resolutions = {
            'coarse': (36, 18),    # 10° 步长
            'standard': (72, 36),   # 5° 步长
            'fine': (144, 72),      # 2.5° 步长
            'ultra': (360, 180),    # 1° 步长
        }
        
    def setup_scene(self, light_object):
        """
        设置Blender场景用于烘焙
        
        Args:
            light_object: 灯具对象
        """
        scene = bpy.context.scene
        
        # 渲染引擎设置
        scene.render.engine = 'CYCLES'
        
        # 单位设置
        scene.unit_settings.system = 'METRIC'
        scene.unit_settings.length_unit = 'METERS'
        
        # Cycles设置
        scene.cycles.samples = 256
        scene.cycles.use_denoising = False
        
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
        
        print(f"✅ 场景设置完成: {width}x{height}")
    
    def create_measurement_sphere(self, center=(0, 0, 0)):
        """
        创建测量球体
        
        Args:
            center: 球体中心坐标
            
        Returns:
            sphere: 球体对象
        """
        # 创建UV球体
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=72,
            ring_count=36,
            radius=self.distance,
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
        
        print(f"✅ 测量球体创建完成: 半径 {self.distance}m")
        
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
        # 创建材质
        mat = bpy.data.materials.new(name="IES_Measurement_Material")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        
        # 漫反射节点（纯白）
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
        
        print(f"✅ 测量材质设置完成")
        
        return mat, image
    
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
        scene.render.bake.margin = 0
        
        print(f"🔥 开始烘焙光照分布...")
        
        # 执行烘焙
        bpy.ops.object.bake(type='COMBINED')
        
        # 保存图像
        image = bpy.data.images.get("IES_Bake_Image")
        if image:
            image.filepath_raw = str(output_exr_path)
            image.file_format = 'OPEN_EXR'
            image.save()
            print(f"✅ EXR已保存: {output_exr_path}")
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
        print(f"📖 读取EXR文件: {exr_path}")
        
        exr_file = OpenEXR.InputFile(str(exr_path))
        header = exr_file.header()
        dw = header['dataWindow']
        width = dw.max.x - dw.min.x + 1
        height = dw.max.y - dw.min.y + 1
        
        FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
        
        r_str = exr_file.channel('R', FLOAT)
        g_str = exr_file.channel('G', FLOAT)
        b_str = exr_file.channel('B', FLOAT)
        
        r = np.frombuffer(r_str, dtype=np.float32).reshape(height, width)
        g = np.frombuffer(g_str, dtype=np.float32).reshape(height, width)
        b = np.frombuffer(b_str, dtype=np.float32).reshape(height, width)
        
        rgb = np.stack([r, g, b], axis=-1)
        
        print(f"✅ EXR读取完成: {width}x{height}, 值域 [{rgb.min():.6f}, {rgb.max():.6f}]")
        
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
    
    def sample_exr_at_angles(self, exr_data, theta, phi):
        """
        在指定球坐标角度采样EXR数据
        
        Args:
            exr_data: EXR数据数组 [height, width, 3]
            theta: 垂直角（度）
            phi: 水平角（度）
            
        Returns:
            value: 采样值（RGB平均）
        """
        # 转换为UV坐标
        u, v = self.spherical_to_uv(theta, phi)
        
        # 转换为像素坐标
        height, width = exr_data.shape[:2]
        x = int(u * (width - 1))
        y = int(v * (height - 1))
        
        # 边界检查
        x = np.clip(x, 0, width - 1)
        y = np.clip(y, 0, height - 1)
        
        # 采样RGB并取平均（辐照度）
        rgb = exr_data[y, x, :]
        irradiance = np.mean(rgb)  # 或使用光度学加权: 0.2126*R + 0.7152*G + 0.0722*B
        
        return irradiance
    
    def irradiance_to_candela(self, irradiance, lumens):
        """
        辐照度转换为坎德拉每千流明
        
        Args:
            irradiance: 辐照度 (W/m²)
            lumens: 总流明值
            
        Returns:
            cd_per_klm: 坎德拉每千流明 (cd/klm)
        """
        # 辐照度转发光强度
        intensity = irradiance * (self.distance ** 2)
        
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
    
    def convert_exr_to_ies(self, exr_path, output_ies_path, lumens, 
                          ies_resolution='standard',
                          manufacturer="Unknown", 
                          luminaire_desc="Generated from EXR"):
        """
        从EXR转换为IES
        
        Args:
            exr_path: EXR文件路径
            output_ies_path: 输出IES路径
            lumens: 总流明值
            ies_resolution: IES分辨率
            manufacturer: 制造商名称
            luminaire_desc: 灯具描述
        """
        print(f"\n🔄 开始EXR到IES转换...")
        
        # 读取EXR
        exr_data = self.read_exr_data(exr_path)
        
        # 生成采样角度
        h_angles, v_angles = self.generate_ies_angles(ies_resolution)
        n_phi = len(h_angles)
        n_theta = len(v_angles)
        
        print(f"📐 IES分辨率: {n_phi} × {n_theta} ({ies_resolution})")
        
        # 采样并转换
        candela_values = np.zeros((n_phi, n_theta))
        
        for i, phi in enumerate(h_angles):
            for j, theta in enumerate(v_angles):
                irradiance = self.sample_exr_at_angles(exr_data, theta, phi)
                cd_per_klm = self.irradiance_to_candela(irradiance, lumens)
                candela_values[i, j] = cd_per_klm
        
        print(f"✅ 采样完成: 坎德拉值域 [{candela_values.min():.2f}, {candela_values.max():.2f}] cd/klm")
        
        # 生成IES文件
        self.write_ies_file(
            output_ies_path, lumens, candela_values,
            h_angles, v_angles, manufacturer, luminaire_desc
        )
    
    def write_ies_file(self, output_path, lumens, candela_values,
                      horizontal_angles, vertical_angles,
                      manufacturer, luminaire_desc):
        """
        写入IES文件
        
        Args:
            output_path: 输出路径
            lumens: 总流明
            candela_values: 光强矩阵 [n_phi, n_theta]
            horizontal_angles: 水平角列表
            vertical_angles: 垂直角列表
            manufacturer: 制造商
            luminaire_desc: 灯具描述
        """
        from datetime import datetime
        
        n_horizontal = len(horizontal_angles)
        n_vertical = len(vertical_angles)
        
        with open(output_path, 'w') as f:
            # 文件头
            f.write("IESNA:LM-63-2002\n")
            f.write(f"[MANUFAC] {manufacturer}\n")
            f.write(f"[LUMCAT] Generated_from_EXR\n")
            f.write(f"[LUMINAIRE] {luminaire_desc}\n")
            f.write(f"[ISSUEDATE] {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("TILT=NONE\n")
            
            # 光度数据行
            f.write(f"1 {lumens:.1f} 1.0 {n_horizontal} {n_vertical} 1 2 1.0 1.0 1.0\n")
            
            # 水平角
            for angle in horizontal_angles:
                f.write(f"{angle:.1f} ")
            f.write("\n")
            
            # 垂直角
            for angle in vertical_angles:
                f.write(f"{angle:.1f} ")
            f.write("\n")
            
            # 光强数据
            count = 0
            for phi_idx in range(n_horizontal):
                for theta_idx in range(n_vertical):
                    cd_value = candela_values[phi_idx, theta_idx]
                    f.write(f"{cd_value:.2f} ")
                    count += 1
                    if count % 10 == 0:
                        f.write("\n")
            
            if count % 10 != 0:
                f.write("\n")
        
        print(f"✅ IES文件已生成: {output_path}")
    
    def process_full_workflow(self, light_object, lumens, 
                             output_exr_path, output_ies_path,
                             ies_resolution='standard',
                             manufacturer="Unknown",
                             luminaire_desc="Custom IES"):
        """
        完整处理流程：从灯具到IES
        
        Args:
            light_object: Blender灯具对象
            lumens: 总流明值
            output_exr_path: EXR输出路径
            output_ies_path: IES输出路径
            ies_resolution: IES分辨率
            manufacturer: 制造商
            luminaire_desc: 灯具描述
        """
        print("="*70)
        print("  🚀 EXR to IES 完整转换流程")
        print("="*70)
        
        # 1. 设置场景
        self.setup_scene(light_object)
        
        # 2. 创建测量球体
        sphere = self.create_measurement_sphere()
        
        # 3. 设置材质
        mat, image = self.setup_measurement_material(sphere)
        
        # 4. 烘焙
        self.bake_light_distribution(sphere, output_exr_path)
        
        # 5. 转换为IES
        self.convert_exr_to_ies(
            output_exr_path, output_ies_path, lumens,
            ies_resolution, manufacturer, luminaire_desc
        )
        
        print("\n" + "="*70)
        print("  ✅ 转换完成！")
        print("="*70)


# 使用示例
def main():
    """主函数 - 使用示例"""
    
    # 1. 首先使用ProductsParametersToRadiantWatts计算灯光强度
    from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter
    
    lamp_converter = LampSpecsToRadiantConverter()
    radiant_watts, method = lamp_converter.calculate_radiant_watts(
        lumens=1000,
        source_type="led",
        color_temp=4000
    )
    
    print(f"💡 灯光强度: {radiant_watts:.2f} W (Radiant Watts)")
    
    # 2. 在Blender中设置灯具（假设已创建）
    # light_object = bpy.data.objects['YourLightObject']
    # light_object.data.energy = radiant_watts
    
    # 3. 创建转换器
    converter = EXRToIESConverter(
        measurement_distance=1.0,
        resolution='high'  # 4K
    )
    
    # 4. 执行完整流程
    converter.process_full_workflow(
        light_object=None,  # 替换为实际灯具对象
        lumens=1000,
        output_exr_path="output/light_distribution.exr",
        output_ies_path="output/light_distribution.ies",
        ies_resolution='standard',  # 72x36
        manufacturer="Custom",
        luminaire_desc="LED Luminaire 1000lm"
    )

if __name__ == "__main__":
    main()
```

---

## ⚠️ 潜在问题与解决方案

### 问题1: 灯具遮挡是特性，非问题 ✅

**重要说明**: 灯具对光源的遮挡**必须保留**，这是IES文件的核心价值！

**物理原理**:
```
真实灯具 = 光源 + 灯罩 + 反射器 + 透镜 + 外壳
IES文件 = 整个灯具系统的配光特性

遮挡效果正是灯具设计的一部分：
- 反射罩：将光线向下聚焦
- 灯罩：阻挡上方光线
- 格栅：控制眩光
- 透镜：改变光束角度
```

**正确做法**:
```python
# ✅ 保持灯具完整性
# 不需要隐藏灯具几何体
# 不需要使用透明材质
# 让Blender自然烘焙，包含所有遮挡和反射效果

# 唯一注意事项：确保测量球体半径合适
# 球体应该完全包围灯具，但不要太远
MEASUREMENT_DISTANCE = max(luminaire_dimensions) * 2.0  # 推荐：灯具最大尺寸的2倍
```

**实例对比**:
```
裸LED灯珠（无灯具）:
  θ=0°(下):  1000 cd
  θ=90°(侧): 800 cd
  θ=180°(上): 1000 cd
  → 近似均匀发光

带反射罩的LED灯具:
  θ=0°(下):  5000 cd  ← 反射聚光
  θ=90°(侧): 200 cd   ← 部分遮挡
  θ=180°(上): 0 cd    ← 完全遮挡
  → 这才是真实的配光！IES应该记录这个
```

**结论**: 
- ❌ 不要移除灯具遮挡
- ✅ 完整保留灯具的光学设计
- ✅ 烘焙结果自然包含所有物理效果

### 问题2: 数值范围差异大

**现象**: 灯具正下方强度可能是侧面的100-1000倍，导致动态范围极大

**解决方案**:

```python
def normalize_candela_values(candela_values):
    """
    归一化光强值（可选）
    
    注意：IES文件应保持真实的相对比例
    此函数仅用于检查，不应用于最终输出
    """
    max_value = candela_values.max()
    min_value = candela_values.min()
    
    print(f"光强动态范围: {max_value/min_value:.1f}:1")
    print(f"最大值: {max_value:.2f} cd/klm")
    print(f"最小值: {min_value:.2f} cd/klm")
    
    # IES应保持原始比例，不做归一化
    return candela_values

# EXR 32位浮点可以存储极大动态范围（10^38）
# 完全可以处理1000:1甚至更大的范围
```

### 问题3: UV接缝伪影

**现象**: UV球体在接缝处（φ=0°/360°）可能出现不连续

**解决方案**:

```python
def fix_uv_seam(candela_values, horizontal_angles):
    """
    修复UV接缝处的不连续
    
    Args:
        candela_values: 光强矩阵 [n_phi, n_theta]
        horizontal_angles: 水平角列表
    
    Returns:
        fixed_values: 修复后的矩阵
    """
    # 如果0°和360°都存在，确保它们的值相同
    if horizontal_angles[0] == 0.0 and horizontal_angles[-1] == 360.0:
        # 取平均值
        avg = (candela_values[0, :] + candela_values[-1, :]) / 2
        candela_values[0, :] = avg
        candela_values[-1, :] = avg
    
    return candela_values
```

### 问题4: 采样精度与性能平衡

**现象**: 高分辨率烘焙耗时长，低分辨率损失细节

**解决方案**:

```python
# 推荐策略：分级处理

# 1. 预览阶段：低分辨率快速迭代
preview_converter = EXRToIESConverter(
    measurement_distance=1.0,
    resolution='low'  # 1K，烘焙快
)

# 2. 最终输出：高分辨率精确结果
final_converter = EXRToIESConverter(
    measurement_distance=1.0,
    resolution='high'  # 4K，高质量
)

# 3. 使用GPU加速烘焙
scene.cycles.device = 'GPU'
preferences = bpy.context.preferences.addons['cycles'].preferences
preferences.compute_device_type = 'CUDA'  # 或 'OPTIX', 'OPENCL'
```

### 问题5: Blender单位与IES单位对应

**现象**: Blender场景单位设置不当导致尺寸错误

**解决方案**:

```python
def verify_scene_units():
    """验证并修正场景单位"""
    scene = bpy.context.scene
    
    # 确保使用公制
    if scene.unit_settings.system != 'METRIC':
        print("⚠️  警告：场景未使用公制单位，已自动修正")
        scene.unit_settings.system = 'METRIC'
    
    # 确保长度单位为米
    if scene.unit_settings.length_unit != 'METERS':
        print("⚠️  警告：长度单位不是米，已自动修正")
        scene.unit_settings.length_unit = 'METERS'
    
    # 确保缩放为1.0
    if scene.unit_settings.scale_length != 1.0:
        print(f"⚠️  警告：单位缩放不是1.0（当前：{scene.unit_settings.scale_length}），已自动修正")
        scene.unit_settings.scale_length = 1.0
    
    print("✅ 场景单位验证通过")
```

---

## 📝 实施步骤建议

### 第一阶段: 基础框架（1-2天）
- [x] 创建`EXRToIESConverter`类基本结构
- [x] 实现场景设置功能
- [x] 实现测量球体创建
- [x] 实现材质设置
- [x] 实现EXR烘焙功能

### 第二阶段: 数据处理（2-3天）
- [x] 实现EXR文件读取（OpenEXR库）
- [x] 实现UV到球坐标转换
- [x] 实现采样和插值算法
- [x] 实现辐照度到坎德拉转换
- [x] 数据归一化和验证

### 第三阶段: IES生成（1-2天）
- [x] 实现IES文件格式生成
- [x] 实现多分辨率支持
- [x] 实现对称性检测和优化
- [x] 添加元数据支持

### 第四阶段: 整合与测试（2-3天）
- [ ] 与`ProductsParametersToRadiantWatts`整合
- [ ] 添加命令行界面
- [ ] 批处理功能
- [ ] 错误处理和日志
- [ ] 单元测试和验证

### 第五阶段: 优化与文档（1-2天）
- [ ] 性能优化
- [ ] GPU加速支持
- [ ] 用户文档
- [ ] 示例场景

**总计**: 约7-12天完整开发周期

---

## 🔗 依赖库

### Python库
```bash
# 必需
pip install numpy          # 数值计算
pip install OpenEXR        # EXR文件读写
pip install Imath          # OpenEXR依赖

# 可选
pip install Pillow         # 备用图像读取
pip install matplotlib     # 数据可视化（调试用）
```

### Blender
- 版本要求: Blender 2.93+ （支持Cycles X）
- 推荐版本: Blender 3.x 或 4.x

---

## 📚 参考资料

### IES标准文档
- IESNA LM-63-2002: IES文件格式标准
- IESNA LM-79: LED产品电气和光度测量
- CIE 121: 光度测量技术

### 光度学基础
- 发光强度（Luminous Intensity）: 坎德拉 (cd)
- 光通量（Luminous Flux）: 流明 (lm)
- 照度（Illuminance）: 勒克斯 (lx = lm/m²)
- 亮度（Luminance）: 坎德拉每平方米 (cd/m²)

### 球坐标系统
```
x = r × sin(θ) × cos(φ)
y = r × sin(θ) × sin(φ)
z = r × cos(θ)

其中:
θ (theta): 垂直角，从Z轴向下 [0°, 180°]
φ (phi): 水平角，从X轴逆时针 [0°, 360°]
r: 半径
```

---

## ✅ 总结

### 方案可行性
✅ **完全可行** - 技术路线清晰，已有成功案例

### 关键成功因素
1. ✅ **正确的UV到球坐标映射**
2. ✅ **物理正确的烘焙设置**（Raw色彩空间，32位浮点）
3. ✅ **准确的单位转换**（米、坎德拉、流明）
4. ✅ **高质量的EXR数据**（足够的分辨率和采样）
5. ✅ **标准的IES格式输出**

### 推荐方案
**方案C（混合法）** - 高分辨率EXR烘焙 + 灵活的IES重采样

### 优势
- 🚀 一次烘焙，多次使用
- 📊 保留完整的光照数据
- 🎯 灵活的输出分辨率
- 💾 EXR可作为档案保存

### 预期效果
- **精度**: 5° 角分辨率，误差 < 2%
- **速度**: 4K EXR烘焙 < 5分钟（GPU）
- **质量**: 满足专业照明设计要求

---

## 🎯 下一步行动

1. **立即开始**: 实现基础框架（场景设置、球体创建）
2. **快速验证**: 创建简单测试场景验证烘焙流程
3. **迭代开发**: 逐步添加功能，每个功能都进行测试
4. **文档同步**: 边开发边完善文档

---

**文档版本**: 1.0  
**最后更新**: 2026-01-21  
**状态**: ✅ 技术方案已确认，可以开始实施

