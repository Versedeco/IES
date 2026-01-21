# IES文件UE导入错误修复说明

## 错误现象

在Unreal Engine中导入生成的IES文件时出现以下错误：

```
[D:/TestLighting/TD_5w_D5M_New.ies : '', InterchangeIESTranslator] 
IES import failed: "V Values are not in increasing order"

[D:/TestLighting/TD_5w_D5M_New.ies : '', TextureLightProfile] 
Unable to retrieve the payload from the source file.
```

## 错误原因

根据 **IES-LM-63标准**，IES文件中的：
- **垂直角度（V-angles/Theta）** 必须严格按 **递增顺序** 排列（通常0° → 180°）
- **水平角度（H-angles/Phi）** 也必须严格按 **递增顺序** 排列（通常0° → 360°）

如果角度数据未排序或顺序错误，会导致UE等引擎无法正确解析IES文件。

## 修复方案

### 修改位置
文件：`exr_to_ies_gui.py`
方法：`EXRToIESConverter.write_ies_file()`

### 修复内容

#### 1. 添加角度排序
```python
# 确保角度按升序排列（符合IES-LM-63标准）
h_angles = np.sort(h_angles)
v_angles = np.sort(v_angles)
```

#### 2. 添加验证逻辑
```python
# 验证角度顺序
if not np.all(np.diff(h_angles) >= 0):
    raise ValueError("水平角度必须按升序排列")
if not np.all(np.diff(v_angles) >= 0):
    raise ValueError("垂直角度必须按升序排列")
```

#### 3. 确认数据写入顺序
数据写入顺序已符合IES标准：
- **外层循环**：遍历水平角（C平面）
- **内层循环**：遍历垂直角（V角）
- 即：每个C平面的所有V角数据连续写入

```python
for phi_idx in range(n_horizontal):      # 每个C平面
    for theta_idx in range(n_vertical):   # 该平面的所有V角
        cd_value = candela_values[phi_idx, theta_idx]
        f.write(f"{cd_value:.2f} ")
```

## IES标准要求总结

### 角度规范
| 角度类型 | 符号 | 范围 | 排序要求 |
|---------|------|------|----------|
| 水平角（C平面） | φ (Phi) | 0° - 360° | 严格递增 |
| 垂直角（V角） | θ (Theta) | 0° - 180° | 严格递增 |

### 数据组织格式
```
光强数据排列顺序：
C0平面: V0, V1, V2, ..., Vn
C1平面: V0, V1, V2, ..., Vn
C2平面: V0, V1, V2, ..., Vn
...
Cm平面: V0, V1, V2, ..., Vn
```

## 修复效果

✅ **修复后**：
- 角度数据自动排序，确保递增
- 添加验证机制，提前发现格式错误
- 数据写入顺序符合IES-LM-63标准
- UE可以正常导入并识别IES文件

## 测试方法

### 1. 重新生成IES文件
使用修复后的程序重新转换EXR：
```bash
python exr_to_ies_gui.py
```

### 2. 验证IES文件格式
打开生成的IES文件，检查：
- 垂直角度行是否按0→180递增
- 水平角度行是否按0→360递增

### 3. 导入UE测试
在Unreal Engine中：
1. 导入新生成的IES文件
2. 检查是否有错误提示
3. 查看光照配置是否正常显示

## 技术参考

- **标准名称**：IESNA LM-63-2002 / IES LM-63-19
- **关键要求**：
  - 角度值必须单调递增
  - 光强数据按"C平面优先"顺序组织
  - 数据精度建议保留2位小数

## 修复日期
2026-01-21

## 相关文件
- `exr_to_ies_gui.py` - 主程序文件
- `EXR转IES技术方案.md` - 技术方案文档
- `可视化功能说明.md` - 可视化功能文档
