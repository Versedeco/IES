#!/usr/bin/env python3
"""
IES流明值修改工具
可以批量修改IES文件的流明值，生成不同亮度版本的IES文件
"""

import os
import sys
import argparse
from pathlib import Path

def read_ies_file(filepath):
    """读取IES文件"""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.readlines()

def find_photometric_line(lines):
    """找到光度数据行的索引"""
    for i, line in enumerate(lines):
        if 'TILT=NONE' in line or 'TILT=INCLUDE' in line:
            # 光度数据在TILT行的下一行
            return i + 1
    raise ValueError("未找到TILT行，可能不是有效的IES文件")

def get_current_lumens(lines):
    """获取当前流明值"""
    idx = find_photometric_line(lines)
    values = lines[idx].split()
    return float(values[1])

def modify_lumens(lines, new_lumens):
    """
    修改流明值

    Args:
        lines: IES文件行列表
        new_lumens: 新的流明值

    Returns:
        modified_lines: 修改后的行列表
        old_lumens: 原流明值
    """
    idx = find_photometric_line(lines)
    values = lines[idx].split()

    old_lumens = float(values[1])
    values[1] = f"{float(new_lumens):.1f}"

    # 重新组合，保持格式
    lines[idx] = ' '.join(values) + '\n'

    return lines, old_lumens

def save_ies_file(filepath, lines):
    """保存IES文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def single_modify(input_file, output_file, new_lumens):
    """
    修改单个IES文件

    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        new_lumens: 新的流明值
    """
    lines = read_ies_file(input_file)
    modified_lines, old_lumens = modify_lumens(lines, new_lumens)
    save_ies_file(output_file, modified_lines)

    ratio = new_lumens / old_lumens

    print(f"✅ 流明值已修改")
    print(f"   原值: {old_lumens:.0f} lm")
    print(f"   新值: {new_lumens:.0f} lm")
    print(f"   比例: {ratio:.2f}x")
    print(f"   输出: {output_file}")

def batch_modify(input_file, lumens_list, output_dir=None):
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
    base_lumens = get_current_lumens(base_lines)
    base_name = input_path.stem

    print(f"\n{'='*70}")
    print(f"  📄 批量修改IES流明值")
    print(f"{'='*70}")
    print(f"基准文件: {input_file}")
    print(f"基准流明: {base_lumens:.0f} lm")
    print(f"输出目录: {output_dir}")
    print(f"生成数量: {len(lumens_list)}")
    print(f"{'-'*70}\n")

    results = []

    for lumens in lumens_list:
        # 复制并修改
        modified_lines = base_lines.copy()
        modified_lines, old_lumens = modify_lumens(modified_lines, lumens)

        # 生成输出文件名
        output_file = output_dir / f"{base_name}_{int(lumens)}lm.ies"

        # 保存
        save_ies_file(output_file, modified_lines)

        ratio = lumens / base_lumens
        results.append((output_file, lumens, ratio))

        print(f"✅ {output_file.name:40} {lumens:6.0f} lm  ({ratio:5.2f}x)")

    print(f"\n{'-'*70}")
    print(f"✅ 完成！共生成 {len(results)} 个IES文件")
    print(f"{'='*70}\n")

    return results

def analyze_ies(filepath):
    """分析IES文件的基本信息"""
    lines = read_ies_file(filepath)
    idx = find_photometric_line(lines)
    values = lines[idx].split()

    print(f"\n{'='*70}")
    print(f"  📊 IES文件分析")
    print(f"{'='*70}")
    print(f"文件路径: {filepath}")
    print(f"{'-'*70}")
    print(f"灯具数量:       {values[0]}")
    print(f"总流明:         {values[1]} lm  ← 关键参数")
    print(f"倍增因子:       {values[2]}")
    print(f"水平角数量:     {values[3]}")
    print(f"垂直角数量:     {values[4]}")
    print(f"光度类型:       {values[5]} (1=C, 2=B, 3=A)")
    print(f"单位类型:       {values[6]} (1=feet, 2=meters)")
    print(f"灯具宽度:       {values[7]} (单位)")
    print(f"灯具长度:       {values[8]} (单位)")
    print(f"灯具高度:       {values[9]} (单位)")
    print(f"{'='*70}\n")

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='修改IES文件的流明值',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：

  1. 分析IES文件
     python modify_ies_lumens.py luminaire.ies --analyze

  2. 修改单个文件
     python modify_ies_lumens.py luminaire.ies -l 2000 -o luminaire_2000lm.ies
  
  3. 批量生成系列文件
     python modify_ies_lumens.py luminaire.ies -b 500 1000 1500 2000
  
  4. 生成调光系列（指定输出目录）
     python modify_ies_lumens.py luminaire.ies -b 250 500 750 1000 -d output/

  5. 生成百分比系列
     python modify_ies_lumens.py luminaire.ies --percent 25 50 75 100
        """
    )

    parser.add_argument('input', help='输入IES文件路径')
    parser.add_argument('-l', '--lumens', type=float, help='新的流明值（单文件模式）')
    parser.add_argument('-o', '--output', help='输出文件路径（单文件模式）')
    parser.add_argument('-b', '--batch', nargs='+', type=float,
                       help='批量模式：流明值列表')
    parser.add_argument('-p', '--percent', nargs='+', type=float,
                       help='批量模式：基于原值的百分比列表（例: 50 75 100 150）')
    parser.add_argument('-d', '--dir', help='批量模式的输出目录')
    parser.add_argument('-a', '--analyze', action='store_true',
                       help='仅分析IES文件，不做修改')

    args = parser.parse_args()

    # 检查文件是否存在
    if not os.path.exists(args.input):
        print(f"❌ 错误：文件不存在: {args.input}")
        sys.exit(1)

    try:
        if args.analyze:
            # 分析模式
            analyze_ies(args.input)

        elif args.percent:
            # 百分比批量模式
            lines = read_ies_file(args.input)
            base_lumens = get_current_lumens(lines)
            lumens_list = [base_lumens * (p / 100.0) for p in args.percent]
            batch_modify(args.input, lumens_list, args.dir)

        elif args.batch:
            # 批量模式
            batch_modify(args.input, args.batch, args.dir)

        elif args.lumens:
            # 单文件模式
            output = args.output or f"{Path(args.input).stem}_{int(args.lumens)}lm.ies"
            single_modify(args.input, output, args.lumens)

        else:
            # 没有指定操作，显示帮助
            parser.print_help()
            print("\n提示：使用 --analyze 查看IES文件信息")
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
