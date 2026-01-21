#!/usr/bin/env python3
"""
Standalone EXR to IES Converter
纯粹的EXR到IES转换工具（不依赖Blender）

可以处理来自任何来源的EXR文件：
- Blender烘焙的EXR
- 3ds Max/V-Ray渲染的EXR
- Corona渲染器的EXR
- Arnold渲染器的EXR
- 任何其他离线渲染引擎的EXR

作者：EXR to IES Project
日期：2026-01-21
版本：1.0
"""

import numpy as np
from pathlib import Path
from datetime import datetime
import argparse
import sys


class StandaloneEXRToIES:
    """独立的EXR到IES转换器（不依赖Blender）"""

    def __init__(self, measurement_distance=5.0):
        """
        初始化转换器

        Args:
            measurement_distance: 测量距离（米）
                                 应该是EXR烘焙时使用的球体半径
        """
        self.measurement_distance = measurement_distance

        # IES分辨率选项
        self.ies_resolutions = {
            'coarse': (36, 18),    # 10° 步长
            'standard': (72, 36),   # 5° 步长
            'fine': (144, 72),      # 2.5° 步长
            'ultra': (360, 180),    # 1° 步长
        }

    def read_exr_openexr(self, exr_path):
        """
        使用OpenEXR库读取EXR文件

        Args:
            exr_path: EXR文件路径

        Returns:
            data: numpy数组 [height, width, 3] (RGB)
        """
        try:
            import OpenEXR
            import Imath
        except ImportError:
            print("❌ 错误：需要安装OpenEXR库")
            print("   安装命令：pip install OpenEXR")
            return None

        print(f"📖 读取EXR文件: {exr_path}")

        exr_file = OpenEXR.InputFile(str(exr_path))
        header = exr_file.header()
        dw = header['dataWindow']
        width = dw.max.x - dw.min.x + 1
        height = dw.max.y - dw.min.y + 1

        FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)

        # 读取RGB通道
        r_str = exr_file.channel('R', FLOAT)
        g_str = exr_file.channel('G', FLOAT)
        b_str = exr_file.channel('B', FLOAT)

        # 转换为numpy数组
        r = np.frombuffer(r_str, dtype=np.float32).reshape(height, width)
        g = np.frombuffer(g_str, dtype=np.float32).reshape(height, width)
        b = np.frombuffer(b_str, dtype=np.float32).reshape(height, width)

        # 合并为RGB图像
        rgb = np.stack([r, g, b], axis=-1)

        print(f"  ✅ EXR读取完成: {width}x{height}")
        print(f"  值域: [{rgb.min():.6f}, {rgb.max():.6f}]")

        return rgb

    def read_exr_pillow(self, exr_path):
        """
        使用Pillow读取EXR文件（备用方法）

        Args:
            exr_path: EXR文件路径

        Returns:
            data: numpy数组 [height, width, 3] (RGB)
        """
        try:
            from PIL import Image
        except ImportError:
            print("❌ 错误：需要安装Pillow库")
            print("   安装命令：pip install Pillow")
            return None

        print(f"📖 读取EXR文件（使用Pillow）: {exr_path}")

        img = Image.open(exr_path)
        data = np.array(img, dtype=np.float32)

        # 确保是RGB格式
        if len(data.shape) == 2:
            # 灰度图，转换为RGB
            data = np.stack([data, data, data], axis=-1)
        elif data.shape[2] == 4:
            # RGBA，只取RGB
            data = data[:, :, :3]

        print(f"  ✅ EXR读取完成: {data.shape[1]}x{data.shape[0]}")
        print(f"  值域: [{data.min():.6f}, {data.max():.6f}]")

        return data

    def read_exr(self, exr_path, method='auto'):
        """
        读取EXR文件（自动选择方法）

        Args:
            exr_path: EXR文件路径
            method: 读取方法 ('auto', 'openexr', 'pillow')

        Returns:
            data: numpy数组 [height, width, 3] (RGB)
        """
        exr_path = Path(exr_path)

        if not exr_path.exists():
            print(f"❌ 错误：文件不存在: {exr_path}")
            return None

        if method == 'auto':
            # 优先尝试OpenEXR，失败则使用Pillow
            data = self.read_exr_openexr(exr_path)
            if data is None:
                print("  尝试使用Pillow读取...")
                data = self.read_exr_pillow(exr_path)
            return data
        elif method == 'openexr':
            return self.read_exr_openexr(exr_path)
        elif method == 'pillow':
            return self.read_exr_pillow(exr_path)
        else:
            print(f"❌ 错误：未知的读取方法: {method}")
            return None

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
            theta: 垂直角（度）0-180
            phi: 水平角（度）0-360
            interpolation: 插值方法 ('nearest', 'bilinear')

        Returns:
            irradiance: 采样值（辐照度，W/m²）
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

            # 采样RGB
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
        # CIE 1931标准：R=0.2126, G=0.7152, B=0.0722
        irradiance = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

        return irradiance

    def irradiance_to_candela_per_klm(self, irradiance, total_lumens):
        """
        辐照度转换为坎德拉每千流明

        Args:
            irradiance: 辐照度 (W/m²)
            total_lumens: 总流明值

        Returns:
            cd_per_klm: 坎德拉每千流明 (cd/klm)
        """
        # 辐照度转发光强度（考虑距离平方反比）
        intensity = irradiance * (self.measurement_distance ** 2)

        # 转换为cd/klm
        cd_per_klm = (intensity / total_lumens) * 1000.0

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

    def convert_exr_to_ies_data(self, exr_data, total_lumens, ies_resolution='standard'):
        """
        从EXR数据转换为IES光强数据

        Args:
            exr_data: EXR数据数组
            total_lumens: 总流明值
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
        print(f"  测量距离: {self.measurement_distance} m")

        # 采样并转换
        candela_values = np.zeros((n_phi, n_theta))

        for i, phi in enumerate(h_angles):
            for j, theta in enumerate(v_angles):
                irradiance = self.sample_exr_at_angles(exr_data, theta, phi)
                cd_per_klm = self.irradiance_to_candela_per_klm(irradiance, total_lumens)
                candela_values[i, j] = cd_per_klm

        print(f"  ✅ 采样完成")
        print(f"  坎德拉值域: [{candela_values.min():.2f}, {candela_values.max():.2f}] cd/klm")

        return candela_values, h_angles, v_angles

    def write_ies_file(self, output_path,
                      total_lumens,
                      candela_values,
                      horizontal_angles,
                      vertical_angles,
                      # 可选元数据
                      manufacturer="Unknown",
                      catalog_number="",
                      luminaire_name="Generated from EXR",
                      lamp_description="",
                      width=1.0,
                      length=1.0,
                      height=1.0,
                      photometric_type=1):
        """
        写入IES文件

        Args:
            output_path: 输出路径
            total_lumens: 总流明值
            candela_values: 光强矩阵 [n_phi, n_theta]
            horizontal_angles: 水平角列表
            vertical_angles: 垂直角列表
            manufacturer: 制造商名称
            catalog_number: 产品编号
            luminaire_name: 灯具名称
            lamp_description: 灯泡描述
            width: 灯具宽度（米）
            length: 灯具长度（米）
            height: 灯具高度（米）
            photometric_type: 光度类型（1=C, 2=B, 3=A）
        """
        n_horizontal = len(horizontal_angles)
        n_vertical = len(vertical_angles)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            # 文件头
            f.write("IESNA:LM-63-2002\n")
            f.write(f"[MANUFAC] {manufacturer}\n")
            f.write(f"[LUMCAT] {catalog_number or 'Generated_from_EXR'}\n")
            f.write(f"[LUMINAIRE] {luminaire_name}\n")
            if lamp_description:
                f.write(f"[LAMP] {lamp_description}\n")
            f.write(f"[ISSUEDATE] {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"[OTHER] Generated by Standalone EXR to IES Converter\n")
            f.write("TILT=NONE\n")

            # 光度数据行（10个值）
            f.write(f"1 {total_lumens:.1f} 1.0 {n_horizontal} {n_vertical} "
                   f"{photometric_type} 2 "
                   f"{width:.3f} {length:.3f} {height:.3f}\n")

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
        print(f"   流明值: {total_lumens:.0f} lm")
        print(f"   分辨率: {n_horizontal}×{n_vertical}")

    def convert(self,
                exr_path,
                output_ies_path,
                total_lumens,
                ies_resolution='standard',
                # 可选参数
                manufacturer="Unknown",
                catalog_number="",
                luminaire_name="",
                lamp_description="",
                width=1.0,
                length=1.0,
                height=1.0):
        """
        完整转换流程：从EXR到IES

        Args:
            exr_path: EXR文件路径
            output_ies_path: 输出IES路径
            total_lumens: 总流明值
            ies_resolution: IES分辨率 ('coarse', 'standard', 'fine', 'ultra')
            manufacturer: 制造商（可选）
            catalog_number: 产品编号（可选）
            luminaire_name: 灯具名称（可选）
            lamp_description: 灯泡描述（可选）
            width: 灯具宽度（米，可选）
            length: 灯具长度（米，可选）
            height: 灯具高度（米，可选）

        Returns:
            success: 是否成功
        """
        print("\n" + "="*70)
        print("  🚀 EXR to IES 转换")
        print("="*70)
        print(f"输入EXR: {exr_path}")
        print(f"输出IES: {output_ies_path}")
        print(f"流明值: {total_lumens} lm")
        print(f"测量距离: {self.measurement_distance} m")
        print("="*70)

        try:
            # 1. 读取EXR
            exr_data = self.read_exr(exr_path)
            if exr_data is None:
                return False

            # 2. 转换为IES数据
            candela_values, h_angles, v_angles = self.convert_exr_to_ies_data(
                exr_data, total_lumens, ies_resolution
            )

            # 3. 写入IES文件
            if not luminaire_name:
                luminaire_name = f"Luminaire {total_lumens:.0f}lm"

            self.write_ies_file(
                output_ies_path,
                total_lumens,
                candela_values,
                h_angles,
                v_angles,
                manufacturer=manufacturer,
                catalog_number=catalog_number,
                luminaire_name=luminaire_name,
                lamp_description=lamp_description,
                width=width,
                length=length,
                height=height
            )

            print("\n" + "="*70)
            print("  ✅ 转换完成！")
            print("="*70 + "\n")

            return True

        except Exception as e:
            print(f"\n❌ 转换过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='EXR到IES转换器（独立版本，不依赖Blender）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：

  # 基本使用
  python standalone_exr_to_ies.py input.exr output.ies -l 1000 -d 5.0

  # 指定IES分辨率
  python standalone_exr_to_ies.py input.exr output.ies -l 1000 -d 5.0 -r fine

  # 添加元数据
  python standalone_exr_to_ies.py input.exr output.ies -l 1000 -d 5.0 \\
      --manufacturer "Custom Lighting" \\
      --name "LED Downlight" \\
      --catalog "DL-1000"

  # 指定灯具尺寸
  python standalone_exr_to_ies.py input.exr output.ies -l 1000 -d 5.0 \\
      --width 0.15 --length 0.15 --height 0.10

注意事项：
  1. 测量距离(-d)应该与EXR烘焙时的球体半径一致
  2. 流明值(-l)是灯具的总光通量
  3. EXR文件应该是equirectangular全景格式（2:1比例）
        """
    )

    # 必需参数
    parser.add_argument('exr_path', help='输入EXR文件路径')
    parser.add_argument('ies_path', help='输出IES文件路径')
    parser.add_argument('-l', '--lumens', type=float, required=True,
                       help='总流明值（必需）')
    parser.add_argument('-d', '--distance', type=float, default=5.0,
                       help='测量距离（米），应与EXR烘焙时的球体半径一致（默认5.0）')

    # IES配置
    parser.add_argument('-r', '--resolution',
                       choices=['coarse', 'standard', 'fine', 'ultra'],
                       default='standard',
                       help='IES分辨率（默认standard）')

    # 元数据
    parser.add_argument('--manufacturer', default='Unknown',
                       help='制造商名称')
    parser.add_argument('--catalog', default='',
                       help='产品编号')
    parser.add_argument('--name', default='',
                       help='灯具名称')
    parser.add_argument('--lamp-desc', default='',
                       help='灯泡描述')

    # 灯具尺寸
    parser.add_argument('--width', type=float, default=1.0,
                       help='灯具宽度（米，默认1.0）')
    parser.add_argument('--length', type=float, default=1.0,
                       help='灯具长度（米，默认1.0）')
    parser.add_argument('--height', type=float, default=1.0,
                       help='灯具高度（米，默认1.0）')

    args = parser.parse_args()

    # 创建转换器
    converter = StandaloneEXRToIES(measurement_distance=args.distance)

    # 执行转换
    success = converter.convert(
        exr_path=args.exr_path,
        output_ies_path=args.ies_path,
        total_lumens=args.lumens,
        ies_resolution=args.resolution,
        manufacturer=args.manufacturer,
        catalog_number=args.catalog,
        luminaire_name=args.name,
        lamp_description=args.lamp_desc,
        width=args.width,
        length=args.length,
        height=args.height
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
