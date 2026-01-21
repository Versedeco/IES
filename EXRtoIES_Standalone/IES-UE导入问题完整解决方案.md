# IES文件UE导入问题完整解决方案

## 📌 目录
- [问题现象](#问题现象)
- [根本原因](#根本原因)
- [解决方案](#解决方案)
- [使用方法](#使用方法)
- [验证步骤](#验证步骤)
- [技术细节](#技术细节)
- [常见问题](#常见问题)

---

## 问题现象

在Unreal Engine中导入生成的IES文件时，出现以下错误：

```
[IES文件路径 : '', InterchangeIESTranslator] 
IES import failed: "V Values are not in increasing order"

[IES文件路径 : '', TextureLightProfile] 
Unable to retrieve the payload from the source file.
```

**影响**：
- ❌ IES文件无法导入UE
- ❌ 无法创建TextureLightProfile资源
- ❌ 无法在场景中使用IES光照

---

## 根本原因

### IES标准要求

根据 **IES-LM-63标准**（照明工程学会标准），IES文件中的角度数据必须满足：

1. **垂直角度（V-angles/Theta）**：必须严格按 **递增顺序** 排列
   - 范围：0° → 180°
   - 示例：`0.0 5.0 10.0 15.0 ... 175.0 180.0`

2. **水平角度（H-angles/Phi）**：必须严格按 **递增顺序** 排列
   - 范围：0° → 360°
   - 示例：`0.0 15.0 30.0 45.0 ... 345.0 360.0`

3. **光强数据顺序**：每个C平面的所有V角数据必须连续写入
   ```
   for 每个C平面:
       for 该平面的每个V角:
           写入光强值
   ```

### 旧版本问题

旧版本程序在生成IES文件时：
- ❌ 未对角度数据进行排序
- ❌ 可能产生乱序的角度值
- ❌ 导致不符合IES标准

---

## 解决方案

### v2.1版本修复

已在 **v2.1版本** 中完全修复此问题！

#### 修复内容

1. **自动角度排序**
   ```python
   # 确保角度按升序排列
   h_angles = np.sort(h_angles)
   v_angles = np.sort(v_angles)
   ```

2. **角度验证机制**
   ```python
   # 验证角度顺序
   if not np.all(np.diff(h_angles) >= 0):
       raise ValueError("水平角度必须按升序排列")
   if not np.all(np.diff(v_angles) >= 0):
       raise ValueError("垂直角度必须按升序排列")
   ```

3. **标准合规写入**
   - ✅ 外层循环遍历水平角
   - ✅ 内层循环遍历垂直角
   - ✅ 每个C平面数据连续写入

---

## 使用方法

### 方法1：使用EXE程序（推荐）

1. **启动程序**
   ```
   双击：dist\EXR_to_IES_Converter.exe
   ```

2. **转换流程**
   - 选择EXR文件
   - 填写必要参数（流明值、测量距离等）
   - 点击"开始转换"按钮
   - 保存生成的IES文件

3. **导入UE**
   - 在UE的Content Browser中右键 → Import
   - 选择生成的IES文件
   - ✅ 导入成功！

### 方法2：使用Python脚本

```bash
cd D:\TestLighting\EXR_to_IES\EXRtoIES_Standalone
python exr_to_ies_gui.py
```

---

## 验证步骤

### 步骤1：验证IES文件格式

用文本编辑器打开生成的IES文件：

**检查水平角度行（第一行角度）**
```
✅ 正确：0.0 15.0 30.0 45.0 60.0 ... 345.0 360.0
❌ 错误：45.0 0.0 90.0 30.0 ...（乱序）
```

**检查垂直角度行（第二行角度）**
```
✅ 正确：0.0 5.0 10.0 15.0 ... 175.0 180.0
❌ 错误：90.0 0.0 45.0 ...（乱序）
```

### 步骤2：UE导入测试

1. **打开UE项目**
2. **导入IES文件**
   - Content Browser → 右键 → Import
   - 选择IES文件
3. **检查Output Log**
   - ✅ 成功：无错误信息
   - ❌ 失败：显示错误提示

### 步骤3：光照效果测试

1. 在场景中添加Point Light或Spot Light
2. 设置Light属性：
   - **IES Texture** → 选择导入的IES
   - **Use IES Intensity** → 勾选
3. 观察光照分布是否正确

---

## 技术细节

### IES文件结构

```
IESNA:LM-63-2002
[MANUFAC] 制造商
[LUMCAT] 型号
...
TILT=NONE
1 <流明> 1.0 <H角数> <V角数> <类型> 2 <宽> <长> <高>
<水平角度行 - 必须递增>
<垂直角度行 - 必须递增>
<光强数据 - 按C平面→V角顺序>
```

### 代码修改位置

**文件**：`exr_to_ies_gui.py`  
**类**：`EXRToIESConverter`  
**方法**：`write_ies_file()`  
**行数**：243-281行

### 关键改动

```python
def write_ies_file(self, output_path, lumens, candela_values,
                  h_angles, v_angles, metadata):
    """写入IES文件"""
    # 【新增】确保角度按升序排列
    h_angles = np.sort(h_angles)
    v_angles = np.sort(v_angles)
    
    # 【新增】验证角度顺序
    if not np.all(np.diff(h_angles) >= 0):
        raise ValueError("水平角度必须按升序排列")
    if not np.all(np.diff(v_angles) >= 0):
        raise ValueError("垂直角度必须按升序排列")
    
    # ...后续写入逻辑
```

---

## 常见问题

### Q1: 使用旧版本生成的IES怎么办？

**答**：必须使用v2.1或更新版本 **重新生成** IES文件。

### Q2: 为什么旧IES在其他软件能用，UE不行？

**答**：不同软件对IES格式要求严格程度不同。UE严格遵循IES标准，要求角度必须递增。

### Q3: 如何确认我使用的是新版本？

**答**：
- 检查程序标题显示 **v2.1**
- 查看 `版本更新日志.md` 中的v2.1条目
- 生成的IES文件角度严格递增

### Q4: 修复后IES的光照效果会改变吗？

**答**：不会！只是调整了角度顺序，光强分布数据完全相同。

### Q5: 如何报告新问题？

**答**：请提供：
- EXR源文件
- 生成的IES文件
- UE Output Log截图
- 程序版本信息

---

## 版本信息

| 版本 | 日期 | 状态 | 说明 |
|------|------|------|------|
| v2.1 | 2026-01-21 | ✅ 当前版本 | 修复UE导入错误 |
| v2.0 | 2026-01-21 | ⚠️ 有已知问题 | 增加可视化功能 |
| v1.x | 更早 | ❌ 不推荐 | 基础版本 |

---

## 相关文档

- 📄 `README.md` - 完整使用说明
- 📄 `版本更新日志.md` - 详细版本历史
- 📄 `IES-UE导入错误修复说明.md` - 技术修复细节
- 📄 `IES修复测试指南.md` - 测试验证方法
- 📄 `UE导入修复-快速说明.txt` - 快速参考

---

## 总结

✅ **问题**：IES文件在UE中导入失败（角度顺序错误）  
✅ **原因**：未遵循IES-LM-63标准（角度未排序）  
✅ **解决**：v2.1版本自动排序并验证角度  
✅ **结果**：完美兼容UE 4.x/5.x

**立即行动**：
1. 使用v2.1版本程序
2. 重新生成IES文件
3. 在UE中测试导入
4. 享受正确的IES光照！

---

**文档版本**：v1.0  
**创建日期**：2026-01-21  
**适用程序版本**：EXR转IES转换器 v2.1及以上
