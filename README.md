# EXR to IES Converter

将EXR光照分布转换为标准IES光度文件的完整工具集。

![Version](https://img.shields.io/badge/version-1.0-blue)
![Blender](https://img.shields.io/badge/Blender-2.93%2B-orange)
![Python](https://img.shields.io/badge/Python-3.7%2B-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## 🎯 两个版本

### 🌟 完整版（Blender集成）
**适用于**: Blender用户，需要从灯具模型生成IES

- ✅ 在Blender中运行
- ✅ 从灯具3D模型自动生成EXR和IES
- ✅ 自动计算所有参数
- ✅ 完整的工作流程

→ 使用 `exr_to_ies_converter.py`  
→ 参见 `使用指南.md`

### ⚡ 独立版（纯Python）
**适用于**: 处理现有EXR文件，支持任何渲染器

- ✅ 不依赖Blender
- ✅ 处理3ds Max/V-Ray/Corona/Arnold等的EXR
- ✅ 命令行工具，快速转换
- ✅ 可集成到任何工作流程

→ 使用 `standalone_exr_to_ies.py` ⭐  
→ 参见 `独立版使用指南.md` ⭐

---

## ✨ 特性

- 🎯 **自动计算测量距离** - 基于灯具尺寸，符合IES标准
- 🌐 **智能球体创建** - 自动配置测量球体和UV映射
- 🔥 **物理正确烘焙** - 32位浮点EXR，保留真实辐照度
- 📊 **标准IES输出** - 符合IESNA LM-63-2002标准
- ⚡ **批量处理** - 一次烘焙，生成多个亮度版本
- 🎨 **完整参数支持** - 描述灯具的所有必要信息

---

## 📦 文件列表

### 核心文件

- `exr_to_ies_converter.py` - **Blender集成版** （完整工作流）
- `standalone_exr_to_ies.py` - **独立版** ⭐（处理现有EXR）
- `ProductsParametersToRadiantWatts.py` - 辐射瓦特计算模块
- `example_usage.py` - Blender版使用示例
- `modify_ies_lumens.py` - IES流明值修改工具

### 文档

- `README.md` - 本文档
- `使用指南.md` - **Blender版完整说明**
- `独立版使用指南.md` - **独立版完整说明** ⭐
- `EXR转IES技术方案.md` - 技术原理和方案
- `测量球体网格密度分析.md` - 精度分析
- `测量距离计算方法.md` - 距离计算详解
- `灯具遮挡与IES真实性.md` - 物理正确性说明
- `灯光功率与IES强度的关系.md` - 功率亮度关系

---

## 🚀 快速开始

### 独立版（推荐用于处理现有EXR）⚡

```bash
# 安装依赖
pip install numpy OpenEXR

# 转换EXR到IES
python standalone_exr_to_ies.py input.exr output.ies -l 1000 -d 5.0

# 参数说明：
# -l 1000: 总流明1000 lm
# -d 5.0: 测量距离5米（必须与EXR烘焙时的球体半径一致）
```

**完成！** 🎉

**详细说明**: 参见 `独立版使用指南.md`

---

### Blender完整版（用于从模型生成）

#### 安装

1. 将所有`.py`文件放入同一目录
2. 在Blender中打开脚本编辑器
3. 加载 `example_usage.py`

### 最简使用

```python
import bpy
from exr_to_ies_converter import EXRToIESConverter, LuminaireParameters

# 1. 选择灯具
luminaire = bpy.context.active_object

# 2. 定义参数
params = LuminaireParameters(
    name="LED Downlight",
    lumens=1000.0,
    source_type="led",
    color_temp=4000
)

# 3. 执行转换
converter = EXRToIESConverter()
converter.process_full_workflow(
    luminaire_object=luminaire,
    luminaire_params=params,
    output_exr_path="output/light.exr",
    output_ies_path="output/light.ies"
)
```

**完成！** 🎉

---

## 📐 灯具参数说明

### LuminaireParameters

完整描述灯具的参数类。

#### 必需参数 ⭐⭐⭐⭐⭐

```python
params = LuminaireParameters(
    name="灯具名称",
    lumens=1000.0,          # 总流明（最重要）
    source_type="led",      # 光源类型
    color_temp=4000,        # 色温（K）
)
```

#### 推荐参数 ⭐⭐⭐⭐

```python
params = LuminaireParameters(
    width=0.15,             # 宽度（米）
    length=0.15,            # 长度（米）
    height=0.10,            # 高度（米）
)
```

#### 可选参数 ⭐⭐⭐

```python
params = LuminaireParameters(
    manufacturer="制造商",
    catalog_number="产品编号",
    cri=80,                 # 显色指数
    beam_angle=60,          # 光束角（度）
    electrical_watts=10.0,  # 电功率（W）
)
```

**详细说明**: 参见 `使用指南.md`

---

## ⚙️ 配置选项

### 标准配置（推荐）⭐⭐⭐⭐⭐

```python
converter = EXRToIESConverter(
    resolution='high',          # 4K EXR
    sphere_density='standard',  # 72×36 球体
    cycles_samples=256          # 标准采样
)
```

**适用**：90%的灯具  
**精度**：>99%  
**时间**：3-5分钟  

### 高精度配置 ⭐⭐⭐⭐

```python
converter = EXRToIESConverter(
    resolution='ultra',         # 8K EXR
    sphere_density='fine',      # 144×72 球体
    cycles_samples=512          # 高采样
)
```

**适用**：汽车灯、科研级测量  
**精度**：>99.5%  
**时间**：15-30分钟  

### 快速预览配置 ⭐⭐

```python
converter = EXRToIESConverter(
    resolution='low',           # 1K EXR
    sphere_density='preview',   # 36×18 球体
    cycles_samples=64           # 快速采样
)
```

**适用**：快速迭代、概念验证  
**精度**：~95%  
**时间**：<2分钟  

---

## 💡 使用场景

### 场景1：标准筒灯

```python
params = LuminaireParameters(
    name="LED Downlight",
    lumens=1000.0,
    source_type="led",
    color_temp=4000,
    width=0.15,
    height=0.10,
    beam_angle=60
)

converter = EXRToIESConverter()  # 标准配置
converter.process_full_workflow(...)
```

### 场景2：汽车大灯

```python
params = LuminaireParameters(
    name="Car Headlight",
    lumens=1500.0,
    source_type="led_high_end",
    color_temp=6000,
    beam_angle=8  # 极窄光束
)

converter = EXRToIESConverter(
    resolution='ultra',         # 8K
    sphere_density='fine',      # 144×72
    cycles_samples=512
)
converter.process_full_workflow(...)
```

### 场景3：批量生成系列产品

```python
# 烘焙一次
base_params = LuminaireParameters(lumens=1000, ...)
# ... 烘焙到 base.exr ...

# 生成多个版本
exr_data = converter.read_exr_data("base.exr")
for lumens in [500, 1000, 1500, 2000]:
    # 转换为不同流明的IES
    # 无需重新烘焙！
```

---

## 📊 性能指标

### 标准配置（72×36球体 + 4K EXR + 256采样）

| 硬件 | CPU渲染 | GPU渲染 |
|------|---------|---------|
| 入门级 | 8-12min | 4-6min |
| 中端 | 5-8min | 2-4min |
| 高端 | 3-5min | 1-2min |

### 精度对比

| 配置 | 角度精度 | 光强误差 | 文件大小 |
|-----|---------|---------|---------|
| 预览 (36×18 + 1K) | ±1° | <5% | ~30MB |
| **标准 (72×36 + 4K)** | **±0.5°** | **<1%** | **~130MB** |
| 精细 (144×72 + 8K) | ±0.25° | <0.3% | ~450MB |

---

## 🎓 工作流程

```
准备灯具 Blender模型
    ↓
定义灯具参数 (LuminaireParameters)
    ↓
创建转换器 (EXRToIESConverter)
    ↓
执行转换 (process_full_workflow)
    ├─ 自动计算辐射瓦数
    ├─ 设置Blender场景
    ├─ 创建测量球体
    ├─ 烘焙光照到EXR
    ├─ 读取EXR数据
    ├─ 转换为IES格式
    └─ 输出IES文件
    ↓
在CG软件中使用IES
```

---

## ⚠️ 注意事项

### ✅ 必须做的

1. **保留灯具遮挡** - 这是配光特性的一部分
2. **使用真实流明值** - 便于验证和调试
3. **完整的灯具模型** - 包含反射器、灯罩等
4. **正确的材质** - 反射器=金属，灯罩=半透明
5. **检查测量距离** - 应≥灯具直径的5倍

### ❌ 避免的

1. ❌ 隐藏灯具几何体（会丢失遮挡信息）
2. ❌ 使用任意功率值（虽然数学上可以）
3. ❌ 测量距离过小（违反远场条件）
4. ❌ 过度追求精度（8K通常不必要）

---

## 🔧 常见问题

### Q: 烘焙时间过长？

**A**: 启用GPU或降低采样/分辨率

```python
# 启用GPU
scene.cycles.device = 'GPU'

# 或降低配置
converter = EXRToIESConverter(
    resolution='medium',
    cycles_samples=128
)
```

### Q: IES在CG软件中太暗/太亮？

**A**: 调整流明值

```python
# 方法1：修改参数重新生成
params.lumens = 1500.0

# 方法2：使用修改工具
python modify_ies_lumens.py output.ies -l 1500
```

### Q: 需要多高的精度？

**A**: 标准配置（72×36 + 4K）足够90%的情况

只有极窄光束（<10°）或科研级需求才需要更高精度。

### Q: 可以重用EXR吗？

**A**: 可以！这是高效工作流的关键

一次烘焙，生成多个不同流明的IES版本。

---

## 📚 技术原理

### 核心概念

1. **远场测量** - 距离 ≥ 5×灯具直径
2. **球坐标采样** - θ (0-180°) × φ (0-360°)
3. **物理正确** - 32位浮点EXR，Raw色彩空间
4. **归一化配光** - cd/klm独立于绝对亮度
5. **线性关系** - 功率翻倍 → EXR翻倍 → IES亮度翻倍

**详细原理**: 参见 `EXR转IES技术方案.md`

---

## 🎯 最佳实践

### 推荐工作流

1. **准备阶段**
   - 完整建模灯具
   - 设置真实材质
   - 添加光源

2. **测试阶段**
   - 使用预览配置快速测试
   - 验证配光形状

3. **最终输出**
   - 使用标准配置生成
   - 保存EXR备份

4. **批量生产**
   - 重用EXR生成多个版本
   - 节省大量时间

### 质量检查

- [ ] 流明值准确
- [ ] 配光形状正确
- [ ] 灯具遮挡保留
- [ ] 测量距离合理
- [ ] IES文件可用

---

## 📖 文档索引

### 快速参考
- ⭐ `README.md` - 本文档
- ⭐ `使用指南.md` - 完整使用说明
- ⭐ `example_usage.py` - 代码示例

### 技术文档
- `EXR转IES技术方案.md` - 完整技术方案
- `测量球体网格密度分析.md` - 精度分析
- `测量距离计算方法.md` - 距离选择
- `灯具遮挡与IES真实性.md` - 物理正确性
- `灯光功率与IES强度的关系.md` - 功率亮度关系

### 快速参考
- `球体网格密度-快速参考.md` - 配置速查
- `烘焙功率选择-快速对比.md` - 功率选择
- `快速问答-IES流明值修改.md` - 常见问题

---

## 🤝 贡献

欢迎提交问题和改进建议！

---

## 📄 许可证

MIT License

---

## 🙏 致谢

基于对IES标准、光度学原理和Blender烘焙机制的深入研究开发。

---

## 📞 支持

遇到问题？

1. 查看 `使用指南.md` 
2. 参考 `example_usage.py` 示例
3. 阅读相关技术文档

---

**版本**: 1.0  
**日期**: 2026-01-21  
**状态**: ✅ 生产就绪  

**快速开始**: 运行 `example_usage.py` 中的示例！🚀
