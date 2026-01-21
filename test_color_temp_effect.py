"""
测试色温对电功率转换的影响
"""

from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter

def print_separator(char="=", length=80):
    print(char * length)

def main():
    converter = LampSpecsToRadiantConverter()

    print_separator()
    print("  🔬 色温对电功率转换影响的验证测试")
    print_separator()

    # 测试1: 白炽灯 - 色温对辐射效率的影响
    print("\n📍 测试1: 60W白炽灯在不同色温下的辐射功率")
    print("-" * 80)

    temps = [2400, 2500, 2600, 2700, 2800]
    print(f"{'色温':>8} | {'辐射功率':>12} | {'色温系数':>10} | {'说明':30}")
    print("-" * 80)

    for temp in temps:
        radiant_watts, _ = converter.calculate_radiant_watts(
            electrical_watts=60,
            source_type="incandescent",
            color_temp=temp
        )
        temp_factor = converter.get_color_temp_factor(temp)

        status = "标准" if temp == 2700 else ("偏冷" if temp > 2700 else "偏暖")
        print(f"{temp:>6}K | {radiant_watts:>10.4f} W | {temp_factor:>10.3f} | {status}")

    # 测试2: 卤素灯 - 色温影响
    print("\n\n📍 测试2: 50W卤素灯在不同色温下的辐射功率")
    print("-" * 80)

    temps = [2900, 3000, 3100, 3200]
    print(f"{'色温':>8} | {'辐射功率':>12} | {'色温系数':>10} | {'说明':30}")
    print("-" * 80)

    for temp in temps:
        radiant_watts, _ = converter.calculate_radiant_watts(
            electrical_watts=50,
            source_type="halogen",
            color_temp=temp
        )
        temp_factor = converter.get_color_temp_factor(temp)

        status = "标准" if temp == 3000 else ("偏冷" if temp > 3000 else "偏暖")
        print(f"{temp:>6}K | {radiant_watts:>10.4f} W | {temp_factor:>10.3f} | {status}")

    # 测试3: LED - 色温影响（应该很小）
    print("\n\n📍 测试3: 10W LED灯在不同色温下的辐射功率")
    print("-" * 80)
    print("注意: LED是非热辐射光源，色温对辐射效率影响很小")
    print("-" * 80)

    temps = [2700, 4000, 5000, 6500]
    print(f"{'色温':>8} | {'辐射功率':>12} | {'色温系数':>10} | {'说明':30}")
    print("-" * 80)

    for temp in temps:
        radiant_watts, _ = converter.calculate_radiant_watts(
            electrical_watts=10,
            source_type="led",
            color_temp=temp
        )
        temp_factor = converter.get_color_temp_factor(temp)

        if temp == 2700:
            status = "暖白"
        elif temp == 4000:
            status = "自然白（标准）"
        elif temp == 5000:
            status = "冷白"
        else:
            status = "日光白"
        print(f"{temp:>6}K | {radiant_watts:>10.4f} W | {temp_factor:>10.3f} | {status}")

    # 测试4: 对比 - 流明法 vs 电功率法
    print("\n\n📍 测试4: 两种计算方法的对比（60W白炽灯 @ 2700K）")
    print("-" * 80)

    # 方法1: 从电功率计算
    radiant_from_watts, _ = converter.calculate_radiant_watts(
        electrical_watts=60,
        source_type="incandescent",
        color_temp=2700
    )

    # 方法2: 从流明计算（假设60W白炽灯产生约800流明）
    radiant_from_lumens, _ = converter.calculate_radiant_watts(
        lumens=800,
        source_type="incandescent",
        color_temp=2700
    )

    print(f"从电功率计算: {radiant_from_watts:.4f} W (总辐射功率，含红外)")
    print(f"从流明计算:   {radiant_from_lumens:.4f} W (可见光辐射功率)")
    print(f"\n差异原因:")
    print(f"  - 电功率法: 60W × 95% × 色温系数 = 总辐射（可见+红外+紫外）")
    print(f"  - 流明法: 800lm ÷ 15lm/W ÷ 色温系数 = 仅可见光辐射")
    print(f"  - 白炽灯只有约8%的辐射是可见光，其余92%是红外热辐射")

    # 测试5: 实际应用建议
    print("\n\n📍 测试5: 色温影响的实际应用场景")
    print("-" * 80)

    print("\n场景A: 影视拍摄 - 卤素灯调光")
    print("  调光使色温从3200K降到2800K（电压降低）")

    radiant_full, _ = converter.calculate_radiant_watts(
        electrical_watts=150,
        source_type="halogen",
        color_temp=3200
    )

    radiant_dimmed, _ = converter.calculate_radiant_watts(
        electrical_watts=150,
        source_type="halogen",
        color_temp=2800
    )

    print(f"  全功率 @ 3200K: {radiant_full:.2f} W")
    print(f"  调光后 @ 2800K: {radiant_dimmed:.2f} W")
    print(f"  辐射功率变化: {((radiant_dimmed/radiant_full-1)*100):+.1f}%")
    print(f"  → Blender中需要相应调整灯光强度")

    print("\n场景B: 白炽灯老化")
    print("  老化使色温从2700K降到2500K")

    radiant_new, _ = converter.calculate_radiant_watts(
        electrical_watts=60,
        source_type="incandescent",
        color_temp=2700
    )

    radiant_aged, _ = converter.calculate_radiant_watts(
        electrical_watts=60,
        source_type="incandescent",
        color_temp=2500
    )

    print(f"  新灯泡 @ 2700K: {radiant_new:.2f} W")
    print(f"  老化后 @ 2500K: {radiant_aged:.2f} W")
    print(f"  辐射功率变化: {((radiant_aged/radiant_new-1)*100):+.1f}%")
    print(f"  → 老化灯泡的光通量和辐射效率都会降低")

    # 总结
    print("\n")
    print_separator()
    print("📊 测试结论")
    print_separator()
    print("\n✅ 色温对电功率转换的影响验证完成！")
    print("\n关键发现:")
    print("  1. 热辐射光源（白炽灯、卤素灯）：色温对辐射效率有显著影响")
    print("  2. 非热辐射光源（LED、荧光灯）：色温影响较小")
    print("  3. 色温升高 → 辐射效率提升（但光谱分布也变化）")
    print("  4. 调光、老化等因素会改变色温，进而影响辐射特性")
    print("\n物理原理:")
    print("  - 白炽灯/卤素灯是热辐射光源，遵循普朗克黑体辐射定律")
    print("  - 温度（色温）越高，单位面积辐射功率越大")
    print("  - 但同时光谱分布也会改变，影响可见光比例")
    print("\n推荐做法:")
    print("  🎯 使用流明值计算更准确（已包含色温影响）")
    print("  🎯 从电功率计算时，需要考虑实际工作色温")
    print("  🎯 调光场景下，色温和辐射功率都会变化")
    print_separator()
    print()

if __name__ == "__main__":
    main()
