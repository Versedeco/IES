"""
EXR to IES Converter - 使用示例
在Blender中运行此脚本

⚠️ 注意：
- 此脚本必须在Blender的脚本编辑器中运行
- bpy 是Blender专用模块，在普通Python环境中会显示导入错误
- 这是正常的，不影响在Blender中的使用

使用方法：
1. 在Blender中打开脚本编辑器
2. 加载此文件
3. 取消注释想要运行的示例函数
4. 点击运行
"""

import bpy  # type: ignore
from exr_to_ies_converter import EXRToIESConverter, LuminaireParameters


def example_basic_usage():
    """基本使用示例 - 单个LED筒灯"""

    print("\n" + "="*70)
    print("  示例1: 基本使用 - LED筒灯")
    print("="*70)

    # 假设场景中有一个名为"Downlight"的灯具
    luminaire = bpy.data.objects.get("Downlight")

    if not luminaire:
        print("❌ 错误：场景中未找到名为'Downlight'的对象")
        print("   请先创建或选择一个灯具对象")
        return

    # 定义灯具参数
    params = LuminaireParameters(
        # 基本信息
        name="LED Downlight 1000lm",
        manufacturer="Custom Lighting Co.",
        catalog_number="DL-1000-4000K",
        description="10W LED Downlight, 60° beam angle",

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
        beam_angle=60,
        photometric_type=1,  # C平面

        # 可选：电功率
        electrical_watts=10.0
    )

    # 创建转换器（标准配置）
    converter = EXRToIESConverter(
        resolution='high',              # 4K EXR
        sphere_density='standard',      # 72×36球体
        cycles_samples=256              # 标准采样
    )

    # 执行完整流程
    success = converter.process_full_workflow(
        luminaire_object=luminaire,
        luminaire_params=params,
        output_exr_path="output/downlight_distribution.exr",
        output_ies_path="output/downlight_1000lm.ies",
        ies_resolution='standard'  # 72×36 IES
    )

    if success:
        print("✅ 转换成功！")
    else:
        print("❌ 转换失败")


def example_high_precision():
    """高精度配置示例 - 汽车大灯"""

    print("\n" + "="*70)
    print("  示例2: 高精度配置 - 汽车大灯")
    print("="*70)

    luminaire = bpy.context.active_object

    if not luminaire:
        print("❌ 错误：请先选择一个灯具对象")
        return

    # 汽车大灯参数
    params = LuminaireParameters(
        name="Car Headlight High Beam",
        manufacturer="Auto Lighting Systems",
        lumens=1500.0,
        source_type="led_high_end",
        color_temp=6000,
        cri=70,
        width=0.12,
        length=0.25,
        height=0.10,
        beam_angle=8,  # 极窄光束
        photometric_type=1
    )

    # 高精度配置
    converter = EXRToIESConverter(
        resolution='ultra',         # 8K EXR
        sphere_density='fine',      # 144×72球体
        cycles_samples=512          # 高采样
    )

    success = converter.process_full_workflow(
        luminaire_object=luminaire,
        luminaire_params=params,
        output_exr_path="output/car_headlight_distribution.exr",
        output_ies_path="output/car_headlight.ies",
        ies_resolution='fine'  # 144×72 IES
    )

    return success


def example_batch_processing():
    """批处理示例 - 生成多个亮度版本"""

    print("\n" + "="*70)
    print("  示例3: 批处理 - 同一灯具的多个亮度版本")
    print("="*70)

    luminaire = bpy.data.objects.get("Pendant_Light")

    if not luminaire:
        print("❌ 错误：场景中未找到名为'Pendant_Light'的对象")
        return

    # 基础参数
    base_params = {
        "name": "LED Pendant Light",
        "manufacturer": "Modern Lighting",
        "source_type": "led",
        "color_temp": 4000,
        "cri": 85,
        "width": 0.20,
        "length": 0.20,
        "height": 0.15,
        "beam_angle": 120,
    }

    # 创建转换器（快速配置）
    converter = EXRToIESConverter(
        resolution='medium',         # 2K EXR（快速）
        sphere_density='standard',
        cycles_samples=128
    )

    # 首先烘焙一次EXR（使用标准1000lm）
    standard_params = LuminaireParameters(
        **base_params,
        lumens=1000.0,
        catalog_number="PL-1000"
    )

    print("\n第1步：烘焙基准EXR...")
    # 只执行到烘焙步骤
    converter.setup_scene()
    radiant_watts, _ = converter.calculate_radiant_watts(standard_params)
    converter.set_light_power(luminaire, radiant_watts)
    sphere = converter.create_measurement_sphere(luminaire, standard_params)
    mat, image = converter.setup_measurement_material(sphere)
    converter.bake_light_distribution(sphere, "output/pendant_base.exr")

    # 读取EXR一次
    exr_data = converter.read_exr_data("output/pendant_base.exr")

    # 生成不同亮度版本的IES
    print("\n第2步：生成不同亮度版本的IES...")
    lumens_variants = [500, 800, 1000, 1200, 1500, 2000]

    for lumens in lumens_variants:
        print(f"\n  生成 {lumens}lm 版本...")

        # 创建对应参数
        params = LuminaireParameters(
            **base_params,
            lumens=float(lumens),
            catalog_number=f"PL-{lumens}"
        )

        # 转换为IES数据
        candela_values, h_angles, v_angles = converter.convert_exr_to_ies_data(
            exr_data, params.lumens, 'standard'
        )

        # 写入IES文件
        converter.write_ies_file(
            f"output/pendant_{lumens}lm.ies",
            params,
            candela_values,
            h_angles,
            v_angles
        )

    print(f"\n✅ 批处理完成！生成了{len(lumens_variants)}个IES文件")
    print("   所有文件共享相同的配光形状，但亮度不同")


def example_custom_configuration():
    """自定义配置示例"""

    print("\n" + "="*70)
    print("  示例4: 自定义配置")
    print("="*70)

    luminaire = bpy.context.active_object

    if not luminaire:
        print("❌ 错误：请先选择一个灯具对象")
        return

    # 自定义参数
    params = LuminaireParameters(
        name="Custom Floodlight",
        manufacturer="Custom",
        lumens=5000.0,
        source_type="led",
        color_temp=5000,
        cri=70,
        width=0.30,
        length=0.25,
        height=0.15,
        beam_angle=45,
        electrical_watts=50.0
    )

    # 完全自定义配置
    converter = EXRToIESConverter(
        resolution='high',              # 4K
        auto_calculate_distance=True,   # 自动计算距离
        measurement_distance=None,      # 或手动指定：5.0
        sphere_density='standard',      # 72×36
        cycles_samples=256
    )

    # 执行
    success = converter.process_full_workflow(
        luminaire_object=luminaire,
        luminaire_params=params,
        output_exr_path="output/custom_floodlight.exr",
        output_ies_path="output/custom_floodlight.ies",
        ies_resolution='standard'
    )

    return success


# ============================================================================
# 快速启动菜单
# ============================================================================

def main_menu():
    """主菜单"""
    print("\n" + "="*70)
    print("  EXR to IES Converter - 使用示例")
    print("="*70)
    print("\n请选择要运行的示例：")
    print("  1. 基本使用 - LED筒灯")
    print("  2. 高精度配置 - 汽车大灯")
    print("  3. 批处理 - 多个亮度版本")
    print("  4. 自定义配置")
    print("\n或直接修改此脚本，调用相应的函数")


if __name__ == "__main__":
    # 运行示例
    # 取消注释下面一行来运行对应的示例

    # example_basic_usage()          # 示例1
    # example_high_precision()       # 示例2
    # example_batch_processing()     # 示例3
    # example_custom_configuration() # 示例4

    main_menu()
