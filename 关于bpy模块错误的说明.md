# 关于"bpy模块未找到"错误的说明

## ❓ 问题

在PyCharm或其他IDE中打开代码时，会看到如下错误：

```
没有名称为 'bpy' 的模块
未解析的引用 'mathutils'
```

## ✅ 这不是真正的错误！

### 原因

这些代码是**专门为Blender设计的**：

- `bpy` - Blender Python API，只在Blender内部可用
- `mathutils` - Blender的数学库，也只在Blender中可用

当你在**普通Python环境**（如PyCharm、VSCode）中打开这些文件时，IDE找不到这些模块，所以会报错。

但这是**正常的**！因为这些模块本来就不在标准Python环境中。

---

## 🎯 解决方案

### 方案1：忽略这些错误（推荐）✅

这些错误**不会影响代码在Blender中的运行**。

只要确保：
1. 在Blender中运行脚本
2. 不要在普通Python环境中运行

### 方案2：抑制IDE警告

我已经在代码中添加了 `# type: ignore` 注释：

```python
import bpy  # type: ignore
from mathutils import Vector  # type: ignore
```

这会告诉IDE忽略这些导入错误。

### 方案3：配置IDE的Blender Python环境（高级）

如果你经常开发Blender插件，可以配置IDE使用Blender的Python解释器：

#### PyCharm配置：

1. **找到Blender的Python路径**：
   ```
   Windows: C:\Program Files\Blender Foundation\Blender 3.x\3.x\python\bin\python.exe
   macOS: /Applications/Blender.app/Contents/Resources/3.x/python/bin/python3.x
   Linux: /usr/share/blender/3.x/python/bin/python3.x
   ```

2. **在PyCharm中配置**：
   - File → Settings → Project → Python Interpreter
   - 点击齿轮图标 → Add
   - 选择 "System Interpreter"
   - 浏览到Blender的Python可执行文件
   - 确认

3. **添加fake-bpy-module（可选）**：
   ```bash
   pip install fake-bpy-module-3.6  # 或你的Blender版本
   ```
   这会提供bpy的类型提示，但不能实际运行。

---

## 🔧 如何使用这些脚本

### 正确的使用方法 ✅

1. **打开Blender**

2. **切换到脚本编辑器**
   - 顶部菜单栏：Scripting 工作区
   - 或手动添加 Text Editor 面板

3. **加载脚本**
   - 点击 "Open" 按钮
   - 选择 `example_usage.py`

4. **修改脚本**
   - 取消注释想运行的示例
   ```python
   if __name__ == "__main__":
       example_basic_usage()  # 取消这行的注释
   ```

5. **运行脚本**
   - 点击 "Run Script" 按钮（▶️）
   - 或按 Alt+P

### 错误的使用方法 ❌

```bash
# 不要在命令行中运行！
python example_usage.py  # ❌ 错误！会报 bpy 未找到

# 不要在普通Python环境中运行！
python exr_to_ies_converter.py  # ❌ 错误！
```

---

## 📊 检查清单

在Blender中运行前，确保：

- [ ] 场景中有灯具对象
- [ ] 灯具包含Light组件
- [ ] 已设置好材质（反射器、灯罩等）
- [ ] 已定义LuminaireParameters
- [ ] 输出目录存在或可创建

---

## 🎓 技术说明

### 为什么要这样设计？

Blender的Python API（bpy）提供了：
- 场景对象访问
- 材质系统
- 渲染引擎控制
- 烘焙功能
- 图像处理

这些功能**只能在Blender内部使用**，无法在标准Python环境中模拟。

因此，这些脚本**必须**作为Blender脚本运行。

### 可以在普通Python中做什么？

只有纯数据处理部分可以独立运行：

```python
# 这些可以在普通Python中运行：
- modify_ies_lumens.py（修改IES文件）
- ProductsParametersToRadiantWatts.py（计算辐射瓦特）

# 这些必须在Blender中运行：
- exr_to_ies_converter.py
- example_usage.py
```

---

## 💡 快速参考

### 在Blender中运行示例

```python
# 在Blender脚本编辑器中：

import bpy
from exr_to_ies_converter import EXRToIESConverter, LuminaireParameters

# 选择当前对象
luminaire = bpy.context.active_object

# 定义参数
params = LuminaireParameters(
    name="Test Light",
    lumens=1000.0,
    source_type="led",
    color_temp=4000
)

# 执行转换
converter = EXRToIESConverter()
converter.process_full_workflow(
    luminaire_object=luminaire,
    luminaire_params=params,
    output_exr_path="//output/test.exr",  # // 表示Blender项目目录
    output_ies_path="//output/test.ies"
)
```

**注意**：在Blender中，`//` 表示当前.blend文件所在目录。

---

## 🔗 相关资源

### Blender Python API文档
- [Blender Python API](https://docs.blender.org/api/current/)
- [bpy.ops.object.bake](https://docs.blender.org/api/current/bpy.ops.object.html#bpy.ops.object.bake)
- [bpy.types.Light](https://docs.blender.org/api/current/bpy.types.Light.html)

### 学习资源
- [Blender Scripting for Artists](https://www.blender.org/support/tutorials/)
- [Blender Python API Quickstart](https://docs.blender.org/api/current/info_quickstart.html)

---

## ✅ 总结

### 关键点

1. **"bpy未找到"不是错误** - 这是正常的，因为bpy只在Blender中存在
2. **代码必须在Blender中运行** - 不能在普通Python环境运行
3. **已添加type: ignore注释** - 抑制IDE警告
4. **功能完全正常** - 在Blender中可以正常使用

### 下一步

1. 在Blender中打开脚本编辑器
2. 加载 `example_usage.py`
3. 选择想运行的示例
4. 点击运行

**享受使用吧！** 🚀

---

**最后更新**: 2026-01-21  
**状态**: 这些"错误"是正常的，可以忽略
