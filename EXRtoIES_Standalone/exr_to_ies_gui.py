# -*- coding: utf-8 -*-
"""
EXR to IES Converter - GUI版本 (增强版)
独立的图形界面工具，用于将EXR文件转换为IES光度文件

功能：
1. 选择EXR文件
2. 输入必要参数（流明、测量距离等）
3. 自定义IES文件头信息
4. 一键转换生成IES文件
5. 3D配光曲线可视化
6. 专业光度图表分析

作者：EXR to IES Project
版本：v2.0 (with Visualization)
日期：2026-01-21
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import numpy as np
from pathlib import Path
from datetime import datetime
import sys
import io

# 设置标准输出编码为UTF-8，避免中文乱码
# 在EXE环境下，sys.stdout可能是None或没有buffer属性
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer is not None:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except (AttributeError, TypeError):
        # 在EXE环境下或其他特殊情况下，忽略编码设置
        pass




class EXRToIESConverter:
    """EXR到IES转换器（内嵌版本）"""

    def __init__(self, measurement_distance=5.0):
        self.measurement_distance = measurement_distance

        # IES分辨率选项
        self.ies_resolutions = {
            '粗糙 (36×18, 10°)': (36, 18),
            '标准 (72×36, 5°)': (72, 36),
            '精细 (144×72, 2.5°)': (144, 72),
            '超精细 (360×180, 1°)': (360, 180),
        }

    def read_exr(self, exr_path):
        """读取EXR文件 - 增强版，支持多种读取方法"""
        errors = []

        # 方法1: 尝试使用OpenEXR（最精确）
        try:
            import OpenEXR
            import Imath

            exr_file = OpenEXR.InputFile(str(exr_path))
            header = exr_file.header()
            dw = header['dataWindow']
            width = dw.max.x - dw.min.x + 1
            height = dw.max.y - dw.min.y + 1

            FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)

            # 检查通道是否存在
            channels = header['channels']

            # 尝试读取RGB通道
            if 'R' in channels and 'G' in channels and 'B' in channels:
                r_str = exr_file.channel('R', FLOAT)
                g_str = exr_file.channel('G', FLOAT)
                b_str = exr_file.channel('B', FLOAT)

                r = np.frombuffer(r_str, dtype=np.float32).reshape(height, width)
                g = np.frombuffer(g_str, dtype=np.float32).reshape(height, width)
                b = np.frombuffer(b_str, dtype=np.float32).reshape(height, width)

                rgb = np.stack([r, g, b], axis=-1)
                print(f"✓ OpenEXR读取成功: {width}x{height}, RGB通道")
                return rgb
            else:
                # 如果没有RGB通道，尝试其他通道组合
                available_channels = list(channels.keys())
                raise ValueError(f"EXR文件缺少RGB通道，可用通道: {available_channels}")

        except ImportError:
            errors.append("OpenEXR未安装")
        except Exception as e:
            import traceback
            error_detail = str(e)
            errors.append(f"OpenEXR失败: {error_detail}")
            # 打印详细错误用于调试
            print(f"OpenEXR错误详情: {error_detail}")
            traceback.print_exc()

        # 方法2: 尝试使用imageio（推荐）
        try:
            # 使用v2 API避免警告
            try:
                import imageio.v2 as imageio
            except:
                import imageio

            img = imageio.imread(str(exr_path))
            data = np.array(img, dtype=np.float32)

            if len(data.shape) == 2:
                rgb = np.stack([data, data, data], axis=-1)
            elif data.shape[2] == 1:
                rgb = np.repeat(data, 3, axis=-1)
            elif data.shape[2] >= 3:
                rgb = data[:, :, :3]
            else:
                raise ValueError(f"不支持的形状: {data.shape}")

            print(f"✓ imageio读取成功: {rgb.shape}")
            return rgb

        except ImportError:
            errors.append("imageio未安装")
        except Exception as e:
            errors.append(f"imageio失败: {str(e)[:50]}")

        # 方法3: 尝试使用Pillow
        try:
            from PIL import Image
            img = Image.open(str(exr_path))

            # 转换为RGB模式
            if img.mode not in ['RGB', 'RGBA', 'F']:
                img = img.convert('RGB')

            data = np.array(img, dtype=np.float32)

            if len(data.shape) == 2:
                rgb = np.stack([data, data, data], axis=-1)
            elif data.shape[2] == 4:
                rgb = data[:, :, :3]
            elif data.shape[2] >= 3:
                rgb = data[:, :, :3]
            else:
                rgb = data

            # 如果值在0-255范围，归一化
            if rgb.max() > 10.0:
                rgb = rgb / 255.0

            print(f"✓ Pillow读取成功: {rgb.shape}")
            return rgb

        except ImportError:
            errors.append("Pillow未安装")
        except Exception as e:
            errors.append(f"Pillow失败: {str(e)[:50]}")

        # 方法4: 尝试使用OpenCV
        try:
            import cv2
            img = cv2.imread(str(exr_path), cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)

            if img is None:
                raise ValueError("OpenCV返回None")

            # BGR转RGB
            if len(img.shape) == 3 and img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            elif len(img.shape) == 2:
                img = np.stack([img, img, img], axis=-1)

            print(f"✓ OpenCV读取成功: {img.shape}")
            return img.astype(np.float32)

        except ImportError:
            errors.append("OpenCV未安装")
        except Exception as e:
            errors.append(f"OpenCV失败: {str(e)[:50]}")

        # 所有方法都失败
        from pathlib import Path
        error_msg = (
            f"无法读取EXR文件: {Path(exr_path).name}\n\n"
            f"尝试的方法:\n" + "\n".join([f"  • {err}" for err in errors]) +
            f"\n\n💡 解决方案:\n"
            f"  OpenEXR可以识别您的文件，但读取时出错\n"
            f"  请检查上方的详细错误信息\n"
            f"  或尝试: pip install opencv-python"
        )
        raise ValueError(error_msg)

    def sample_exr_at_angles(self, exr_data, theta, phi):
        """在指定角度采样EXR"""
        u = phi / 360.0
        v = theta / 180.0

        height, width = exr_data.shape[:2]

        x_float = u * (width - 1)
        y_float = v * (height - 1)

        x0 = int(np.floor(x_float))
        x1 = min(x0 + 1, width - 1)
        y0 = int(np.floor(y_float))
        y1 = min(y0 + 1, height - 1)

        wx = x_float - x0
        wy = y_float - y0

        rgb = ((1 - wx) * (1 - wy) * exr_data[y0, x0, :] +
               wx * (1 - wy) * exr_data[y0, x1, :] +
               (1 - wx) * wy * exr_data[y1, x0, :] +
               wx * wy * exr_data[y1, x1, :])

        # 光度学加权
        irradiance = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
        return irradiance

    def convert_to_ies(self, exr_data, lumens, ies_resolution, metadata):
        """转换为IES数据"""
        n_phi, n_theta = ies_resolution

        h_angles = np.linspace(0, 360, n_phi)
        v_angles = np.linspace(0, 180, n_theta)

        candela_values = np.zeros((n_phi, n_theta))

        for i, phi in enumerate(h_angles):
            for j, theta in enumerate(v_angles):
                irradiance = self.sample_exr_at_angles(exr_data, theta, phi)
                intensity = irradiance * (self.measurement_distance ** 2)
                cd_per_klm = (intensity / lumens) * 1000.0
                candela_values[i, j] = cd_per_klm

        return candela_values, h_angles, v_angles

    def write_ies_file(self, output_path, lumens, candela_values,
                      h_angles, v_angles, metadata):
        """写入IES文件"""
        n_horizontal = len(h_angles)
        n_vertical = len(v_angles)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("IESNA:LM-63-2002\n")
            f.write(f"[MANUFAC] {metadata['manufacturer']}\n")
            f.write(f"[LUMCAT] {metadata['catalog_number']}\n")
            f.write(f"[LUMINAIRE] {metadata['luminaire_name']}\n")
            f.write(f"[LAMP] {metadata['lamp_description']}\n")
            f.write(f"[ISSUEDATE] {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"[OTHER] {metadata['other_info']}\n")
            f.write("TILT=NONE\n")

            f.write(f"1 {lumens:.1f} 1.0 {n_horizontal} {n_vertical} "
                   f"{metadata['photometric_type']} 2 "
                   f"{metadata['width']:.3f} {metadata['length']:.3f} {metadata['height']:.3f}\n")

            for angle in h_angles:
                f.write(f"{angle:.1f} ")
            f.write("\n")

            for angle in v_angles:
                f.write(f"{angle:.1f} ")
            f.write("\n")

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


class IESVisualizer:
    """IES可视化器 - 生成3D配光曲线和专业光度图表"""

    def __init__(self):
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D

            # 配置matplotlib支持中文显示
            import matplotlib.font_manager as fm

            # 尝试设置中文字体
            chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'STSong', 'FangSong']
            font_found = False

            for font_name in chinese_fonts:
                try:
                    # 检查字体是否可用
                    font_list = [f.name for f in fm.fontManager.ttflist]
                    if font_name in font_list:
                        plt.rcParams['font.sans-serif'] = [font_name]
                        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                        font_found = True
                        print(f"使用字体: {font_name}")
                        break
                except:
                    continue

            if not font_found:
                # 如果没有找到中文字体，使用默认设置
                plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
                print("警告: 未找到中文字体，可能显示方框")

            self.plt = plt
            self.has_matplotlib = True
        except ImportError:
            self.has_matplotlib = False

    def visualize_ies(self, candela_values, h_angles, v_angles, metadata):
        """
        可视化IES数据

        Args:
            candela_values: 坎德拉值数组 (n_phi, n_theta)
            h_angles: 水平角度
            v_angles: 垂直角度
            metadata: IES元数据
        """
        if not self.has_matplotlib:
            return None, "需要安装matplotlib库才能显示可视化\n请运行: pip install matplotlib"

        try:
            # 创建图表窗口
            fig = self.plt.figure(figsize=(16, 10))
            fig.suptitle(f'IES Photometric Analysis - {metadata.get("luminaire_name", "Unknown")}',
                        fontsize=16, fontweight='bold')

            # 1. 3D极坐标配光曲线
            ax1 = fig.add_subplot(2, 3, 1, projection='3d')
            self._plot_3d_polar(ax1, candela_values, h_angles, v_angles)

            # 2. 俯视图 (水平配光)
            ax2 = fig.add_subplot(2, 3, 2, projection='polar')
            self._plot_horizontal_distribution(ax2, candela_values, h_angles, v_angles)

            # 3. 侧视图 (垂直配光 - C0-C180)
            ax3 = fig.add_subplot(2, 3, 3, projection='polar')
            self._plot_vertical_distribution(ax3, candela_values, h_angles, v_angles,
                                            plane_angles=[0, 180])

            # 4. 伪彩色配光图
            ax4 = fig.add_subplot(2, 3, 4)
            self._plot_intensity_map(ax4, candela_values, h_angles, v_angles)

            # 5. 垂直配光曲线 (多个C平面)
            ax5 = fig.add_subplot(2, 3, 5, projection='polar')
            self._plot_vertical_distribution_multi(ax5, candela_values, h_angles, v_angles)

            # 6. 光度数据统计
            ax6 = fig.add_subplot(2, 3, 6)
            self._plot_statistics(ax6, candela_values, metadata)

            self.plt.tight_layout(rect=[0, 0.03, 1, 0.96])

            return fig, None

        except Exception as e:
            return None, f"可视化错误: {str(e)}"

    def _plot_3d_polar(self, ax, candela_values, h_angles, v_angles):
        """绘制3D极坐标配光曲线"""
        ax.set_title('3D Polar Distribution', fontsize=10, fontweight='bold')

        # ...existing code...
        theta_grid = np.deg2rad(v_angles)
        phi_grid = np.deg2rad(h_angles)

        # 归一化坎德拉值用于半径
        max_cd = np.max(candela_values)
        if max_cd > 0:
            r_normalized = candela_values / max_cd
        else:
            r_normalized = candela_values

        # 采样降低密度（每隔几个点取一个）
        step = max(1, len(h_angles) // 36)
        phi_sample = phi_grid[::step]
        theta_sample = theta_grid

        for i, phi in enumerate(phi_sample):
            idx = i * step
            if idx >= len(r_normalized):
                break
            r_slice = r_normalized[idx, :]

            x = r_slice * np.sin(theta_sample) * np.cos(phi)
            y = r_slice * np.sin(theta_sample) * np.sin(phi)
            z = r_slice * np.cos(theta_sample)

            # 颜色映射
            colors = self.plt.cm.jet(r_slice)
            ax.plot(x, y, z, alpha=0.6, linewidth=0.8)

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z (光轴)')
        try:
            ax.set_box_aspect([1,1,1])
        except:
            pass

        # 添加图例
        ax.text2D(0.05, 0.95, f'最大值: {max_cd:.1f} cd/klm',
                 transform=ax.transAxes, fontsize=8)

    def _plot_horizontal_distribution(self, ax, candela_values, h_angles, v_angles):
        """绘制水平配光图 (C-Plane at γ=90°)"""
        ax.set_title('Horizontal Distribution\nC-plane at gamma=90°',
                    fontsize=10, fontweight='bold')

        # 找到最接近90度的垂直角度索引
        gamma_90_idx = np.argmin(np.abs(v_angles - 90))
        horizontal_slice = candela_values[:, gamma_90_idx]

        theta = np.deg2rad(h_angles)
        ax.plot(theta, horizontal_slice, 'b-', linewidth=2, label='gamma=90°')

        # 填充
        ax.fill(theta, horizontal_slice, alpha=0.3)

        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_xlabel('C-angle (deg)', fontsize=8)
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(True, alpha=0.3)

    def _plot_vertical_distribution(self, ax, candela_values, h_angles, v_angles,
                                    plane_angles=[0, 180]):
        """绘制垂直配光图 (指定C平面)"""
        ax.set_title('Vertical Distribution\nC0-C180 plane',
                    fontsize=10, fontweight='bold')

        theta = np.deg2rad(v_angles)

        for c_angle in plane_angles:
            c_idx = np.argmin(np.abs(h_angles - c_angle))
            vertical_slice = candela_values[c_idx, :]

            ax.plot(theta, vertical_slice, linewidth=2,
                   label=f'C{int(c_angle)}', alpha=0.8)

        ax.set_theta_zero_location('N')
        ax.set_theta_direction(1)
        ax.set_thetamin(0)
        ax.set_thetamax(180)
        ax.set_xlabel('Gamma-angle (deg)', fontsize=8)
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(True, alpha=0.3)

    def _plot_vertical_distribution_multi(self, ax, candela_values, h_angles, v_angles):
        """绘制多个C平面的垂直配光"""
        ax.set_title('Multi-plane Vertical',
                    fontsize=10, fontweight='bold')

        theta = np.deg2rad(v_angles)
        c_planes = [0, 45, 90, 135, 180, 225, 270, 315]

        colors = self.plt.cm.rainbow(np.linspace(0, 1, len(c_planes)))

        for i, c_angle in enumerate(c_planes):
            c_idx = np.argmin(np.abs(h_angles - c_angle))
            vertical_slice = candela_values[c_idx, :]

            ax.plot(theta, vertical_slice, linewidth=1.5,
                   label=f'C{int(c_angle)}', color=colors[i], alpha=0.7)

        ax.set_theta_zero_location('N')
        ax.set_theta_direction(1)
        ax.set_thetamin(0)
        ax.set_thetamax(180)
        ax.legend(loc='upper right', fontsize=6, ncol=2)
        ax.grid(True, alpha=0.3)

    def _plot_intensity_map(self, ax, candela_values, h_angles, v_angles):
        """绘制光强分布热图"""
        ax.set_title('Intensity Map', fontsize=10, fontweight='bold')

        # 转置数据以正确显示
        im = ax.imshow(candela_values.T, aspect='auto', origin='lower',
                      extent=[h_angles[0], h_angles[-1], v_angles[0], v_angles[-1]],
                      cmap='jet', interpolation='bilinear')

        ax.set_xlabel('C-angle (deg)', fontsize=9)
        ax.set_ylabel('Gamma-angle (deg)', fontsize=9)

        # 添加颜色条
        cbar = self.plt.colorbar(im, ax=ax)
        cbar.set_label('cd/klm', fontsize=8)

        # 添加网格
        ax.grid(True, alpha=0.3, color='white', linewidth=0.5)

    def _plot_statistics(self, ax, candela_values, metadata):
        """绘制光度统计信息"""
        ax.axis('off')
        ax.set_title('Photometric Statistics',
                    fontsize=10, fontweight='bold')

        max_cd = np.max(candela_values)
        min_cd = np.min(candela_values)
        mean_cd = np.mean(candela_values)
        std_cd = np.std(candela_values)

        # 找到最大值位置
        max_idx = np.unravel_index(np.argmax(candela_values), candela_values.shape)

        stats_text = f"""
[Basic Info]
Luminaire: {metadata.get('luminaire_name', 'N/A')}
Manufacturer: {metadata.get('manufacturer', 'N/A')}
Lumens: {metadata.get('lumens', 'N/A')} lm

[Photometric Data]
Max Intensity: {max_cd:.2f} cd/klm
Min Intensity: {min_cd:.2f} cd/klm
Avg Intensity: {mean_cd:.2f} cd/klm
Std Dev: {std_cd:.2f}

[Max Intensity Direction]
Horizontal (C): {max_idx[0]}
Vertical (gamma): {max_idx[1]}

[Data Points]
Horizontal samples: {candela_values.shape[0]} pts
Vertical samples: {candela_values.shape[1]} pts
Total points: {candela_values.size} pts

[Light Distribution]
Symmetry: {'Axisymmetric' if self._check_symmetry(candela_values) else 'Asymmetric'}
Beam Angle: {self._calculate_beam_angle(candela_values):.1f} deg
        """

        ax.text(0.1, 0.5, stats_text, fontsize=9, family='monospace',
               verticalalignment='center', bbox=dict(boxstyle='round',
               facecolor='wheat', alpha=0.3))

    def _check_symmetry(self, candela_values):
        """检查配光是否轴对称"""
        # 简单检查：比较0度和180度的差异
        if candela_values.shape[0] < 2:
            return False

        slice_0 = candela_values[0, :]
        slice_180 = candela_values[candela_values.shape[0]//2, :]

        correlation = np.corrcoef(slice_0, slice_180)[0, 1]
        return correlation > 0.95

    def _calculate_beam_angle(self, candela_values):
        """计算光束角 (50%最大光强的角度范围)"""
        max_cd = np.max(candela_values)
        threshold = max_cd * 0.5

        # 在垂直方向查找
        vertical_max = np.max(candela_values, axis=0)
        above_threshold = vertical_max >= threshold

        if not np.any(above_threshold):
            return 0.0

        # 找到超过阈值的角度范围
        indices = np.where(above_threshold)[0]
        angle_range = len(indices) * (180.0 / len(vertical_max))

        return angle_range


class ConverterGUI:
    """转换器图形界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("EXR转IES转换器 v2.0")
        self.root.geometry("800x900")
        self.root.resizable(True, True)

        # 设置默认字体，避免乱码
        try:
            import locale
            locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
        except:
            pass

        self.exr_path = None
        self.converter = None
        self.visualizer = IESVisualizer()
        self.last_conversion_data = None  # 存储最后的转换数据

        self.setup_styles()
        self.create_widgets()
        self.center_window()

    def setup_styles(self):
        """设置样式 - 使用中文友好字体"""
        style = ttk.Style()
        style.theme_use('clam')

        # 尝试使用中文字体，避免乱码
        chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial']
        default_font = None

        # 检测可用的中文字体
        import tkinter.font as tkfont
        available_fonts = tkfont.families()

        for font in chinese_fonts:
            if font in available_fonts:
                default_font = font
                break

        if not default_font:
            default_font = 'TkDefaultFont'

        # 配置样式，使用检测到的字体
        style.configure('Title.TLabel', font=(default_font, 16, 'bold'))
        style.configure('Header.TLabel', font=(default_font, 11, 'bold'))
        style.configure('Info.TLabel', font=(default_font, 9))
        style.configure('Action.TButton', font=(default_font, 10, 'bold'))

    def center_window(self):
        """居中窗口"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text="📁 EXR转IES转换器 (带可视化)",
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0, pady=(0, 5))

        subtitle_label = ttk.Label(
            main_frame,
            text="将EXR光照分布文件转换为标准IES格式 | 支持3D配光曲线可视化",
            style='Info.TLabel'
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 20))

        # EXR文件选择
        file_frame = ttk.LabelFrame(main_frame, text="1. 选择EXR文件", padding="15")
        file_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        file_frame.columnconfigure(0, weight=1)

        self.file_path_var = tk.StringVar(value="未选择文件")
        ttk.Label(file_frame, textvariable=self.file_path_var, foreground='gray').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10)
        )

        ttk.Button(file_frame, text="📂 浏览...", command=self.browse_exr_file).grid(
            row=0, column=1
        )

        # 基本参数
        param_frame = ttk.LabelFrame(main_frame, text="2. 输入转换参数", padding="15")
        param_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        param_frame.columnconfigure(1, weight=1)

        # 流明值
        ttk.Label(param_frame, text="流明值 (lm):", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=8
        )
        self.lumens_var = tk.StringVar(value="1000")
        ttk.Entry(param_frame, textvariable=self.lumens_var, font=('Arial', 10)).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=8
        )
        ttk.Label(param_frame, text="灯具的总光通量", style='Info.TLabel',
                 foreground='gray').grid(row=1, column=1, sticky=tk.W, padx=(10, 0))

        # 测量距离
        ttk.Label(param_frame, text="测量距离 (m):", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, pady=8
        )
        self.distance_var = tk.StringVar(value="5.0")
        ttk.Entry(param_frame, textvariable=self.distance_var, font=('Arial', 10)).grid(
            row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=8
        )
        ttk.Label(param_frame, text="EXR烘焙时的球体半径（必须一致！）",
                 style='Info.TLabel', foreground='red').grid(
            row=3, column=1, sticky=tk.W, padx=(10, 0)
        )

        # IES分辨率
        ttk.Label(param_frame, text="IES分辨率:", font=('Arial', 10, 'bold')).grid(
            row=4, column=0, sticky=tk.W, pady=8
        )
        self.resolution_var = tk.StringVar()
        resolution_combo = ttk.Combobox(
            param_frame,
            textvariable=self.resolution_var,
            state='readonly',
            font=('Arial', 10)
        )
        resolution_combo['values'] = list(EXRToIESConverter(5.0).ies_resolutions.keys())
        resolution_combo.current(1)  # 默认选择"标准"
        resolution_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=8)

        # IES文件头信息
        metadata_frame = ttk.LabelFrame(main_frame, text="3. IES文件头信息（可选）", padding="15")
        metadata_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        metadata_frame.columnconfigure(1, weight=1)

        # 制造商
        ttk.Label(metadata_frame, text="制造商:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.manufacturer_var = tk.StringVar(value="Custom Lighting")
        ttk.Entry(metadata_frame, textvariable=self.manufacturer_var).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5
        )

        # 产品编号
        ttk.Label(metadata_frame, text="产品编号:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.catalog_var = tk.StringVar(value="")
        ttk.Entry(metadata_frame, textvariable=self.catalog_var).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5
        )

        # 灯具名称
        ttk.Label(metadata_frame, text="灯具名称:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.luminaire_name_var = tk.StringVar(value="Generated from EXR")
        ttk.Entry(metadata_frame, textvariable=self.luminaire_name_var).grid(
            row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5
        )

        # 灯泡描述
        ttk.Label(metadata_frame, text="灯泡描述:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.lamp_desc_var = tk.StringVar(value="LED Light Source")
        ttk.Entry(metadata_frame, textvariable=self.lamp_desc_var).grid(
            row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5
        )

        # 其他信息
        ttk.Label(metadata_frame, text="其他信息:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.other_info_var = tk.StringVar(value="Generated by EXR to IES Converter")
        ttk.Entry(metadata_frame, textvariable=self.other_info_var).grid(
            row=4, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5
        )

        # 灯具尺寸
        size_sub_frame = ttk.Frame(metadata_frame)
        size_sub_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(size_sub_frame, text="灯具尺寸 (m):").grid(row=0, column=0, sticky=tk.W)

        ttk.Label(size_sub_frame, text="宽").grid(row=0, column=1, padx=(10, 5))
        self.width_var = tk.StringVar(value="0.15")
        ttk.Entry(size_sub_frame, textvariable=self.width_var, width=8).grid(row=0, column=2)

        ttk.Label(size_sub_frame, text="长").grid(row=0, column=3, padx=(10, 5))
        self.length_var = tk.StringVar(value="0.15")
        ttk.Entry(size_sub_frame, textvariable=self.length_var, width=8).grid(row=0, column=4)

        ttk.Label(size_sub_frame, text="高").grid(row=0, column=5, padx=(10, 5))
        self.height_var = tk.StringVar(value="0.10")
        ttk.Entry(size_sub_frame, textvariable=self.height_var, width=8).grid(row=0, column=6)

        # 转换按钮区域
        button_row = ttk.Frame(main_frame)
        button_row.grid(row=5, column=0, pady=15)

        ttk.Button(
            button_row,
            text="🔄 开始转换",
            command=self.convert,
            style='Action.TButton'
        ).pack(side=tk.LEFT, padx=5)

        self.visualize_button = ttk.Button(
            button_row,
            text="📊 显示IES可视化",
            command=self.show_visualization,
            state='disabled'
        )
        self.visualize_button.pack(side=tk.LEFT, padx=5)

        # 进度和日志
        log_frame = ttk.LabelFrame(main_frame, text="转换日志", padding="15")
        log_frame.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        main_frame.rowconfigure(6, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            font=('Consolas', 9),
            wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, sticky=(tk.W, tk.E))

        ttk.Button(button_frame, text="❓ 帮助", command=self.show_help).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="📋 清除日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Label(
            button_frame,
            text="提示：选择EXR文件→输入参数→点击转换",
            style='Info.TLabel',
            foreground='gray'
        ).pack(side=tk.RIGHT)

    def log(self, message):
        """添加日志"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()

    def clear_log(self):
        """清除日志"""
        self.log_text.delete(1.0, tk.END)

    def browse_exr_file(self):
        """浏览EXR文件"""
        filename = filedialog.askopenfilename(
            title="选择EXR文件",
            filetypes=[
                ("EXR文件", "*.exr"),
                ("所有文件", "*.*")
            ]
        )

        if filename:
            self.exr_path = filename
            self.file_path_var.set(filename)
            self.log(f"✅ 已选择文件: {Path(filename).name}")

    def convert(self):
        """执行转换"""
        try:
            # 验证输入
            if not self.exr_path:
                messagebox.showerror("错误", "请先选择EXR文件")
                return

            lumens = float(self.lumens_var.get())
            distance = float(self.distance_var.get())

            if lumens <= 0:
                messagebox.showerror("错误", "流明值必须大于0")
                return

            if distance <= 0:
                messagebox.showerror("错误", "测量距离必须大于0")
                return

            self.clear_log()
            self.log("="*60)
            self.log("开始转换...")
            self.log("="*60)

            # 创建转换器
            self.converter = EXRToIESConverter(measurement_distance=distance)

            # 读取EXR
            self.log(f"\n📖 读取EXR文件: {Path(self.exr_path).name}")
            exr_data = self.converter.read_exr(self.exr_path)
            self.log(f"  ✅ EXR尺寸: {exr_data.shape[1]}×{exr_data.shape[0]}")
            self.log(f"  值域: [{exr_data.min():.6f}, {exr_data.max():.6f}]")

            # 获取IES分辨率
            resolution_name = self.resolution_var.get()
            ies_resolution = self.converter.ies_resolutions[resolution_name]

            # 转换
            self.log(f"\n🔄 转换为IES数据...")
            self.log(f"  IES分辨率: {ies_resolution[0]}×{ies_resolution[1]}")
            self.log(f"  流明值: {lumens} lm")
            self.log(f"  测量距离: {distance} m")

            candela_values, h_angles, v_angles = self.converter.convert_to_ies(
                exr_data, lumens, ies_resolution,
                metadata=None  # metadata不用在这里
            )

            self.log(f"  ✅ 采样完成")
            self.log(f"  坎德拉值域: [{candela_values.min():.2f}, {candela_values.max():.2f}] cd/klm")

            # 准备元数据
            metadata = {
                'manufacturer': self.manufacturer_var.get(),
                'catalog_number': self.catalog_var.get() or 'EXR-GENERATED',
                'luminaire_name': self.luminaire_name_var.get(),
                'lamp_description': self.lamp_desc_var.get(),
                'other_info': self.other_info_var.get(),
                'photometric_type': 1,
                'width': float(self.width_var.get()),
                'length': float(self.length_var.get()),
                'height': float(self.height_var.get()),
            }

            # 选择保存位置
            output_path = filedialog.asksaveasfilename(
                title="保存IES文件",
                defaultextension=".ies",
                filetypes=[("IES文件", "*.ies"), ("所有文件", "*.*")],
                initialfile=Path(self.exr_path).stem + ".ies"
            )

            if not output_path:
                self.log("\n❌ 用户取消保存")
                return

            # 写入IES
            self.log(f"\n💾 写入IES文件...")
            self.converter.write_ies_file(
                output_path, lumens, candela_values,
                h_angles, v_angles, metadata
            )

            file_size = Path(output_path).stat().st_size / 1024
            self.log(f"  ✅ IES文件已保存: {Path(output_path).name}")
            self.log(f"  文件大小: {file_size:.1f} KB")

            # 存储转换数据用于可视化
            self.last_conversion_data = {
                'candela_values': candela_values,
                'h_angles': h_angles,
                'v_angles': v_angles,
                'metadata': {**metadata, 'lumens': lumens}
            }

            # 启用可视化按钮
            self.visualize_button.config(state='normal')

            self.log("\n" + "="*60)
            self.log("✅ 转换完成！")
            self.log("="*60)
            self.log("\n💡 提示: 点击 '📊 显示IES可视化' 按钮查看配光曲线")

            messagebox.showinfo("成功", f"IES文件已生成！\n\n{output_path}\n\n💡 可以点击 '显示IES可视化' 查看配光曲线")

        except ValueError as e:
            error_msg = str(e)
            # 确保错误信息编码正确
            try:
                error_msg = error_msg.encode('utf-8').decode('utf-8')
            except:
                pass
            messagebox.showerror("输入错误", f"请检查输入值:\n{error_msg}")
            self.log(f"\n❌ 错误: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            # 确保错误信息编码正确
            try:
                error_msg = error_msg.encode('utf-8').decode('utf-8')
            except:
                pass
            messagebox.showerror("转换错误", f"转换过程中出错:\n{error_msg}")
            self.log(f"\n❌ 错误: {error_msg}")
            import traceback
            self.log(traceback.format_exc())

    def show_visualization(self):
        """显示IES可视化"""
        if not self.last_conversion_data:
            messagebox.showwarning("提示", "请先完成转换再查看可视化")
            return

        if not self.visualizer.has_matplotlib:
            messagebox.showerror(
                "缺少依赖",
                "需要安装matplotlib才能显示可视化\n\n"
                "请运行以下命令:\n"
                "pip install matplotlib"
            )
            return

        self.log("\n📊 生成可视化图表...")

        try:
            fig, error = self.visualizer.visualize_ies(
                self.last_conversion_data['candela_values'],
                self.last_conversion_data['h_angles'],
                self.last_conversion_data['v_angles'],
                self.last_conversion_data['metadata']
            )

            if error:
                self.log(f"❌ {error}")
                messagebox.showerror("可视化错误", error)
            else:
                self.log("✅ 可视化图表已生成")
                self.visualizer.plt.show()

        except Exception as e:
            self.log(f"❌ 可视化错误: {str(e)}")
            messagebox.showerror("错误", f"生成可视化时出错:\n{str(e)}")

    def show_help(self):
        """显示帮助"""
        help_text = """
【EXR转IES转换器】使用帮助

📖 基本流程:

1. 选择EXR文件
   - 点击"浏览"按钮选择EXR文件
   - 支持Blender/3ds Max/Corona等渲染的EXR

2. 输入转换参数
   ▶ 流明值 (必需)
     - 灯具的总光通量
     - 例如：1000, 1500, 2000
   
   ▶ 测量距离 (关键！)
     - 必须与EXR烘焙时的球体半径一致
     - 错误的距离会导致IES光强不正确
     - 默认：5.0米
   
   ▶ IES分辨率
     - 标准 (72×36)：适合大多数情况
     - 精细 (144×72)：用于高精度要求

3. IES文件头信息（可选）
   - 制造商、产品编号等
   - 都有默认值，可以不修改

4. 点击"开始转换"
   - 选择保存位置
   - 完成转换

5. 📊 查看IES可视化（新功能！）
   - 转换成功后点击"显示IES可视化"
   - 显示6个专业图表：
     ✓ 3D极坐标配光曲线
     ✓ 水平配光图（极坐标）
     ✓ 垂直配光图（C0-C180）
     ✓ 光强分布热图
     ✓ 多平面垂直配光
     ✓ 光度统计信息
   - 需要安装matplotlib库

⚠️ 重要提示:

1. 测量距离必须正确！
   如果EXR是从半径5米的球体烘焙的，
   这里的测量距离就必须输入5.0

2. EXR格式要求
   - Equirectangular全景格式（2:1比例）
   - 球坐标UV映射
   - 32位或16位浮点

3. 流明值可以随意修改
   同一个EXR可以生成不同流明的IES

📦 依赖库:

基础功能：
- numpy（必需）
- OpenEXR（推荐）或 Pillow（备选）

可视化功能（可选）：
- matplotlib
  安装方式: pip install matplotlib

如果不需要可视化，可以不安装matplotlib

❓ 常见问题:

Q: IES在CG软件中太暗/太亮？
A: 检查测量距离是否正确，或修改流明值

Q: 提示无法读取EXR？
A: 安装 OpenEXR 或 Pillow 库

Q: 转换后的IES配光不对？
A: 确认EXR是equirectangular格式

Q: 无法显示可视化？
A: 安装matplotlib库：pip install matplotlib

📊 可视化图表说明:

1. 3D配光曲线：真实的3D空间光强分布
2. 水平配光：俯视图，显示灯具的水平光分布
3. 垂直配光：侧视图，显示主平面的垂直分布
4. 光强热图：伪彩色强度分布，便于观察光斑
5. 多平面对比：8个C平面的垂直分布对比
6. 统计信息：最大/平均光强、光束角、对称性等

📞 支持:
如有问题，请查看完整文档或联系技术支持。

版本: v2.0 (with Visualization)
日期: 2026-01-21
"""

        help_window = tk.Toplevel(self.root)
        help_window.title("使用帮助")
        help_window.geometry("700x850")

        help_text_widget = scrolledtext.ScrolledText(
            help_window,
            font=('Arial', 10),
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        help_text_widget.pack(fill=tk.BOTH, expand=True)
        help_text_widget.insert(1.0, help_text)
        help_text_widget.config(state='disabled')


def main():
    """主函数"""
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
