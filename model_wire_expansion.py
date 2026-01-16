# model_wire_expansion.py

def build_expanded_wires_vba(original_curve_name,
                             N_wires,
                             r_wire,
                             desp_val,
                             rot_val_deg,
                             material="PEC",
                             group_name="curve1",
                             invert_rotation=False):
    """
    基于中心样条线，通过平移和旋转生成 N 根编织线并实体化。
    自动处理 N 为奇数（保留中心线）和 N 为偶数（删除中心线）的情况。
    """
    vba_code = []

    # 确定旋转符号
    rot_sign_base = -1.0 if not invert_rotation else 1.0

    # 存储最终需要转为实体的曲线名称列表
    final_wires_list = []

    # === 1. 循环生成/处理每一根线 ===
    for i in range(N_wires):
        # 计算偏移因子
        factor = i - (N_wires - 1) / 2.0

        # 计算具体的物理偏移量
        z_shift = factor * desp_val
        angle_shift = factor * (rot_val_deg * rot_sign_base)

        # --- 情况 A: 中心线 (Factor 为 0) ---
        if abs(factor) < 1e-9:
            final_wires_list.append(original_curve_name)
            continue

        # --- 情况 B: 侧边线 (Factor 不为 0) ---
        # 1. 复制并平移
        unique_name = f"{original_curve_name}_run_{i}"

        vba_code.append(f'With Transform')
        vba_code.append(f'     .Reset')
        vba_code.append(f'     .Name "{group_name}:{original_curve_name}"')
        vba_code.append(f'     .Vector "0", "0", "{z_shift}"')
        vba_code.append(f'     .UsePickedPoints "False"')
        vba_code.append(f'     .InvertPickedPoints "False"')
        vba_code.append(f'     .MultipleObjects "True"')  # 复制
        vba_code.append(f'     .Repetitions "1"')
        vba_code.append(f'     .Transform "Curve", "Translate"')
        vba_code.append(f'End With')

        # 2. 立即重命名 (【核心修正点】)
        # 旧代码: Component.Rename ... (报错)
        # 新代码: Curve.RenameCurveItem "组名", "旧名", "新名"
        # CST 复制后的默认名字是 "原名_1"
        vba_code.append(f'Curve.RenameCurveItem "{group_name}", "{original_curve_name}_1", "{unique_name}"')

        # 3. 原地旋转
        vba_code.append(f'With Transform')
        vba_code.append(f'     .Reset')
        vba_code.append(f'     .Name "{group_name}:{unique_name}"')
        vba_code.append(f'     .Origin "Free"')
        vba_code.append(f'     .Center "0", "0", "0"')
        vba_code.append(f'     .Angle "0", "0", "{angle_shift}"')
        vba_code.append(f'     .MultipleObjects "False"')  # 移动
        vba_code.append(f'     .Transform "Curve", "Rotate"')
        vba_code.append(f'End With')

        final_wires_list.append(unique_name)

    # === 2. 将列表中的所有曲线转化为实体 (Wire) ===
    for idx, curve_name in enumerate(final_wires_list):
        wire_solid_name = f"Solid_{original_curve_name}_{idx}"

        vba_code.append(f'With Wire')
        vba_code.append(f'     .Reset')
        vba_code.append(f'     .Name "{wire_solid_name}"')
        vba_code.append(f'     .Folder "{group_name}"')
        vba_code.append(f'     .Radius "{r_wire}"')
        vba_code.append(f'     .Type "CurveWire"')
        vba_code.append(f'     .Curve "{group_name}:{curve_name}"')
        vba_code.append(f'     .Material "{material}"')
        vba_code.append(f'     .SolidWireModel "True"')
        vba_code.append(f'     .Termination "Natural"')
        vba_code.append(f'     .Mitering "NewMiter"')
        vba_code.append(f'     .AdvancedChainSelection "True"')
        vba_code.append(f'     .Add')
        vba_code.append(f'End With')

    # === 3. 清理工作 ===
    if N_wires % 2 == 0:
        vba_code.append(f'Curve.DeleteCurveItem "{group_name}", "{original_curve_name}"')

    return "\n".join(vba_code)