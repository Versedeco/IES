# ProductsParametersToRadiantWatts - 快速参考

## 📋 文件说明

**文件名**: `ProductsParametersToRadiantWatts.py`

**功能**: 将灯具厂商提供的规格参数（流明值或电功率）转换为Blender所需的辐射瓦特(Radiant Watts)

---

## 🚀 快速使用

### 方法1：Python代码中使用

```python
from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter

# 创建转换器
converter = LampSpecsToRadiantConverter()

# 从流明值转换
radiant_watts, method = converter.calculate_radiant_watts(
    lumens=1000,        # 流明值
    source_type="led",  # 光源类型
    color_temp=4000     # 色温（K）
)

print(f"Blender设置: Light.energy = {radiant_watts:.2f}")
```

### 方法2：命令行使用

```bash
# 从流明值转换
python ProductsParametersToRadiantWatts.py --lumens 1000 --type led --temp 4000

# 从电功率转换
python ProductsParametersToRadiantWatts.py --watts 60 --type incandescent --temp 2700

# 同时提供流明和电功率（用于验证）
python ProductsParametersToRadiantWatts.py --lumens 800 --watts 10 --type led --temp 3000

# 显示支持的光源类型
python ProductsParametersToRadiantWatts.py --list-types
```

### 方法3：运行示例

```bash
# 运行main.py查看所有使用示例
python main.py
```

---

## 📊 支持的光源类型

| 类型 | 代码名称 | 光效范围 | 典型光效 | 色温范围 |
|-----|---------|---------|---------|---------|
| **LED灯** | `led` | 80-150 lm/W | 100 lm/W | 2700-6500K |
| **高端LED** | `led_high_end` | 120-200 lm/W | 150 lm/W | 2700-6500K |
| **白炽灯** | `incandescent` | 10-20 lm/W | 15 lm/W | 2400-2700K |
| **卤素灯** | `halogen` | 15-25 lm/W | 20 lm/W | 2900-3200K |
| **荧光灯** | `fluorescent` | 50-80 lm/W | 65 lm/W | 2700-6500K |
| **金卤灯** | `metal_halide` | 70-100 lm/W | 85 lm/W | 3000-5500K |
| **高压钠灯** | `high_pressure_sodium` | 80-140 lm/W | 110 lm/W | 1900-2200K |

---

## 💡 实际应用示例

### 示例1：LED筒灯

```python
converter = LampSpecsToRadiantConverter()

# 灯具规格：1000流明，LED，4000K
radiant_watts, _ = converter.calculate_radiant_watts(
    lumens=1000,
    source_type="led",
    color_temp=4000
)

# 结果：约 6.15 W
# 在Blender中设置：light.data.energy = 6.15
```

### 示例2：60W白炽灯泡

```python
# 灯具规格：60W电功率，白炽灯，2700K
radiant_watts, _ = converter.calculate_radiant_watts(
    electrical_watts=60,
    source_type="incandescent",
    color_temp=2700
)

# 结果：约 57 W（几乎全部转为辐射，但大部分是红外热）
# 在Blender中设置：light.data.energy = 57
```

### 示例3：节能灯

```python
# 灯具规格：800流明，荧光灯，4000K
radiant_watts, _ = converter.calculate_radiant_watts(
    lumens=800,
    source_type="fluorescent",
    color_temp=4000
)

# 结果：约 6.5 W
```

---

## 🔍 核心方法说明

### `calculate_radiant_watts()`

**最常用的方法**

```python
radiant_watts, method = converter.calculate_radiant_watts(
    lumens=None,              # 流明值（可选）
    electrical_watts=None,    # 电功率（可选）
    source_type="led",        # 光源类型（必需）
    color_temp=4000          # 色温（必需）
)
```

**参数**：
- `lumens` - 总流明值（优先使用）
- `electrical_watts` - 电功率（备选）
- `source_type` - 光源类型（见上表）
- `color_temp` - 色温（K）

**返回**：
- `radiant_watts` - 辐射瓦特值（用于Blender）
- `method` - 计算方法描述

**注意**：必须提供 `lumens` 或 `electrical_watts` 其中之一

---

## 📐 核心概念

### 什么是辐射瓦特？

**辐射瓦特 (Radiant Watts)**：电磁辐射功率，包括可见光和不可见光（如红外）

在Blender中：
- `Light.energy` 的单位就是辐射瓦特
- 不同光源的辐射瓦特差异很大

### 为什么需要转换？

灯具厂商提供的参数：
- 流明（lm）- 可见光通量
- 电功率（W）- 电能消耗

Blender需要的参数：
- 辐射瓦特（W）- 辐射功率

**关键差异**：
```
LED灯：1000 lm ≈ 6 W 辐射瓦特
白炽灯：1000 lm ≈ 60 W 辐射瓦特（大部分是热）
```

### 色温的影响

色温影响光谱分布，进而影响：
- 光视效能（光效）
- 辐射效率

**示例**（LED，1000流明）：
- 2700K（暖光）→ 约 7.2 W 辐射瓦特
- 4000K（中性光）→ 约 6.1 W 辐射瓦特
- 6500K（冷光）→ 约 5.6 W 辐射瓦特

---

## 🎯 常见场景

### 场景1：已知流明值（最常见）

```python
# 产品规格：1200流明 LED灯
radiant_watts, _ = converter.calculate_radiant_watts(
    lumens=1200,
    source_type="led",
    color_temp=4000
)
```

### 场景2：已知电功率

```python
# 产品规格：10W LED灯
radiant_watts, _ = converter.calculate_radiant_watts(
    electrical_watts=10,
    source_type="led",
    color_temp=4000
)
```

### 场景3：同时提供（用于验证）

```python
# 产品规格：800流明，8W LED灯
radiant_watts, _ = converter.calculate_radiant_watts(
    lumens=800,
    electrical_watts=8,
    source_type="led",
    color_temp=4000
)

# 会验证光效是否合理：800/8 = 100 lm/W
```

### 场景4：批量处理

```python
lamp_list = [
    {"name": "筒灯", "lumens": 1000, "type": "led", "color_temp": 4000},
    {"name": "吊灯", "lumens": 1500, "type": "led", "color_temp": 3000},
    {"name": "台灯", "watts": 60, "type": "incandescent", "color_temp": 2700},
]

results = converter.batch_calculate(lamp_list)
```

---

## 🔧 高级功能

### 获取色温修正系数

```python
temp_factor = converter.get_color_temp_factor(5000)
# 返回：1.05（高色温光效略高）
```

### 详细输出

```python
converter.print_conversion_result(
    lumens=1000,
    electrical_watts=10,
    source_type="led",
    color_temp=4000,
    radiant_watts=radiant_watts,
    calculation_method=method
)
# 输出详细的转换报告，包括验证信息
```

---

## ⚠️ 注意事项

### 1. 色温范围

使用超出典型范围的色温会有警告：

```python
# LED典型色温：2700-6500K
# 使用7000K会警告
radiant_watts, _ = converter.calculate_radiant_watts(
    lumens=1000,
    source_type="led",
    color_temp=7000  # ⚠️ 超出范围
)
```

### 2. 光效验证

如果同时提供流明和电功率，会验证光效：

```python
# 光效 = 1000 / 5 = 200 lm/W
# 超出LED典型范围（80-150），会有警告
converter.calculate_radiant_watts(
    lumens=1000,
    electrical_watts=5,  # ⚠️ 光效过高
    source_type="led"
)
```

### 3. 白炽灯色温影响

白炽灯的色温直接影响辐射效率：

```python
# 60W白炽灯，不同色温结果不同
# 2700K（标准）：约 57 W 辐射瓦特
# 2400K（低）：约 54 W 辐射瓦特
```

---

## 📚 相关文档

- `main.py` - 完整的使用示例（7个示例）
- `exr_to_ies_converter.py` - 集成了此模块的完整转换器
- `使用指南.md` - 完整的EXR到IES转换指南

---

## 💻 集成到其他代码

### 在exr_to_ies_converter中的使用

```python
from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter

# 在EXRToIESConverter类中
def calculate_radiant_watts(self, luminaire_params):
    """计算辐射瓦数"""
    if self.lamp_converter is None:
        # 简化计算
        radiant_watts = luminaire_params.lumens / 100.0
    else:
        # 使用完整计算
        radiant_watts, method = self.lamp_converter.calculate_radiant_watts(
            lumens=luminaire_params.lumens,
            source_type=luminaire_params.source_type,
            color_temp=luminaire_params.color_temp
        )
    return radiant_watts
```

---

## 🎓 公式说明

### 核心转换公式

```
辐射瓦特 = 流明 / (最大光视效能 × 相对光效)

其中：
- 最大光视效能 = 683 lm/W（555nm单色光）
- 相对光效 = 实际光效 / 最大光视效能
```

### 色温修正

```
调整后光效 = 典型光效 × 色温修正系数

色温修正系数：
- 2700K: 0.85（暖光，光效低）
- 4000K: 1.00（基准）
- 6500K: 1.10（冷光，光效高）
```

---

## ✅ 总结

### 最常用的代码

```python
from ProductsParametersToRadiantWatts import LampSpecsToRadiantConverter

converter = LampSpecsToRadiantConverter()

# 99%的情况下，你只需要这一行
radiant_watts, _ = converter.calculate_radiant_watts(
    lumens=1000,        # 从产品规格获取
    source_type="led",  # LED/白炽/卤素/荧光
    color_temp=4000     # 从产品规格获取
)

# 然后在Blender中使用
# light.data.energy = radiant_watts
```

### 快速测试

```bash
# 命令行快速测试
python ProductsParametersToRadiantWatts.py --lumens 1000 --type led --temp 4000

# 查看所有示例
python main.py
```

---

**文件位置**: `D:\TestLighting\EXR_to_IES\ProductsParametersToRadiantWatts.py`  
**示例文件**: `D:\TestLighting\EXR_to_IES\main.py`  
**版本**: 1.0  
**日期**: 2026-01-21
