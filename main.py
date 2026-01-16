import math
import sys
# 导入系统模块，用于修改 Python 的搜索路径
cst_lib_path = r"D:\Program Files\CST Studio Suite 2024\AMD64\python_cst_libraries"
#  Python 接口库路径（很重要，必须指向你自己电脑上正确的 CST 安装路径）
sys.path.append(cst_lib_path)
# 把 CST 的 Python 库路径添加到 Python 的模块搜索路径中
import cst
import cst.interface
import cst.results
# 导入 CST 的核心接口模块：
#   cst.interface → 用于创建、管理项目
#   cst.results   → 用于读取仿真结果
import time
# 导入时间模块，用于在等待求解器完成时暂停

# 创建一个新的 CST 设计环境（相当于打开 CST 软件）
de = cst.interface.DesignEnvironment()
# 在这个设计环境中新建一个 Microwave Studio 项目（微波工作室）
#prj = de.new_mws()
# 直接打开已存在的项目python_cst
project_path = r"D:\Thesis_Dataset_Programs\CST\python_cst.cst"
prj = de.open_project(project_path)

print(f"已成功打开项目：{project_path}")

# 把新建的项目保存到指定路径（注意：这个文件夹必须已经存在）
#prj.save(r"D:\Thesis_Dataset_Programs\CST\python_cst.cst")
# =========================================================================
# 【新增】全局清空指令：在开始建模前，强制删除默认的组件和曲线组
# =========================================================================


# 设置求解器类型为 频域求解器（HF Eigenmode）
prj.model3d.add_to_history("Set Solver Type", 'ChangeSolverType "HF Frequency Domain"')

# ------------------- 设置几何输入值 -------------------
r_wire = 0.05
D_shield = 1.46
N_carriers = 16
N_wires_per_carrier = 3
alpha_deg = 21.44
lambda_i = 0.02
lambda_m = 0.0455
lambda_e = 0.02
kappa = 0.02
omega = 0.2
gamma = 1.0



# ------------------- 设置中间几何值 -------------------
#  计算屏蔽层半径 R
R_in = D_shield / 2.0
R_out = D_shield /2 + 4*r_wire + lambda_e + lambda_m + lambda_i
# 计算半锭数 K (用于确定单元结构的对称性)
K = N_carriers / 2.0
# 将编织角转换为弧度制，用于三角函数计算
alpha_rad = alpha_deg * math.pi / 180.0

# 单元扇区角度 Theta (度)；一个重复单元在圆周方向占用的角度
Theta_deg = 360.0 / K
# 单元扇区弧长 s_global：单元结构在屏蔽层直径处的周向长度
s_global_arc = math.pi * D_shield / K
# 单元轴向长度 z (节距的一小段)：根据编织角，计算出单元在电缆轴向(Z轴)的长度
z = s_global_arc / math.tan(alpha_rad)

# ---------------------------------------------------

# ------------------- 构建编织层 -------------------
# ---------- 构建扇形区域 ------------
from model_sector import build_sector_vba
sectorVba = build_sector_vba(
    R_out=R_out,
    Theta_deg=Theta_deg,
    R_in=R_in,
    z=z
)

prj.model3d.add_to_history("Set sector", sectorVba)

# ---------- 构建编织线 ------------142开始先构建4个载体的每个线，任何进行平移旋转，在生成实体
import os
# 导入你刚才保存的生成器类
from braid_generator import BraWiGG_Generic_Generator
# 导入上一轮我们写的VBA构建函数 (假设文件名为 model_spline.py)
from model_spline import build_spline_from_txt_vba
# ==========================================
# 1. 调用生成器生成 TXT 文件
# ==========================================
print("正在计算几何数据并生成 TXT 文件...")

# 实例化生成器，传入 main 中已定义的变量
# 假设 main 中的变量名与类参数名一致，如果不一致请自行修改左边的变量名
gen = BraWiGG_Generic_Generator(
    r_wire=r_wire,
    D_shield=D_shield,
    N_carriers=N_carriers,  # 确保 main 里定义了这些变量
    N_wires_per_carrier=N_wires_per_carrier,
    alpha_deg=alpha_deg,
    lambda_i=lambda_i,
    lambda_m=lambda_m,
    lambda_e=lambda_e,
    kappa=kappa,
    omega=omega,
    gamma=gamma
)
# 执行生成，这会在当前目录下创建4个txt文件
gen.generate_files()


# ==========================================
# 2. 将生成的 TXT 导入 CST
# ==========================================
print("正在将 TXT 数据导入 CST...")

# 定义要导入的文件名和你希望在CST中显示的样条曲线名称
# 格式: (文件名, CST中的Spline名称)
files_to_import = [
    ("WiresR_B.txt", "Spline_RB"),
    ("WiresR_F.txt", "Spline_RF"),
    ("WiresL_B.txt", "Spline_LB"),
    ("WiresL_F.txt", "Spline_LF")
]

for txt_filename, spline_name in files_to_import:
    # 获取文件的绝对路径，防止路径错误
    file_full_path = os.path.abspath(txt_filename)

    if os.path.exists(file_full_path):
        # 1. 生成 VBA 字符串 (调用上一轮写的功能)
        spline_vba = build_spline_from_txt_vba(
            file_path=file_full_path,
            spline_name=spline_name,
            curve_name="curve1"  # 确保CST中已经创建了 curve1，或者在这里修改为其他曲线组名
        )

        # 2. 发送给 CST 执行
        # 使用 try-except 防止某个文件出错导致程序崩溃
        try:
            prj.model3d.add_to_history(f"Import {spline_name}", spline_vba)
            print(f"  [成功] {spline_name} 已导入")
        except Exception as e:
            print(f"  [失败] 导入 {spline_name} 时发生 CST 错误: {e}")

    else:
        print(f"  [警告] 找不到文件: {file_full_path}")

# 可选：刷新视图
# prj.model3d.full_history_rebuild()

## ... (前面的代码保持不变，直到 Import Spline 完成) ...

# ==========================================
# 3. 编织线扩展 (生成 4*N 根线)
# ==========================================
from model_wire_expansion import build_expanded_wires_vba

print(f">>> 正在扩展编织线 (每载体 N={N_wires_per_carrier})...")

# --- A. 计算物理参数 ---
# W: 线束宽度。假设紧密排列，宽度 = N * 2 * r_wire，
# 但根据你的描述公式 desp = W / ..., 这里 W 通常指单根线的节距宽度或者是特定的带状宽度。
# 按照你的示例逻辑 "desp是平移量"，通常取 W 为单根线的特征宽度或用户指定宽度。
# **假设**: 这里的变换是基于单根线间距的，所以 W 这里取 2*r_wire (两倍半径即直径)
W = 2 * r_wire+kappa

# R_base 计算
R_base = D_shield / 2.0 + r_wire + lambda_i

# desp 计算
# 注意: math.sin 接收弧度
desp = W / (2 * math.sin(alpha_rad))

# rot 计算 (单位: 度)
# rot = (W / (2 * cos(alpha)) / R_base) * (180/pi)
rot_val = (W / (2 * math.cos(alpha_rad)) / R_base) * (180 / math.pi)

print(f"   [参数] R_base: {R_base:.4f} mm")
print(f"   [参数] desp (Z轴平移): {desp:.4f} mm")
print(f"   [参数] rot (旋转角度): {rot_val:.4f} deg")

# --- B. 循环处理 4 组载体 ---
# 配置列表: (样条线名, 是否反转旋转逻辑)
# 左旋载体 (LB, LF) 的螺旋方向与右旋 (RB, RF) 相反。
# 通常如果 RB 是 (Z+, Rot-), 那么 LB 应该是 (Z+, Rot+)。
# 因此将 LB/LF 的 invert_rotation 设为 True。
carriers_config = [
    ("Spline_RB", False),
    ("Spline_RF", False),
    ("Spline_LB", True),
    ("Spline_LF", True)
]

for spline_name, invert_flag in carriers_config:
    print(f"   正在处理载体: {spline_name} ...")

    # 生成 VBA
    expansion_vba = build_expanded_wires_vba(
        original_curve_name=spline_name,
        N_wires=N_wires_per_carrier,
        r_wire=r_wire,
        desp_val=desp,
        rot_val_deg=rot_val,
        material="PEC",
        group_name="curve1",
        invert_rotation=invert_flag
    )

    # 发送给 CST 执行
    # 使用唯一的 Step Name 防止覆盖
    step_name = f"Expand_{spline_name}"
    try:
        prj.model3d.add_to_history(step_name, expansion_vba)
        print(f"   [成功] {spline_name} 扩展完成")
    except Exception as e:
        print(f"   [失败] {spline_name} 扩展出错: {e}")

print("\n=== 所有编织线生成完毕 ===")













