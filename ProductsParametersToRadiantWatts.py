import argparse


class LampSpecsToRadiantConverter:
    def __init__(self):
        # 不同光源类型的光谱效率特性
        self.light_source_specs = {
            "led": {
                "name": "LED灯",
                "luminous_efficacy_range": (80, 150),  # lm/W 光效范围
                "typical_efficacy": 100,  # 典型光效
                "radiant_efficiency": 0.35,  # 电能→辐射能效率（现代LED约30-40%）
                "visible_fraction": 0.30,  # 辐射中可见光比例
                "color_temp_range": (2700, 6500),
                "cri_range": (70, 95)
            },
            "led_high_end": {
                "name": "高端LED灯",
                "luminous_efficacy_range": (120, 200),
                "typical_efficacy": 150,
                "radiant_efficiency": 0.45,  # 高端LED效率更高
                "visible_fraction": 0.35,
                "color_temp_range": (2700, 6500),
                "cri_range": (90, 98)
            },
            "incandescent": {
                "name": "白炽灯",
                "luminous_efficacy_range": (10, 20),
                "typical_efficacy": 15,
                "radiant_efficiency": 0.95,  # 几乎全部转为辐射(含热)
                "visible_fraction": 0.08,  # 大部分是红外热辐射（约5-10%可见光）
                "color_temp_range": (2400, 2700),
                "cri_range": (100, 100)
            },
            "halogen": {
                "name": "卤素灯",
                "luminous_efficacy_range": (15, 25),
                "typical_efficacy": 20,
                "radiant_efficiency": 0.90,
                "visible_fraction": 0.05,
                "color_temp_range": (2900, 3200),
                "cri_range": (100, 100)
            },
            "fluorescent": {
                "name": "荧光灯/节能灯",
                "luminous_efficacy_range": (50, 80),
                "typical_efficacy": 65,
                "radiant_efficiency": 0.85,
                "visible_fraction": 0.20,
                "color_temp_range": (2700, 6500),
                "cri_range": (60, 85)
            },
            "metal_halide": {
                "name": "金属卤化物灯",
                "luminous_efficacy_range": (70, 100),
                "typical_efficacy": 85,
                "radiant_efficiency": 0.65,
                "visible_fraction": 0.25,
                "color_temp_range": (3000, 5500),
                "cri_range": (65, 85)
            },
            "high_pressure_sodium": {
                "name": "高压钠灯",
                "luminous_efficacy_range": (80, 140),
                "typical_efficacy": 110,
                "radiant_efficiency": 0.40,
                "visible_fraction": 0.28,
                "color_temp_range": (1900, 2200),
                "cri_range": (20, 25)
            }
        }

        # 色温对光谱效率的影响系数
        self.color_temp_factors = {
            # 色温越低(暖光)，光视效能越低
            2700: 0.85,  # 暖白
            3000: 0.90,  # 中暖
            4000: 1.00,  # 自然白(基准)
            5000: 1.05,  # 日光白
            6500: 1.10  # 冷白
        }

    def get_color_temp_factor(self, color_temp):
        """根据色温获取光谱效率修正系数"""
        # 线性插值
        temps = sorted(self.color_temp_factors.keys())
        if color_temp <= temps[0]:
            return self.color_temp_factors[temps[0]]
        if color_temp >= temps[-1]:
            return self.color_temp_factors[temps[-1]]

        for i in range(len(temps) - 1):
            if temps[i] <= color_temp <= temps[i + 1]:
                t1, t2 = temps[i], temps[i + 1]
                f1, f2 = self.color_temp_factors[t1], self.color_temp_factors[t2]
                # 线性插值
                factor = f1 + (f2 - f1) * (color_temp - t1) / (t2 - t1)
                return factor
        return 1.0

    def lumens_to_radiant_watts(self, lumens, source_type, color_temp=4000):
        """将流明值转换为辐射瓦特（可见光辐射功率）"""
        if source_type not in self.light_source_specs:
            raise ValueError(f"不支持的光源类型: {source_type}")

        specs = self.light_source_specs[source_type]

        # 获取色温修正系数
        temp_factor = self.get_color_temp_factor(color_temp)

        # 修正后的典型光效 (lm/W)
        # 不同光源的光谱分布不同，实际光视效能也不同
        adjusted_efficacy = specs["typical_efficacy"] * temp_factor

        # 理论最大光视效能 683 lm/W (555nm单色光)
        max_luminous_efficacy = 683

        # 计算相对光视效能（相对于理论最大值的比例）
        relative_efficacy = adjusted_efficacy / max_luminous_efficacy

        # 可见光辐射瓦特 = 流明 / (最大光视效能 × 相对光效)
        # 物理关系: lumens = radiant_watts_visible × luminous_efficacy
        # 因此: radiant_watts_visible = lumens / luminous_efficacy
        radiant_watts = lumens / (max_luminous_efficacy * relative_efficacy)

        return radiant_watts

    def electrical_watts_to_radiant_watts(self, electrical_watts, source_type, color_temp=4000):
        """将电功率转换为辐射瓦特（考虑色温影响）"""
        if source_type not in self.light_source_specs:
            raise ValueError(f"不支持的光源类型: {source_type}")

        specs = self.light_source_specs[source_type]

        # 获取色温修正系数
        temp_factor = self.get_color_temp_factor(color_temp)

        # 色温对辐射效率的影响
        # 对于热辐射光源（白炽灯、卤素灯），色温直接影响辐射效率
        # 对于非热辐射光源（LED、荧光灯），色温影响相对较小

        # 调整后的辐射效率
        if source_type in ["incandescent", "halogen"]:
            # 热辐射光源：色温越高，辐射效率越高（但可见光比例变化）
            # 使用色温修正系数来调整
            adjusted_efficiency = specs["radiant_efficiency"] * temp_factor
        else:
            # 非热辐射光源：色温影响较小
            adjusted_efficiency = specs["radiant_efficiency"]

        # 电功率 → 辐射功率
        radiant_watts = electrical_watts * adjusted_efficiency

        return radiant_watts

    def calculate_radiant_watts(self, lumens=None, electrical_watts=None,
                                source_type="led", color_temp=4000):
        """
        综合计算辐射瓦特
        优先使用流明值，如果没有则使用电功率
        """
        if source_type not in self.light_source_specs:
            available_types = ", ".join(self.light_source_specs.keys())
            raise ValueError(f"不支持的光源类型: {source_type}\n可用类型: {available_types}")

        specs = self.light_source_specs[source_type]

        # 验证色温范围
        temp_min, temp_max = specs["color_temp_range"]
        if not (temp_min <= color_temp <= temp_max):
            print(f"⚠️  警告: 色温 {color_temp}K 超出 {specs['name']} 典型范围 ({temp_min}-{temp_max}K)")

        radiant_watts = None
        calculation_method = ""

        if lumens is not None:
            # 方法1: 从流明计算
            radiant_watts = self.lumens_to_radiant_watts(lumens, source_type, color_temp)
            calculation_method = "从流明值计算"

            # 验证合理性 - 反算电功率
            estimated_electrical = lumens / specs["typical_efficacy"]

        elif electrical_watts is not None:
            # 方法2: 从电功率计算
            radiant_watts = self.electrical_watts_to_radiant_watts(electrical_watts, source_type, color_temp)
            calculation_method = "从电功率计算"

            # 验证合理性 - 反算流明
            estimated_lumens = electrical_watts * specs["typical_efficacy"]

        else:
            raise ValueError("必须提供流明值或电功率其中之一")

        return radiant_watts, calculation_method

    def print_conversion_result(self, lumens, electrical_watts, source_type,
                                color_temp, radiant_watts, calculation_method):
        """打印详细的转换结果"""
        specs = self.light_source_specs[source_type]

        print("=" * 70)
        print("灯具规格 → Blender辐射瓦特 转换结果")
        print("=" * 70)

        # 输入参数
        print("📋 输入参数:")
        print(f"   光源类型:     {specs['name']} ({source_type})")
        if lumens:
            print(f"   光通量:       {lumens} lm")
        if electrical_watts:
            print(f"   电功率:       {electrical_watts} W")
        print(f"   色温:         {color_temp} K")

        # 转换结果
        print("\n🔄 转换结果:")
        print(f"   Blender设置:  {radiant_watts:.2f} W (Radiant Watts)")
        print(f"   计算方法:     {calculation_method}")

        # 验证信息
        print(f"\n✅ 验证信息:")
        if lumens:
            estimated_electrical = lumens / specs["typical_efficacy"]
            print(f"   估算电功率:   {estimated_electrical:.1f} W")
            if electrical_watts:
                efficiency = lumens / electrical_watts
                print(f"   实际光效:     {efficiency:.1f} lm/W")
                typical_range = specs["luminous_efficacy_range"]
                if typical_range[0] <= efficiency <= typical_range[1]:
                    print(f"   光效评价:     ✅ 正常 (典型范围: {typical_range[0]}-{typical_range[1]} lm/W)")
                else:
                    print(f"   光效评价:     ⚠️  异常 (典型范围: {typical_range[0]}-{typical_range[1]} lm/W)")

        if electrical_watts and not lumens:
            estimated_lumens = electrical_watts * specs["typical_efficacy"]
            print(f"   估算光通量:   {estimated_lumens:.0f} lm")

        # 使用建议
        print(f"\n💡 使用建议:")
        print(f"   在Blender中设置灯光的 Radiant Watts = {radiant_watts:.2f}")
        print(f"   然后进行HDR烘培，最后使用EXR转IES脚本")
        print("=" * 70)

    def batch_calculate(self, lamp_list):
        """批量计算多个灯具"""
        print("批量转换结果:")
        print("-" * 80)

        results = []
        for i, lamp in enumerate(lamp_list, 1):
            lumens = lamp.get("lumens")
            watts = lamp.get("watts")
            source_type = lamp.get("type", "led")
            color_temp = lamp.get("color_temp", 4000)
            name = lamp.get("name", f"灯具{i}")

            try:
                radiant_watts, method = self.calculate_radiant_watts(
                    lumens, watts, source_type, color_temp)

                results.append({
                    "name": name,
                    "radiant_watts": radiant_watts,
                    "source_type": source_type,
                    "method": method
                })

                print(f"{i:2d}. {name:20s} → {radiant_watts:6.2f}W (Radiant) [{source_type}]")

            except Exception as e:
                print(f"{i:2d}. {name:20s} → 错误: {e}")

        return results


def main():
    parser = argparse.ArgumentParser(
        description='将灯具厂商规格参数转换为Blender辐射瓦特',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
支持的光源类型:
  led              - 普通LED灯
  led_high_end     - 高端LED灯  
  incandescent     - 白炽灯
  halogen          - 卤素灯
  fluorescent      - 荧光灯/节能灯
  metal_halide     - 金属卤化物灯
  high_pressure_sodium - 高压钠灯

使用示例:
  # 从流明计算
  python lamp_to_radiant.py --lumens 1000 --type led --temp 5000

  # 从电功率计算  
  python lamp_to_radiant.py --watts 60 --type incandescent --temp 2700

  # 同时提供流明和电功率(用于验证)
  python lamp_to_radiant.py --lumens 800 --watts 10 --type led --temp 3000
        """)

    parser.add_argument('--lumens', type=float, help='光通量(流明)')
    parser.add_argument('--watts', type=float, help='电功率(瓦特)')
    parser.add_argument('--type', default='led', help='光源类型 (默认: led)')
    parser.add_argument('--temp', type=int, default=4000, help='色温(K, 默认: 4000)')
    parser.add_argument('--list-types', action='store_true', help='显示支持的光源类型')
    parser.add_argument('--batch', help='批量处理配置文件(JSON格式)')

    args = parser.parse_args()

    converter = LampSpecsToRadiantConverter()

    # 显示光源类型
    if args.list_types:
        print("支持的光源类型详细信息:")
        print("=" * 80)
        for key, specs in converter.light_source_specs.items():
            efficacy_range = specs["luminous_efficacy_range"]
            temp_range = specs["color_temp_range"]
            print(f"{key:20s} - {specs['name']}")
            print(f"{'':20s}   光效: {efficacy_range[0]}-{efficacy_range[1]} lm/W")
            print(f"{'':20s}   色温: {temp_range[0]}-{temp_range[1]} K")
            print()
        return 0

    # 批量处理
    if args.batch:
        import json
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                lamp_list = json.load(f)
            converter.batch_calculate(lamp_list)
        except Exception as e:
            print(f"批量处理错误: {e}")
        return 0

    # 单个计算
    if not args.lumens and not args.watts:
        print("错误: 必须提供 --lumens 或 --watts 其中之一")
        return 1

    try:
        radiant_watts, method = converter.calculate_radiant_watts(
            args.lumens, args.watts, args.type, args.temp)

        converter.print_conversion_result(
            args.lumens, args.watts, args.type, args.temp,
            radiant_watts, method)

    except Exception as e:
        print(f"计算错误: {e}")
        return 1

    return 0


# 使用示例
if __name__ == "__main__":
    # 命令行使用示例:
    # python lamp_to_radiant.py --lumens 1000 --type led --temp 5000
    # python lamp_to_radiant.py --watts 60 --type incandescent

    # 代码中直接使用示例:
    # converter = LampSpecsToRadiantConverter()
    # radiant_watts, method = converter.calculate_radiant_watts(
    #     lumens=1200, source_type="led", color_temp=4000)
    # print(f"Blender设置: {radiant_watts:.2f} W")

    exit(main())
