# IES文件流明值修改指南

## 🎯 核心发现

**是的！修改IES文件头部的流明值，CG软件中的灯光亮度会相应改变。**

这是因为：
```
实际光强 = (cd/klm 配光数据) × (总流明值 / 1000)

只要改变总流明值，实际光强就按比例缩放。
```

---

## 📋 IES文件结构

### 关键行位置

```
IESNA:LM-63-2002                    ← 第1行：标准版本
[MANUFAC] Manufacturer Name         ← 可选元数据
[LUMCAT] Catalog Number
...
TILT=NONE                           ← TILT行
1  1000  1.0  72  36  1  2  1.0  1.0  1.0   ← **光度数据行**（关键！）
   ↑
   这个值是总流明（lm）

解析：
位置1: 灯具数量 (通常为1)
位置2: 总流明值 ← **要修改的就是这个！**
位置3: 倍增因子 (通常为1.0)
位置4: 水平角数量
位置5: 垂直角数量
位置6: 光度类型
位置7: 单位类型
位置8-10: 灯具尺寸
```

---

## 🛠️ 手动修改方法

### 方法1：文本编辑器

```bash
# 1. 用任意文本编辑器打开IES文件
notepad luminaire.ies

# 2. 找到光度数据行（TILT=NONE的下一行）
TILT=NONE
1 1000 1.0 72 36 1 2 1.0 1.0 1.0
  ^^^^
  
# 3. 修改流明值
1 2000 1.0 72 36 1 2 1.0 1.0 1.0
  ^^^^
  改为2000（翻倍亮度）

# 4. 保存文件

# 5. 在CG软件中重新加载IES
# 灯光亮度会翻倍！
```

### 方法2：使用Python脚本（推荐）

```python
def modify_ies_lumens(input_ies, output_ies, new_lumens):
    """
    修改IES文件的流明值
    
    Args:
        input_ies: 输入IES文件路径
        output_ies: 输出IES文件路径
        new_lumens: 新的流明值
    """
    with open(input_ies, 'r') as f:
        lines = f.readlines()
    
    # 查找光度数据行
    for i, line in enumerate(lines):
        if line.strip() == 'TILT=NONE':
            # 下一行是光度数据行
            photometric_line = lines[i + 1]
            values = photometric_line.split()
            
            # 修改流明值（第2个值，索引1）
            old_lumens = float(values[1])
            values[1] = str(new_lumens)
            
            # 重新组合
            lines[i + 1] = ' '.join(values) + '\n'
            
            print(f"✅ 流明值已修改: {old_lumens} lm → {new_lumens} lm")
            print(f"   亮度变化: {new_lumens/old_lumens:.1f}x")
            break
    
    # 写入新文件
    with open(output_ies, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ 已保存到: {output_ies}")

# 使用示例
modify_ies_lumens(
    input_ies="downlight_1000lm.ies",
    output_ies="downlight_2000lm.ies",
    new_lumens=2000
)
```

---

## 🎬 在不同CG软件中的效果

### Blender (Cycles/EEVEE)

```python
# Blender会正确读取流明值并缩放光强

# 原始IES：1000 lm
light.data.node_tree.nodes["IES Texture"].filepath = "luminaire_1000lm.ies"
# → 渲染亮度：基准

# 修改后IES：2000 lm（其他数据不变）
light.data.node_tree.nodes["IES Texture"].filepath = "luminaire_2000lm.ies"
# → 渲染亮度：翻倍 ✅
```

### 3ds Max (V-Ray/Corona)

```
V-Ray IES Light:
- 加载 luminaire_1000lm.ies → 亮度 100%
- 加载 luminaire_2000lm.ies → 亮度自动变为 200% ✅

Corona Light (IES):
- 同样会根据IES流明值自动调整
```

### Unreal Engine

```cpp
// Unreal的IES Profile也会正确解析流明值
// 光强会按IES中的流明值缩放

IESTexture->Brightness = (cd_per_klm / 1000) × lumens_from_ies
```

---

## 🔬 验证测试

### 测试程序

```python
import re

def analyze_ies_file(ies_path):
    """分析IES文件的关键参数"""
    with open(ies_path, 'r') as f:
        content = f.read()
    
    # 查找TILT行后的光度数据
    match = re.search(r'TILT=NONE\s+([\d\.\s]+)', content)
    if match:
        values = match.group(1).split()
        
        print(f"📄 文件: {ies_path}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  灯具数量:     {values[0]}")
        print(f"  总流明:       {values[1]} lm  ← 关键")
        print(f"  倍增因子:     {values[2]}")
        print(f"  水平角数:     {values[3]}")
        print(f"  垂直角数:     {values[4]}")
        print(f"  光度类型:     {values[5]}")
        print(f"  单位类型:     {values[6]}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        
        return float(values[1])
    
    return None

# 对比测试
print("🔬 IES文件对比分析\n")

lumens_1 = analyze_ies_file("downlight_1000lm.ies")
lumens_2 = analyze_ies_file("downlight_2000lm.ies")

if lumens_1 and lumens_2:
    ratio = lumens_2 / lumens_1
    print(f"📊 亮度比例: {ratio:.2f}x")
    print(f"   当在CG软件中使用这两个IES时，")
    print(f"   第二个的亮度将是第一个的 {ratio:.1f} 倍")
```

---

## 💡 实际应用场景

### 场景1：快速生成系列产品IES

```python
# 同一款灯具的不同功率版本

base_ies = "LED_downlight_base.ies"  # 基准版本

# 生成系列产品
for lumens in [500, 800, 1000, 1200, 1500, 2000]:
    modify_ies_lumens(
        input_ies=base_ies,
        output_ies=f"LED_downlight_{lumens}lm.ies",
        new_lumens=lumens
    )

结果：
✅ LED_downlight_500lm.ies   → 50% 亮度
✅ LED_downlight_1000lm.ies  → 100% 亮度（基准）
✅ LED_downlight_2000lm.ies  → 200% 亮度

所有文件配光形状相同，只是亮度不同！
```

### 场景2：调光模拟

```python
# 模拟调光器效果

full_brightness = "luminaire_full.ies"  # 1000 lm

# 生成不同调光级别
dimming_levels = {
    "100%": 1000,
    "75%": 750,
    "50%": 500,
    "25%": 250,
}

for level, lumens in dimming_levels.items():
    modify_ies_lumens(
        input_ies=full_brightness,
        output_ies=f"luminaire_dim_{level}.ies",
        new_lumens=lumens
    )

# 在动画中切换不同的IES文件
# 实现调光效果
```

### 场景3：灯具老化模拟

```python
# 模拟LED光衰（流明维持率）

new_lamp = "LED_lamp_new.ies"  # 1000 lm

# 不同使用年限的光衰
aging_stages = {
    "new": 1.00,      # 100% 新灯
    "1year": 0.95,    # 95% 光衰5%
    "3years": 0.85,   # 85% 光衰15%
    "5years": 0.70,   # 70% 光衰30%
}

base_lumens = 1000
for stage, ratio in aging_stages.items():
    modify_ies_lumens(
        input_ies=new_lamp,
        output_ies=f"LED_lamp_{stage}.ies",
        new_lumens=int(base_lumens * ratio)
    )

# 在渲染中使用不同阶段的IES
# 可视化灯具老化效果
```

---

## ⚠️ 重要注意事项

### 1. 配光数据不变

```
修改流明值时：
✅ 总亮度改变
✅ 各方向光强按比例缩放
❌ 配光形状（cd/klm）不变
❌ 光束角不变
❌ 截止角不变

示例：
原始 1000 lm:
  θ=0°: 5000 cd
  θ=30°: 3000 cd
  光束角: 60°

修改为 2000 lm:
  θ=0°: 10000 cd  ← 翻倍
  θ=30°: 6000 cd  ← 翻倍
  光束角: 60°     ← 不变
```

### 2. 物理合理性

```python
⚠️ 虽然可以任意修改流明值，但应保持物理合理性：

合理：
✅ 同款LED灯的不同功率版本 (500-2000 lm)
✅ 调光范围 (10%-100%)
✅ 考虑光衰的老化模拟

不合理：
❌ 将1000 lm改为1000000 lm（灯具尺寸支持不了）
❌ 将配光窄的灯改超高流明（热量散不出去）
❌ 物理上不可能的配置
```

### 3. 色温问题

```
重要：IES文件不存储色温信息！

修改流明值时：
- 亮度会改变 ✅
- 配光会缩放 ✅
- 色温不会改变 ❌

如果需要改变色温：
→ 在CG软件中单独设置光源颜色
→ Blender: Light.color
→ 3ds Max: Light Color
→ Unreal: Light Color
```

### 4. 文件兼容性

```
修改后的IES文件：
✅ 符合IES标准格式
✅ 所有CG软件都能正确读取
✅ 可通过IES验证工具检查

但要注意：
- 保持文件格式不变
- 不要改变配光数据
- 不要破坏文件结构
```

---

## 🧪 完整示例脚本

```python
#!/usr/bin/env python3
"""
IES流明值修改工具
可以批量修改IES文件的流明值
"""

import os
import sys
import argparse
from pathlib import Path

def read_ies_file(filepath):
    """读取IES文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.readlines()

def find_photometric_line(lines):
    """找到光度数据行的索引"""
    for i, line in enumerate(lines):
        if 'TILT=NONE' in line:
            return i + 1
    raise ValueError("未找到TILT=NONE行，可能不是有效的IES文件")

def modify_lumens(lines, new_lumens):
    """修改流明值"""
    idx = find_photometric_line(lines)
    values = lines[idx].split()
    
    old_lumens = float(values[1])
    values[1] = str(float(new_lumens))
    
    lines[idx] = ' '.join(values) + '\n'
    
    return lines, old_lumens

def save_ies_file(filepath, lines):
    """保存IES文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def batch_modify_ies(input_file, lumens_list, output_dir=None):
    """
    批量生成不同流明值的IES文件
    
    Args:
        input_file: 输入IES文件
        lumens_list: 流明值列表
        output_dir: 输出目录，默认为输入文件所在目录
    """
    input_path = Path(input_file)
    
    if output_dir is None:
        output_dir = input_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取基准文件
    base_lines = read_ies_file(input_path)
    base_name = input_path.stem
    
    print(f"📄 基准文件: {input_file}")
    print(f"📁 输出目录: {output_dir}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    results = []
    
    for lumens in lumens_list:
        # 复制并修改
        modified_lines = base_lines.copy()
        modified_lines, old_lumens = modify_lumens(modified_lines, lumens)
        
        # 生成输出文件名
        output_file = output_dir / f"{base_name}_{int(lumens)}lm.ies"
        
        # 保存
        save_ies_file(output_file, modified_lines)
        
        ratio = lumens / old_lumens
        results.append((output_file, lumens, ratio))
        
        print(f"✅ {output_file.name}")
        print(f"   流明: {lumens} lm (基准的 {ratio:.2f}x)")
    
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ 完成！共生成 {len(results)} 个IES文件")
    
    return results

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='修改IES文件的流明值',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 修改单个文件
  python modify_ies_lumens.py luminaire.ies -l 2000 -o luminaire_2000lm.ies
  
  # 批量生成系列文件
  python modify_ies_lumens.py luminaire.ies -b 500 1000 1500 2000
  
  # 生成调光系列
  python modify_ies_lumens.py luminaire.ies -b 250 500 750 1000 -d output/
        """
    )
    
    parser.add_argument('input', help='输入IES文件')
    parser.add_argument('-l', '--lumens', type=float, help='新的流明值')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-b', '--batch', nargs='+', type=float, 
                       help='批量模式：流明值列表')
    parser.add_argument('-d', '--dir', help='批量模式的输出目录')
    
    args = parser.parse_args()
    
    if args.batch:
        # 批量模式
        batch_modify_ies(args.input, args.batch, args.dir)
    elif args.lumens:
        # 单文件模式
        output = args.output or f"{Path(args.input).stem}_{int(args.lumens)}lm.ies"
        
        lines = read_ies_file(args.input)
        lines, old_lumens = modify_lumens(lines, args.lumens)
        save_ies_file(output, lines)
        
        print(f"✅ 流明值已修改: {old_lumens} → {args.lumens} lm")
        print(f"✅ 已保存到: {output}")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
```

**使用方法**：
```bash
# 单文件修改
python modify_ies_lumens.py downlight.ies -l 2000

# 批量生成系列
python modify_ies_lumens.py downlight.ies -b 500 1000 1500 2000

# 指定输出目录
python modify_ies_lumens.py downlight.ies -b 500 1000 1500 -d output/
```

---

## 📚 总结

### ✅ 核心结论

**是的！修改IES文件头部的流明值字段，CG软件中的灯光亮度会相应改变。**

这是因为：
1. IES的配光数据 (cd/klm) 是归一化的
2. 实际光强 = (cd/klm) × (总流明 / 1000)
3. 改变总流明 → 实际光强按比例缩放
4. 所有专业CG软件都正确支持这个机制

### 🎯 实际价值

这个特性非常有用：
- ✅ 快速生成系列产品IES
- ✅ 模拟调光效果
- ✅ 模拟灯具老化
- ✅ 灵活调整场景亮度
- ✅ 无需重新烘焙EXR

### ⚠️ 注意事项

- 只改变亮度，不改变配光形状
- 保持物理合理性
- IES不存储色温（需在CG软件中单独设置）
- 修改后的文件完全符合标准

---

**这正是我们之前讨论的线性关系在实际中的应用！** 🎉

---

**文档版本**: 1.0  
**创建日期**: 2026-01-21  
**关键发现**: 修改IES流明值可以直接改变CG软件中的灯光亮度
