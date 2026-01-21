"""
模拟参数测试 - 验证修正后的代码
测试各种常见灯具的参数转换
"""

from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter

def print_separator(char="=", length=80):
    print(char * length)

def print_header(title):
    print_separator()
    print(f"  {title}")
    print_separator()

def test_scenario(converter, scenario_name, **kwargs):
    """执行单个测试场景"""
    print(f"\n📍 {scenario_name}")
    print("-" * 80)

    try:
        radiant_watts, method = converter.calculate_radiant_watts(**kwargs)

        # 显示输入参数
        if 'lumens' in kwargs:
            print(f"   输入: {kwargs['lumens']} 流明 | {kwargs['source_type']} | {kwargs.get('color_temp', 4000)}K")
        elif 'electrical_watts' in kwargs:
            print(f"   输入: {kwargs['electrical_watts']} W电功率 | {kwargs['source_type']} | {kwargs.get('color_temp', 4000)}K")

        # 显示计算结果
        print(f"   方法: {method}")
        print(f"   ✅ 结果: {radiant_watts:.4f} W (Radiant Watts)")

        # 显示计算过程
        specs = converter.light_source_specs[kwargs['source_type']]
        if 'lumens' in kwargs:
            efficacy = specs['typical_efficacy']
            print(f"   说明: {kwargs['lumens']} lm ÷ {efficacy} lm/W = {kwargs['lumens']/efficacy:.2f} W 可见光辐射")
        elif 'electrical_watts' in kwargs:
            efficiency = specs['radiant_efficiency']
            print(f"   说明: {kwargs['electrical_watts']} W × {efficiency*100:.0f}% = {kwargs['electrical_watts']*efficiency:.2f} W 总辐射功率")

        return radiant_watts

    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return None

def main():
    converter = LampSpecsToRadiantConverter()

    print("\n")
    print_header("🔬 灯光参数转换模拟测试")
    print(f"测试时间: 2026-01-21")
    print(f"目的: 验证修正后的 lumens → radiant watts 转换")

    # ==================== 测试组1: 从流明计算（推荐方法）====================
    print_header("测试组1: 从流明值计算辐射瓦特 (推荐用于Blender)")

    test_scenario(converter,
                  "案例1.1: 普通LED灯珠 - 1000流明",
                  lumens=1000,
                  source_type="led",
                  color_temp=4000)

    test_scenario(converter,
                  "案例1.2: 高端LED灯珠 - 1500流明",
                  lumens=1500,
                  source_type="led_high_end",
                  color_temp=5000)

    test_scenario(converter,
                  "案例1.3: 白炽灯泡 - 800流明 (相当于60W)",
                  lumens=800,
                  source_type="incandescent",
                  color_temp=2700)

    test_scenario(converter,
                  "案例1.4: 卤素灯 - 1000流明",
                  lumens=1000,
                  source_type="halogen",
                  color_temp=3000)

    test_scenario(converter,
                  "案例1.5: 荧光灯/节能灯 - 1200流明",
                  lumens=1200,
                  source_type="fluorescent",
                  color_temp=4000)

    # ==================== 测试组2: 从电功率计算 ====================
    print("\n")
    print_header("测试组2: 从电功率计算辐射瓦特")

    test_scenario(converter,
                  "案例2.1: 10W LED灯珠",
                  electrical_watts=10,
                  source_type="led",
                  color_temp=4000)

    test_scenario(converter,
                  "案例2.2: 60W 白炽灯泡",
                  electrical_watts=60,
                  source_type="incandescent",
                  color_temp=2700)

    test_scenario(converter,
                  "案例2.3: 100W 白炽灯泡",
                  electrical_watts=100,
                  source_type="incandescent",
                  color_temp=2700)

    test_scenario(converter,
                  "案例2.4: 50W 卤素灯",
                  electrical_watts=50,
                  source_type="halogen",
                  color_temp=3000)

    # ==================== 测试组3: 对比分析 ====================
    print("\n")
    print_header("测试组3: 等效亮度对比（1000流明）")

    results = {}
    for source_type in ["led", "led_high_end", "incandescent", "halogen", "fluorescent"]:
        specs = converter.light_source_specs[source_type]
        result = test_scenario(converter,
                              f"案例3.x: {specs['name']} - 1000流明",
                              lumens=1000,
                              source_type=source_type,
                              color_temp=4000)
        results[source_type] = result

    # ==================== 测试组4: 实际应用场景 ====================
    print("\n")
    print_header("测试组4: 实际应用场景模拟")

    print("\n🏠 场景A: 家庭客厅照明")
    test_scenario(converter,
                  "主灯: LED吸顶灯 - 3000流明",
                  lumens=3000,
                  source_type="led",
                  color_temp=4000)

    print("\n🏢 场景B: 办公室照明")
    test_scenario(converter,
                  "日光灯管: 荧光灯 - 2500流明",
                  lumens=2500,
                  source_type="fluorescent",
                  color_temp=5000)

    print("\n💡 场景C: 台灯/阅读灯")
    test_scenario(converter,
                  "LED台灯: 500流明",
                  lumens=500,
                  source_type="led",
                  color_temp=5000)

    print("\n🎬 场景D: 影视灯光")
    test_scenario(converter,
                  "卤素聚光灯: 150W",
                  electrical_watts=150,
                  source_type="halogen",
                  color_temp=3200)

    # ==================== 测试组5: 色温影响测试 ====================
    print("\n")
    print_header("测试组5: 色温对转换结果的影响")

    print("\n同一LED灯（1000流明）在不同色温下：")
    for temp in [2700, 4000, 5000, 6500]:
        test_scenario(converter,
                      f"色温 {temp}K",
                      lumens=1000,
                      source_type="led",
                      color_temp=temp)

    # ==================== 总结 ====================
    print("\n")
    print_separator()
    print("📊 测试总结")
    print_separator()
    print("\n✅ 所有测试完成！")
    print("\n关键发现:")
    print("  1. 相同流明值下，不同光源类型的辐射瓦特不同")
    print("  2. 光效越高的光源，相同流明需要的辐射瓦特越少")
    print("  3. 从流明计算得到的是「可见光辐射功率」")
    print("  4. 从电功率计算得到的是「总辐射功率」（含红外等）")
    print("\n推荐用法:")
    print("  🎯 在Blender中设置灯光时，优先使用「从流明计算」的方法")
    print("  🎯 流明值可从灯具产品参数或IES文件中获取")
    print("  🎯 这样能更准确地反映人眼感知的亮度")
    print_separator()
    print("\n")

if __name__ == "__main__":
    main()
