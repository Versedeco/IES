"""
IES文件格式验证工具
用于检查IES文件是否符合IES-LM-63标准（特别是角度顺序）
"""

import sys
from pathlib import Path


def validate_ies_file(ies_path):
    """验证IES文件格式"""
    print("=" * 70)
    print("  IES文件格式验证工具")
    print("=" * 70)
    print()

    path = Path(ies_path)

    # 检查文件是否存在
    if not path.exists():
        print(f"❌ 错误：文件不存在 - {ies_path}")
        return False

    print(f"📁 文件: {path.name}")
    print(f"📂 路径: {path.parent}")
    print(f"📏 大小: {path.stat().st_size / 1024:.2f} KB")
    print()

    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False

    # 查找TILT行
    tilt_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('TILT='):
            tilt_idx = i
            break

    if tilt_idx == -1:
        print("❌ 错误：未找到TILT行")
        return False

    print(f"✅ 找到TILT行（第{tilt_idx + 1}行）")

    # 解析数据行（TILT后第一行）
    data_line_idx = tilt_idx + 1
    if data_line_idx >= len(lines):
        print("❌ 错误：缺少数据行")
        return False

    data_line = lines[data_line_idx].strip()
    data_parts = data_line.split()

    if len(data_parts) < 10:
        print(f"❌ 错误：数据行格式不正确（字段数不足）")
        return False

    try:
        n_lamps = int(data_parts[0])
        lumens = float(data_parts[1])
        multiplier = float(data_parts[2])
        n_horizontal = int(data_parts[3])
        n_vertical = int(data_parts[4])
        photometric_type = int(data_parts[5])
        units_type = int(data_parts[6])
        width = float(data_parts[7])
        length = float(data_parts[8])
        height = float(data_parts[9])
    except ValueError as e:
        print(f"❌ 错误：数据行解析失败 - {e}")
        return False

    print(f"\n📊 IES参数:")
    print(f"  流明值: {lumens:.1f} lm")
    print(f"  水平角数量: {n_horizontal}")
    print(f"  垂直角数量: {n_vertical}")
    print(f"  光度类型: {photometric_type}")
    print(f"  灯具尺寸: {width}×{length}×{height} m")
    print()

    # 解析水平角度
    h_angles_idx = data_line_idx + 1
    h_angles_line = lines[h_angles_idx].strip()
    h_angles = [float(x) for x in h_angles_line.split()]

    if len(h_angles) != n_horizontal:
        print(f"❌ 错误：水平角度数量不匹配（期望{n_horizontal}，实际{len(h_angles)}）")
        return False

    # 验证水平角度递增
    h_angles_valid = True
    for i in range(1, len(h_angles)):
        if h_angles[i] < h_angles[i-1]:
            print(f"❌ 错误：水平角度未递增")
            print(f"   位置 {i}: {h_angles[i-1]:.1f}° → {h_angles[i]:.1f}° （递减！）")
            h_angles_valid = False
            break

    if h_angles_valid:
        print(f"✅ 水平角度顺序正确")
        print(f"   范围: {h_angles[0]:.1f}° → {h_angles[-1]:.1f}°")
        print(f"   步长: {h_angles[1] - h_angles[0]:.1f}° (平均)")

    # 解析垂直角度
    v_angles_idx = h_angles_idx + 1
    v_angles_line = lines[v_angles_idx].strip()
    v_angles = [float(x) for x in v_angles_line.split()]

    if len(v_angles) != n_vertical:
        print(f"❌ 错误：垂直角度数量不匹配（期望{n_vertical}，实际{len(v_angles)}）")
        return False

    # 验证垂直角度递增（这是UE报错的关键！）
    v_angles_valid = True
    for i in range(1, len(v_angles)):
        if v_angles[i] < v_angles[i-1]:
            print(f"❌ 错误：垂直角度未递增 ⚠️ 这会导致UE导入失败！")
            print(f"   位置 {i}: {v_angles[i-1]:.1f}° → {v_angles[i]:.1f}° （递减！）")
            v_angles_valid = False
            break

    if v_angles_valid:
        print(f"✅ 垂直角度顺序正确 ✨ UE可以导入")
        print(f"   范围: {v_angles[0]:.1f}° → {v_angles[-1]:.1f}°")
        print(f"   步长: {v_angles[1] - v_angles[0]:.1f}° (平均)")

    print()

    # 最终结果
    all_valid = h_angles_valid and v_angles_valid

    print("=" * 70)
    if all_valid:
        print("✅ 验证通过！此IES文件符合IES-LM-63标准")
        print("✅ 可以在Unreal Engine中正常导入")
    else:
        print("❌ 验证失败！此IES文件不符合标准")
        print("❌ 在Unreal Engine中导入会失败")
        print()
        print("💡 建议：使用v2.1或更新版本的程序重新生成IES文件")
    print("=" * 70)

    return all_valid


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python validate_ies.py <IES文件路径>")
        print()
        print("示例:")
        print('  python validate_ies.py "D:/TestLighting/test.ies"')
        print()
        input("按回车键退出...")
        sys.exit(1)

    ies_path = sys.argv[1]
    result = validate_ies_file(ies_path)

    print()
    input("按回车键退出...")

    sys.exit(0 if result else 1)
