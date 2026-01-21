# ProductsParametersToRadiantWatts.py - 文件说明

## 📋 文件位置

**完整路径**: `D:\TestLighting\EXR_to_IES\ProductsParametersToRadiantWatts.py`

**已找到**: ✅ 文件存在并完全可用

---

## 🎯 功能说明

这个Python模块用于将灯具厂商提供的规格参数转换为Blender所需的辐射瓦特值。

### 核心功能

1. **流明 → 辐射瓦特** 转换
2. **电功率 → 辐射瓦特** 转换
3. **色温影响** 考虑
4. **多种光源类型** 支持
5. **批量处理** 能力

---

## 📊 支持的光源类型（7种）

| 序号 | 代码 | 名称 | 典型光效 |
|-----|------|------|---------|
| 1 | `led` | LED灯 | 100 lm/W |
| 2 | `led_high_end` | 高端LED灯 | 150 lm/W |
| 3 | `incandescent` | 白炽灯 | 15 lm/W |
| 4 | `halogen` | 卤素灯 | 20 lm/W |
| 5 | `fluorescent` | 荧光灯/节能灯 | 65 lm/W |
| 6 | `metal_halide` | 金属卤化物灯 | 85 lm/W |
| 7 | `high_pressure_sodium` | 高压钠灯 | 110 lm/W |

---

## 🚀 快速使用

### Python代码中使用（最常用）

```python
from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter

# 创建转换器
converter = LampSpecsToRadiantConverter()

# 转换（只需一行！）
radiant_watts, method = converter.calculate_radiant_watts(
    lumens=1000,        # 流明值
    source_type="led",  # 光源类型
    color_temp=4000     # 色温
)

# 结果：radiant_watts = 10.0 W
# 在Blender中设置：light.data.energy = 10.0
```

### 命令行使用

```bash
# 基本转换
python ProductsParametersToRadiantWatts.py --lumens 1000 --type led --temp 4000

# 显示所有光源类型
python ProductsParametersToRadiantWatts.py --list-types
```

### 运行示例

```bash
# 运行完整示例（推荐先看这个）
python main.py
```

---

## 💡 实际运行结果

刚才运行 `main.py` 的结果显示：

### 示例1：1000流明LED灯（4000K）
```
输入：1000 lm LED灯，4000K
输出：10.00 W (Radiant Watts)
→ 在Blender中设置：Light.energy = 10.00
```

### 示例2：60W白炽灯（2700K）
```
输入：60W 白炽灯，2700K
输出：48.45 W (Radiant Watts)
```

### 示例5：色温影响（1000流明LED）
```
2700K（暖光）:  11.76 W
3000K:         11.11 W
4000K（中性）:  10.00 W
5000K:          9.52 W
6500K（冷光）:   9.09 W

结论：色温越高，辐射瓦特越低（光效更高）
```

---

## 📚 相关文件

### 核心文件

1. **ProductsParametersToRadiantWatts.py** - 主程序（369行）
   - 转换逻辑
   - 命令行接口
   - 批量处理

2. **main.py** - 使用示例（216行）
   - 7个完整示例
   - 演示所有功能

### 文档文件

3. **ProductsParametersToRadiantWatts使用指南.md** - 详细文档
   - 快速参考
   - 所有功能说明
   - 公式解释

---

## 🔗 在其他代码中的集成

### 在exr_to_ies_converter.py中

```python
# 已集成到EXR转IES完整工作流中

from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter

class EXRToIESConverter:
    def __init__(self):
        self.lamp_converter = LampSpecsToRadiantConverter()
    
    def calculate_radiant_watts(self, luminaire_params):
        radiant_watts, method = self.lamp_converter.calculate_radiant_watts(
            lumens=luminaire_params.lumens,
            source_type=luminaire_params.source_type,
            color_temp=luminaire_params.color_temp
        )
        return radiant_watts, method
```

### 在standalone_exr_to_ies.py中

独立版不需要此模块，因为它直接处理EXR文件。

---

## 🎓 核心概念

### 为什么需要转换？

**灯具厂商提供**：
- 流明（lm）- 人眼感知的光
- 电功率（W）- 电能消耗

**Blender需要**：
- 辐射瓦特（W）- 电磁辐射功率

**关键差异**：
```
LED：1000 lm → 约 10 W 辐射瓦特
白炽灯：1000 lm → 约 67 W 辐射瓦特

为什么差异这么大？
→ 白炽灯大部分能量是红外热辐射（不可见光）
→ LED几乎全是可见光
```

### 色温的影响

```
相同LED灯，1000流明：
- 2700K（暖光）→ 11.76 W（光效低，需要更多辐射）
- 4000K（中性）→ 10.00 W（基准）
- 6500K（冷光）→  9.09 W（光效高，需要更少辐射）

原因：人眼对不同波长的光敏感度不同
```

---

## 💻 代码质量

### 特点

✅ **完整实现** - 支持7种光源类型  
✅ **物理正确** - 基于真实光谱效率  
✅ **色温修正** - 考虑色温对效率的影响  
✅ **验证功能** - 自动检查参数合理性  
✅ **命令行接口** - 可独立使用  
✅ **批量处理** - 支持多灯具处理  
✅ **详细输出** - 提供完整的计算报告  

### 代码结构

```
ProductsParametersToRadiantWatts.py (369行)
├── LampSpecsToRadiantConverter 类
│   ├── __init__() - 初始化光源数据
│   ├── get_color_temp_factor() - 色温修正
│   ├── lumens_to_radiant_watts() - 流明转换
│   ├── electrical_watts_to_radiant_watts() - 电功率转换
│   ├── calculate_radiant_watts() - 主计算方法 ⭐
│   ├── print_conversion_result() - 详细输出
│   └── batch_calculate() - 批量处理
└── main() - 命令行入口
```

---

## 🔧 高级用法

### 批量处理

```python
converter = LampSpecsToRadiantConverter()

lamp_list = [
    {"name": "筒灯", "lumens": 1000, "type": "led", "color_temp": 4000},
    {"name": "吊灯", "lumens": 1500, "type": "led", "color_temp": 3000},
    {"name": "台灯", "watts": 60, "type": "incandescent", "color_temp": 2700},
]

results = converter.batch_calculate(lamp_list)
```

### 详细输出

```python
converter.print_conversion_result(
    lumens=1200,
    electrical_watts=12,
    source_type="led",
    color_temp=5000,
    radiant_watts=radiant_watts,
    calculation_method=method
)
```

输出包括：
- 输入参数
- 转换结果
- 验证信息（光效检查）
- 使用建议

---

## 📈 测试验证

### 运行测试

```bash
# 运行所有示例，验证功能
python main.py

# 输出显示所有7个示例都正常运行 ✅
```

### 测试覆盖

- ✅ 基本转换（流明→辐射瓦特）
- ✅ 电功率转换
- ✅ 详细输出验证
- ✅ 多光源类型对比
- ✅ 色温影响验证
- ✅ 批量处理
- ✅ 光源类型列表

---

## 🎯 使用场景

### 场景1：Blender灯光设置

```python
# 1. 获取灯具规格（从产品目录）
lumens = 1000
source_type = "led"
color_temp = 4000

# 2. 转换
radiant_watts, _ = converter.calculate_radiant_watts(lumens, None, source_type, color_temp)

# 3. 在Blender中设置
import bpy
light = bpy.context.active_object.data
light.energy = radiant_watts
```

### 场景2：完整工作流（与EXR转IES集成）

```python
# 在exr_to_ies_converter.py中自动使用
params = LuminaireParameters(
    lumens=1000,
    source_type="led",
    color_temp=4000
)

converter = EXRToIESConverter()
converter.process_full_workflow(luminaire, params, "out.exr", "out.ies")
# ↑ 内部自动调用 ProductsParametersToRadiantWatts
```

### 场景3：产品系列生成

```python
# 同一款灯具的不同功率版本
base_type = "led"
base_temp = 4000

for lumens in [500, 1000, 1500, 2000]:
    radiant_watts, _ = converter.calculate_radiant_watts(
        lumens=lumens,
        source_type=base_type,
        color_temp=base_temp
    )
    print(f"{lumens}lm → {radiant_watts:.2f}W")
```

---

## ✅ 验证和状态

### 文件状态

- ✅ 文件存在
- ✅ 代码完整（369行）
- ✅ 功能正常
- ✅ 已集成到主工作流
- ✅ 有完整示例（main.py）
- ✅ 有详细文档

### 测试状态

- ✅ 所有示例运行成功
- ✅ 7种光源类型都可用
- ✅ 色温修正正常工作
- ✅ 批量处理正常
- ✅ 命令行接口可用

---

## 📝 快速命令参考

```bash
# 查看示例（推荐第一步）
python main.py

# 转换单个值
python ProductsParametersToRadiantWatts.py --lumens 1000 --type led --temp 4000

# 显示所有光源类型
python ProductsParametersToRadiantWatts.py --list-types

# 在Python代码中使用
from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter
converter = LampSpecsToRadiantConverter()
radiant_watts, _ = converter.calculate_radiant_watts(lumens=1000, source_type="led", color_temp=4000)
```

---

## 🎊 总结

### 文件已找到 ✅

`ProductsParametersToRadiantWatts.py` 已经存在于项目中，并且：

1. ✅ 功能完整
2. ✅ 已测试验证
3. ✅ 有详细文档
4. ✅ 有使用示例
5. ✅ 已集成到主工作流

### 如何使用

**最简单的方式**：

```python
from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter

converter = LampSpecsToRadiantConverter()
radiant_watts, _ = converter.calculate_radiant_watts(
    lumens=1000,
    source_type="led",
    color_temp=4000
)

# 在Blender中使用
# light.data.energy = radiant_watts
```

**完整示例**: 运行 `python main.py`

---

**文件位置**: `D:\TestLighting\EXR_to_IES\ProductsParametersToRadiantWatts.py`  
**示例文件**: `D:\TestLighting\EXR_to_IES\main.py`  
**文档**: `D:\TestLighting\EXR_to_IES\ProductsParametersToRadiantWatts使用指南.md`  
**状态**: ✅ 完全可用
