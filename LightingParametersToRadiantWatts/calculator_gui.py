"""
灯光参数转辐射瓦特计算器 - GUI版本
Lighting Parameters to Radiant Watts Calculator

一个简单易用的图形界面工具，用于将灯具参数转换为Blender所需的辐射瓦特值。
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
from datetime import datetime


class LampSpecsToRadiantConverter:
    """灯具规格到辐射瓦特转换器（内嵌版本）"""

    def __init__(self):
        # 光源类型规格
        self.light_source_specs = {
            "LED灯": {
                "code": "led",
                "typical_efficacy": 100,
                "efficacy_range": (80, 150),
                "radiant_efficiency": 0.35,
                "temp_range": (2700, 6500),
                "description": "普通LED灯，光效80-150 lm/W"
            },
            "高端LED灯": {
                "code": "led_high_end",
                "typical_efficacy": 150,
                "efficacy_range": (120, 200),
                "radiant_efficiency": 0.45,
                "temp_range": (2700, 6500),
                "description": "高端LED灯，光效120-200 lm/W"
            },
            "白炽灯": {
                "code": "incandescent",
                "typical_efficacy": 15,
                "efficacy_range": (10, 20),
                "radiant_efficiency": 0.95,
                "temp_range": (2400, 2700),
                "description": "白炽灯泡，光效10-20 lm/W"
            },
            "卤素灯": {
                "code": "halogen",
                "typical_efficacy": 20,
                "efficacy_range": (15, 25),
                "radiant_efficiency": 0.90,
                "temp_range": (2900, 3200),
                "description": "卤素灯，光效15-25 lm/W"
            },
            "荧光灯/节能灯": {
                "code": "fluorescent",
                "typical_efficacy": 65,
                "efficacy_range": (50, 80),
                "radiant_efficiency": 0.85,
                "temp_range": (2700, 6500),
                "description": "荧光灯/节能灯，光效50-80 lm/W"
            },
            "金属卤化物灯": {
                "code": "metal_halide",
                "typical_efficacy": 85,
                "efficacy_range": (70, 100),
                "radiant_efficiency": 0.65,
                "temp_range": (3000, 5500),
                "description": "金卤灯，光效70-100 lm/W"
            },
            "高压钠灯": {
                "code": "high_pressure_sodium",
                "typical_efficacy": 110,
                "efficacy_range": (80, 140),
                "radiant_efficiency": 0.40,
                "temp_range": (1900, 2200),
                "description": "高压钠灯，光效80-140 lm/W"
            }
        }

        # 色温修正系数
        self.color_temp_factors = {
            2700: 0.85,
            3000: 0.90,
            4000: 1.00,
            5000: 1.05,
            6500: 1.10
        }

    def get_color_temp_factor(self, color_temp):
        """获取色温修正系数"""
        temps = sorted(self.color_temp_factors.keys())
        if color_temp <= temps[0]:
            return self.color_temp_factors[temps[0]]
        if color_temp >= temps[-1]:
            return self.color_temp_factors[temps[-1]]

        for i in range(len(temps) - 1):
            if temps[i] <= color_temp <= temps[i + 1]:
                t1, t2 = temps[i], temps[i + 1]
                f1, f2 = self.color_temp_factors[t1], self.color_temp_factors[t2]
                factor = f1 + (f2 - f1) * (color_temp - t1) / (t2 - t1)
                return factor
        return 1.0

    def calculate_radiant_watts(self, lumens, source_name, color_temp):
        """计算辐射瓦特"""
        if source_name not in self.light_source_specs:
            raise ValueError(f"未知的光源类型: {source_name}")

        specs = self.light_source_specs[source_name]
        temp_factor = self.get_color_temp_factor(color_temp)
        adjusted_efficacy = specs["typical_efficacy"] * temp_factor
        max_luminous_efficacy = 683
        relative_efficacy = adjusted_efficacy / max_luminous_efficacy
        radiant_watts = lumens / (max_luminous_efficacy * relative_efficacy)

        return radiant_watts, specs


class CalculatorApp:
    """计算器主窗口"""

    def __init__(self, root):
        self.root = root
        self.root.title("灯光参数转辐射瓦特计算器 v1.0")
        self.root.geometry("700x800")
        self.root.resizable(True, True)

        # 创建转换器
        self.converter = LampSpecsToRadiantConverter()

        # 设置样式
        self.setup_styles()

        # 创建界面
        self.create_widgets()

        # 居中窗口
        self.center_window()

    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 标题样式
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 11, 'bold'))
        style.configure('Info.TLabel', font=('Arial', 9))

        # 按钮样式
        style.configure('Calculate.TButton', font=('Arial', 11, 'bold'))

    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text="🔆 灯光参数转辐射瓦特计算器",
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0, pady=(0, 10))

        subtitle_label = ttk.Label(
            main_frame,
            text="将灯具参数转换为Blender所需的辐射瓦特值",
            style='Info.TLabel'
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 20))

        # 输入区域
        input_frame = ttk.LabelFrame(main_frame, text="输入参数", padding="15")
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        input_frame.columnconfigure(1, weight=1)

        # 光源类型
        ttk.Label(input_frame, text="光源类型:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=8
        )
        self.source_type_var = tk.StringVar()
        source_combo = ttk.Combobox(
            input_frame,
            textvariable=self.source_type_var,
            state='readonly',
            font=('Arial', 10),
            width=30
        )
        source_combo['values'] = list(self.converter.light_source_specs.keys())
        source_combo.current(0)
        source_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=8)
        source_combo.bind('<<ComboboxSelected>>', self.on_source_type_changed)

        # 光源描述
        self.source_desc_label = ttk.Label(
            input_frame,
            text="",
            style='Info.TLabel',
            foreground='gray'
        )
        self.source_desc_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(0, 8))
        self.update_source_description()

        # 流明值
        ttk.Label(input_frame, text="流明值 (lm):", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, pady=8
        )
        self.lumens_var = tk.StringVar(value="1000")
        lumens_entry = ttk.Entry(input_frame, textvariable=self.lumens_var, font=('Arial', 10))
        lumens_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=8)

        ttk.Label(input_frame, text="灯具的总光通量", style='Info.TLabel', foreground='gray').grid(
            row=3, column=1, sticky=tk.W, padx=(10, 0), pady=(0, 8)
        )

        # 色温
        ttk.Label(input_frame, text="色温 (K):", font=('Arial', 10, 'bold')).grid(
            row=4, column=0, sticky=tk.W, pady=8
        )

        color_temp_frame = ttk.Frame(input_frame)
        color_temp_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=8)
        color_temp_frame.columnconfigure(0, weight=1)

        self.color_temp_var = tk.StringVar(value="4000")
        color_temp_entry = ttk.Entry(color_temp_frame, textvariable=self.color_temp_var, font=('Arial', 10))
        color_temp_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))

        # 预设色温按钮
        preset_frame = ttk.Frame(color_temp_frame)
        preset_frame.grid(row=0, column=1)

        ttk.Button(preset_frame, text="2700K", command=lambda: self.color_temp_var.set("2700"), width=7).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="4000K", command=lambda: self.color_temp_var.set("4000"), width=7).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="6500K", command=lambda: self.color_temp_var.set("6500"), width=7).pack(side=tk.LEFT, padx=2)

        ttk.Label(input_frame, text="光源的色温（2700K暖光，4000K中性，6500K冷光）",
                 style='Info.TLabel', foreground='gray').grid(
            row=5, column=1, sticky=tk.W, padx=(10, 0), pady=(0, 8)
        )

        # 计算按钮
        calc_button = ttk.Button(
            main_frame,
            text="🔄 计算辐射瓦特",
            command=self.calculate,
            style='Calculate.TButton'
        )
        calc_button.grid(row=3, column=0, pady=15)

        # 结果区域
        result_frame = ttk.LabelFrame(main_frame, text="计算结果", padding="15")
        result_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        result_frame.columnconfigure(1, weight=1)

        # 辐射瓦特结果
        ttk.Label(result_frame, text="辐射瓦特:", font=('Arial', 11, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=8
        )
        self.result_watts_label = ttk.Label(
            result_frame,
            text="--",
            font=('Arial', 16, 'bold'),
            foreground='#2E7D32'
        )
        self.result_watts_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=8)

        # Blender设置说明
        ttk.Label(result_frame, text="Blender设置:", font=('Arial', 10, 'bold')).grid(
            row=1, column=0, sticky=tk.W, pady=8
        )
        self.blender_label = ttk.Label(
            result_frame,
            text="--",
            font=('Arial', 10),
            foreground='#1565C0'
        )
        self.blender_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=8)

        # 复制按钮
        self.copy_button = ttk.Button(
            result_frame,
            text="📋 复制数值",
            command=self.copy_result,
            state='disabled'
        )
        self.copy_button.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))

        # 详细信息区域
        detail_frame = ttk.LabelFrame(main_frame, text="详细信息", padding="15")
        detail_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        main_frame.rowconfigure(5, weight=1)

        self.detail_text = scrolledtext.ScrolledText(
            detail_frame,
            height=10,
            font=('Consolas', 9),
            wrap=tk.WORD
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        # 底部信息
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=6, column=0, sticky=(tk.W, tk.E))

        ttk.Label(
            footer_frame,
            text="提示：先输入参数，点击「计算辐射瓦特」按钮，然后在Blender中使用计算结果",
            style='Info.TLabel',
            foreground='gray'
        ).pack(side=tk.LEFT)

        ttk.Button(
            footer_frame,
            text="❓ 帮助",
            command=self.show_help
        ).pack(side=tk.RIGHT)

    def on_source_type_changed(self, event=None):
        """光源类型改变时更新描述和色温建议"""
        self.update_source_description()

    def update_source_description(self):
        """更新光源描述"""
        source_name = self.source_type_var.get()
        if source_name in self.converter.light_source_specs:
            specs = self.converter.light_source_specs[source_name]
            desc = specs['description']
            self.source_desc_label.config(text=desc)

    def calculate(self):
        """执行计算"""
        try:
            # 获取输入
            lumens = float(self.lumens_var.get())
            source_name = self.source_type_var.get()
            color_temp = float(self.color_temp_var.get())

            # 验证输入
            if lumens <= 0:
                messagebox.showerror("输入错误", "流明值必须大于0")
                return

            if color_temp < 1000 or color_temp > 10000:
                messagebox.showerror("输入错误", "色温范围应在1000K-10000K之间")
                return

            # 计算
            radiant_watts, specs = self.converter.calculate_radiant_watts(
                lumens, source_name, color_temp
            )

            # 显示结果
            self.result_watts_label.config(text=f"{radiant_watts:.2f} W")
            self.blender_label.config(text=f"Light.energy = {radiant_watts:.2f}")
            self.copy_button.config(state='normal')

            # 显示详细信息
            self.show_details(lumens, source_name, color_temp, radiant_watts, specs)

        except ValueError as e:
            messagebox.showerror("输入错误", f"请检查输入值是否正确:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("计算错误", f"计算过程中出错:\n{str(e)}")

    def show_details(self, lumens, source_name, color_temp, radiant_watts, specs):
        """显示详细计算信息"""
        self.detail_text.delete(1.0, tk.END)

        detail_info = f"""
{'='*60}
计算详情
{'='*60}

📋 输入参数:
   光源类型:     {source_name}
   流明值:       {lumens:.0f} lm
   色温:         {color_temp:.0f} K

🔄 转换结果:
   辐射瓦特:     {radiant_watts:.3f} W
   
✅ 验证信息:
   典型光效:     {specs['typical_efficacy']} lm/W
   光效范围:     {specs['efficacy_range'][0]}-{specs['efficacy_range'][1]} lm/W
   色温范围:     {specs['temp_range'][0]}-{specs['temp_range'][1]} K
   
   估算电功率:   {lumens / specs['typical_efficacy']:.1f} W
   实际光效:     {lumens / (lumens / specs['typical_efficacy']):.1f} lm/W

💡 使用说明:
   1. 在Blender中选择灯光对象
   2. 设置 Light.energy = {radiant_watts:.2f}
   3. 或在Python中: light.data.energy = {radiant_watts:.2f}
   4. 然后可以进行烘焙或渲染

📅 计算时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}
"""
        self.detail_text.insert(1.0, detail_info)

    def copy_result(self):
        """复制结果到剪贴板"""
        result_text = self.result_watts_label.cget("text").split()[0]
        self.root.clipboard_clear()
        self.root.clipboard_append(result_text)
        messagebox.showinfo("已复制", f"数值 {result_text} 已复制到剪贴板")

    def show_help(self):
        """显示帮助信息"""
        help_text = """
【灯光参数转辐射瓦特计算器】使用帮助

📖 基本说明:
   这个工具用于将灯具厂商提供的参数（流明值、色温）转换为
   Blender所需的辐射瓦特(Radiant Watts)值。

🔢 输入参数说明:

   1. 光源类型
      - 选择灯具使用的光源类型
      - 不同光源的光谱效率不同
      
   2. 流明值 (lm)
      - 灯具的总光通量
      - 可从产品规格书获取
      - 例如: 1000 lm, 1500 lm
      
   3. 色温 (K)
      - 光源的色温
      - 2700K: 暖白光
      - 4000K: 中性白光
      - 6500K: 冷白光

📊 计算结果说明:

   辐射瓦特 (Radiant Watts)
   - Blender Light对象的energy属性值
   - 包含可见光和不可见光(如红外)的辐射功率

💻 在Blender中使用:

   方法1: 在界面中设置
   - 选择灯光对象
   - Light面板 → Power → 输入计算结果

   方法2: 在Python脚本中
   - light.data.energy = [计算结果]

❓ 常见问题:

   Q: 为什么LED和白炽灯相同流明，辐射瓦特差异大？
   A: 白炽灯大部分能量转为红外热辐射，LED几乎全是可见光。

   Q: 色温如何影响结果？
   A: 高色温光效更高，需要的辐射功率更少。

📧 反馈与支持:
   如有问题或建议，请联系技术支持。

版本: v1.0
日期: 2026-01-21
"""

        help_window = tk.Toplevel(self.root)
        help_window.title("使用帮助")
        help_window.geometry("600x700")

        help_text_widget = scrolledtext.ScrolledText(
            help_window,
            font=('Arial', 10),
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        help_text_widget.pack(fill=tk.BOTH, expand=True)
        help_text_widget.insert(1.0, help_text)
        help_text_widget.config(state='disabled')


def main():
    """主函数"""
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
