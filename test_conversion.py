"""测试转换脚本的正确性"""
from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter

def test_calculations():
    converter = LampSpecsToRadiantConverter()
    
    print("=" * 70)
    print("测试案例 - 验证修正后的计算逻辑")
    print("=" * 70)
    
    # 测试1: LED灯 1000流明
    print("\n测试1: LED灯 1000流明")
    radiant_watts, method = converter.calculate_radiant_watts(
        lumens=1000, source_type="led", color_temp=4000)
    print(f"结果: {radiant_watts:.2f} W (Radiant Watts)")
    print(f"说明: 1000流明 ÷ 100 lm/W = {1000/100:.1f} W 可见光辐射功率")
    
    # 测试2: 白炽灯 800流明
    print("\n测试2: 白炽灯 800流明")
    radiant_watts, method = converter.calculate_radiant_watts(
        lumens=800, source_type="incandescent", color_temp=2700)
    print(f"结果: {radiant_watts:.2f} W (Radiant Watts)")
    print(f"说明: 800流明 ÷ 15 lm/W = {800/15:.1f} W 可见光辐射功率")
    
    # 测试3: 从电功率计算 - 10W LED
    print("\n测试3: 10W LED灯 (从电功率计算)")
    radiant_watts, method = converter.calculate_radiant_watts(
        electrical_watts=10, source_type="led", color_temp=4000)
    print(f"结果: {radiant_watts:.2f} W (Radiant Watts)")
    print(f"说明: 10W × 35% 辐射效率 = {10*0.35:.2f} W 总辐射功率")
    
    # 测试4: 60W 白炽灯 (从电功率计算)
    print("\n测试4: 60W 白炽灯 (从电功率计算)")
    radiant_watts, method = converter.calculate_radiant_watts(
        electrical_watts=60, source_type="incandescent", color_temp=2700)
    print(f"结果: {radiant_watts:.2f} W (Radiant Watts)")
    print(f"说明: 60W × 95% 辐射效率 = {60*0.95:.1f} W 总辐射功率")
    
    # 测试5: 验证一致性 - 同时提供流明和电功率
    print("\n测试5: 验证一致性 - 10W LED @ 100 lm/W = 1000流明")
    radiant_from_lumens, _ = converter.calculate_radiant_watts(
        lumens=1000, source_type="led", color_temp=4000)
    radiant_from_watts, _ = converter.calculate_radiant_watts(
        electrical_watts=10, source_type="led", color_temp=4000)
    print(f"从流明计算: {radiant_from_lumens:.2f} W")
    print(f"从电功率计算: {radiant_from_watts:.2f} W")
    print(f"差异: 这两个值可能不同，因为:")
    print(f"  - 流明法计算的是「可见光」辐射功率")
    print(f"  - 电功率法计算的是「总」辐射功率(含红外、紫外等)")
    
    print("\n" + "=" * 70)
    print("✅ 所有测试完成！")
    print("=" * 70)

if __name__ == "__main__":
    test_calculations()
