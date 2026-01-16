import os


def build_spline_from_txt_vba(file_path, spline_name, curve_name="curve1"):
    """
    读取txt文件，返回创建3D Spline所需的完整VBA字符串
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到文件: {file_path}")

    vba_code = []

    # 1. 构建 VBA 头部
    vba_code.append('With Polygon3D')
    vba_code.append('     .Reset')
    vba_code.append('     .Version 10')
    vba_code.append(f'     .Name "{spline_name}"')
    vba_code.append(f'     .Curve "{curve_name}"')
    vba_code.append('     .SetInterpolation "Spline"')  # 关键：设置为样条曲线

    # 2. 读取文件并生成点坐标
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            # 确保一行至少有3个数据 (X Y Z)
            if len(parts) >= 3:
                x, y, z = parts[0], parts[1], parts[2]
                vba_code.append(f'     .Point "{x}", "{y}", "{z}"')

    # 3. 构建 VBA 尾部
    vba_code.append('     .Create')
    vba_code.append('End With')

    # 返回拼接好的字符串
    return "\n".join(vba_code)