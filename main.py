"""
灯具参数转换为Blender辐射瓦特 - 使用示例

这个脚本展示了如何使用 ProductsParametersToRadiantWatts.py
将灯具厂商提供的流明值或电功率转换为Blender所需的辐射瓦特(Radiant Watts)
"""

from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter


def example_1_basic_usage():
    """示例1：基本使用 - LED灯"""
    print("\n" + "="*70)
    print("示例1：基本使用 - 从流明值转换")
    print("="*70)

    # 创建转换器
    converter = LampSpecsToRadiantConverter()

    # 从流明值计算辐射瓦特
    radiant_watts, method = converter.calculate_radiant_watts(
        lumens=1000,        # 1000流明的LED灯
        source_type="led",  # LED光源
        color_temp=4000     # 4000K色温
    )

    print(f"\n✅ 转换结果：")
    print(f"   输入：1000 lm LED灯，4000K")
    print(f"   输出：{radiant_watts:.2f} W (Radiant Watts)")
    print(f"   方法：{method}")
    print(f"\n💡 在Blender中设置：Light.energy = {radiant_watts:.2f}")


def example_2_from_electrical_watts():
    """示例2：从电功率转换 - 白炽灯"""
    print("\n" + "="*70)
    print("示例2：从电功率转换 - 60W白炽灯")
    print("="*70)

    converter = LampSpecsToRadiantConverter()

    # 从电功率计算
    radiant_watts, method = converter.calculate_radiant_watts(
        electrical_watts=60,      # 60W白炽灯
        source_type="incandescent",
        color_temp=2700
    )

    print(f"\n✅ 转换结果：")
    print(f"   输入：60W 白炽灯，2700K")
    print(f"   输出：{radiant_watts:.2f} W (Radiant Watts)")
    print(f"   方法：{method}")


def example_3_detailed_output():
    """示例3：详细输出 - 使用打印函数"""
    print("\n" + "="*70)
    print("示例3：详细输出")
    print("="*70)

    converter = LampSpecsToRadiantConverter()

    # 计算
    lumens = 1200
    electrical_watts = 12
    source_type = "led"
    color_temp = 5000

    radiant_watts, method = converter.calculate_radiant_watts(
        lumens=lumens,
        electrical_watts=electrical_watts,
        source_type=source_type,
        color_temp=color_temp
    )

    # 使用详细打印函数
    converter.print_conversion_result(
        lumens, electrical_watts, source_type,
        color_temp, radiant_watts, method
    )


def example_4_different_sources():
    """示例4：不同光源类型对比"""
    print("\n" + "="*70)
    print("示例4：不同光源类型对比（相同流明）")
    print("="*70)

    converter = LampSpecsToRadiantConverter()

    # 相同流明，不同光源
    lumens = 1000
    sources = ["led", "led_high_end", "incandescent", "halogen", "fluorescent"]

    print(f"\n相同流明值 {lumens} lm，不同光源的辐射瓦特对比：")
    print("-" * 70)

    for source in sources:
        try:
            radiant_watts, _ = converter.calculate_radiant_watts(
                lumens=lumens,
                source_type=source,
                color_temp=4000
            )

            specs = converter.light_source_specs[source]
            print(f"{specs['name']:15s}: {radiant_watts:6.2f} W (Radiant)")
        except:
            pass


def example_5_color_temp_effect():
    """示例5：色温影响"""
    print("\n" + "="*70)
    print("示例5：色温对辐射瓦特的影响（LED灯）")
    print("="*70)

    converter = LampSpecsToRadiantConverter()

    lumens = 1000
    source_type = "led"
    color_temps = [2700, 3000, 4000, 5000, 6500]

    print(f"\n相同LED灯（{lumens} lm），不同色温的辐射瓦特：")
    print("-" * 70)

    for temp in color_temps:
        radiant_watts, _ = converter.calculate_radiant_watts(
            lumens=lumens,
            source_type=source_type,
            color_temp=temp
        )

        print(f"{temp}K: {radiant_watts:6.2f} W (Radiant)")


def example_6_batch_processing():
    """示例6：批量处理多个灯具"""
    print("\n" + "="*70)
    print("示例6：批量处理")
    print("="*70)

    converter = LampSpecsToRadiantConverter()

    # 定义多个灯具
    lamp_list = [
        {"name": "LED筒灯", "lumens": 1000, "type": "led", "color_temp": 4000},
        {"name": "LED吊灯", "lumens": 1500, "type": "led", "color_temp": 3000},
        {"name": "白炽台灯", "watts": 60, "type": "incandescent", "color_temp": 2700},
        {"name": "卤素射灯", "watts": 50, "type": "halogen", "color_temp": 3000},
        {"name": "节能灯", "lumens": 800, "type": "fluorescent", "color_temp": 4000},
    ]

    # 批量转换
    results = converter.batch_calculate(lamp_list)


def example_7_list_all_types():
    """示例7：显示所有支持的光源类型"""
    print("\n" + "="*70)
    print("示例7：支持的光源类型")
    print("="*70)

    converter = LampSpecsToRadiantConverter()

    print("\n所有支持的光源类型：")
    print("-" * 70)

    for key, specs in converter.light_source_specs.items():
        efficacy_range = specs["luminous_efficacy_range"]
        temp_range = specs["color_temp_range"]
        print(f"\n{key}:")
        print(f"  名称：{specs['name']}")
        print(f"  光效范围：{efficacy_range[0]}-{efficacy_range[1]} lm/W")
        print(f"  典型光效：{specs['typical_efficacy']} lm/W")
        print(f"  色温范围：{temp_range[0]}-{temp_range[1]} K")
        print(f"  显色指数：{specs['cri_range'][0]}-{specs['cri_range'][1]}")


def main():
    """运行所有示例"""
    print("="*70)
    print("  灯具参数转换为Blender辐射瓦特 - 使用示例")
    print("="*70)

    # 运行各个示例
    example_1_basic_usage()
    example_2_from_electrical_watts()
    example_3_detailed_output()
    example_4_different_sources()
    example_5_color_temp_effect()
    example_6_batch_processing()
    example_7_list_all_types()

    print("\n" + "="*70)
    print("  所有示例运行完成！")
    print("="*70)
    print("\n💡 提示：")
    print("   1. 取消注释下面的代码可以单独运行某个示例")
    print("   2. 也可以在命令行使用：")
    print("      python ProductsParametersToRadiantWatts.py --lumens 1000 --type led --temp 4000")


if __name__ == '__main__':
    # 运行所有示例
    main()

    # 或者单独运行某个示例（取消注释）：
    # example_1_basic_usage()
    # example_2_from_electrical_watts()
    # example_3_detailed_output()
    # example_4_different_sources()
    # example_5_color_temp_effect()
    # example_6_batch_processing()
    # example_7_list_all_types()
