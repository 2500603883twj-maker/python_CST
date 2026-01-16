import numpy as np
import sys


class BraWiGG_Generic_Generator:
    def __init__(self,
                 r_wire=0.05,
                 D_shield=1.46,
                 N_carriers=16,
                 N_wires_per_carrier=3,
                 alpha_deg=21.44,
                 lambda_i=0.02,
                 lambda_m=0.0455,
                 lambda_e=0.02,
                 kappa=0.02,
                 omega=0.2,
                 gamma=1.0):

        # ================= 1. 基础参数初始化 =================
        self.r_wire = float(r_wire)
        self.D_shield = float(D_shield)
        self.N_carriers = int(N_carriers)
        self.N_wires_per_carrier = int(N_wires_per_carrier)
        self.alpha_deg = float(alpha_deg)

        # 间隙参数
        self.lambda_i = float(lambda_i)
        self.lambda_m = float(lambda_m)
        self.lambda_e = float(lambda_e)
        self.kappa = float(kappa)

        # 波形控制参数
        self.omega = float(omega)
        self.gamma = float(gamma)
        self.dd = 0.2

        # ================= 2. 几何参数动态计算 =================
        self.R_inner = self.D_shield / 2.0

        # 半径界限
        self.R_low = self.R_inner + self.r_wire + self.lambda_i
        self.R_high = self.R_inner + 3.0 * self.r_wire + self.lambda_i + self.lambda_m
        self.h_wave = self.R_high - self.R_low

        # 螺旋参数
        self.K = self.N_carriers / 2.0
        self.Theta_deg = 360.0 / self.K
        self.s = np.pi * self.D_shield / self.K
        self.z_sector = self.s / np.tan(np.deg2rad(self.alpha_deg))

        # 偏移量
        # z_sector ≈ 1.46mm, z_shift_half ≈ 0.73mm
        self.z_shift_half = self.z_sector / 2.0
        self.theta_shift_half = self.Theta_deg / 2.0

        # 计算辅助变量 (L, k, x0)
        arc_len = self.R_low * np.deg2rad(self.Theta_deg)
        self.L = np.sqrt(arc_len ** 2 + self.z_sector ** 2)
        self.d = self.L * self.dd / 4.0
        term = self.omega ** 2 - (self.h_wave / 2.0 - self.omega) ** 2
        self.k = np.sqrt(self.d ** 2 / term) if term > 0 else 1.0
        self.x0 = self.L / 4.0 - self.d

        # ==========================================================
        # [核心修正] 生成窗口控制
        # 1. Start Offset = 0.5: 跳过前0.5个周期(Z从 -0.73 跳到 0.0)
        # 2. Sectors Gen = 2.0: 生成长度为 2.0 * 1.46 = 2.92mm
        # 结果: WiresR_B 将从 Z=0.0 (Low) 开始，到 Z=2.92 (Low) 结束
        # ==========================================================
        self.t_start_offset = 0.5
        self.num_sectors_gen = 2.0

        self.num_points = 2000
        # 全局坐标原点 (数学上的 t=0 处) 依然保持为 -0.73
        self.z_start_global = -self.z_shift_half

    def check_validity(self):
        h_check = 2.0 * self.r_wire + self.lambda_m
        gamma_min = h_check / 2.0
        if self.gamma < gamma_min:
            return False
        return True

    def _get_bump(self, t_global):
        sector_idx = int(t_global)
        t_local = t_global - sector_idx

        xx = t_local * self.L
        if t_local > 0.5:
            xx_calc = self.L - xx
        else:
            xx_calc = xx

        threshold_mid = 0.25
        threshold_rise_start = 0.25 - self.dd / 4.0
        threshold_rise_end = 0.25 + self.dd / 4.0

        t_compare = t_local if t_local <= 0.5 else (1.0 - t_local)

        if t_compare < threshold_rise_start:
            return 0.0
        elif t_compare < threshold_mid:
            val = self.omega ** 2 - ((xx_calc - self.x0) ** 2) / (self.k ** 2)
            return self.omega - np.sqrt(max(0, val))
        elif t_compare < threshold_rise_end:
            val = self.omega ** 2 - ((xx_calc - self.x0 - 2 * self.d) ** 2) / (self.k ** 2)
            return self.h_wave - self.omega + np.sqrt(max(0, val))
        else:
            return self.h_wave

    def generate_files(self):
        if not self.check_validity():
            return

        print(f"开始生成几何文件 (修正版)...")
        print(f"  > 起始偏移 (Offset): {self.t_start_offset} sectors")
        print(f"  > 生成长度 (Duration): {self.num_sectors_gen} sectors")
        print(f"  > 预计 WiresR_B Z轴范围: 0.00 mm -> {(self.num_sectors_gen * self.z_sector):.2f} mm")

        data_RB = []
        data_RF = []
        data_LB = []
        data_LF = []

        path_RB_base = []

        # ==========================================
        # 1. 计算基准路径
        # ==========================================
        for i in range(self.num_points):
            t_norm = i / (self.num_points - 1)

            # [修正] 加上起始偏移量
            # t_global 现在从 0.5 运行到 2.5
            t_global = self.t_start_offset + t_norm * self.num_sectors_gen

            theta_deg = self.Theta_deg * t_global
            z_val = self.z_start_global + self.z_sector * t_global

            bump = self._get_bump(t_global)

            path_RB_base.append({
                'theta': theta_deg,
                'z': z_val,
                'bump': bump
            })

        # ==========================================
        # 2. 生成 WiresR_B (基准)
        # ==========================================
        for p in path_RB_base:
            r_val = self.R_high - p['bump']
            x = r_val * np.cos(np.deg2rad(p['theta']))
            y = r_val * np.sin(np.deg2rad(p['theta']))
            z = p['z']
            data_RB.append(f"{x:.6f} {y:.6f} {z:.6f}")

        # ==========================================
        # 3. 生成 WiresR_F (右向前)
        # ==========================================
        for p in path_RB_base:
            z_new = p['z'] - self.z_shift_half
            theta_new = p['theta'] + self.theta_shift_half
            r_val = self.R_low + p['bump']
            x = r_val * np.cos(np.deg2rad(theta_new))
            y = r_val * np.sin(np.deg2rad(theta_new))
            data_RF.append(f"{x:.6f} {y:.6f} {z_new:.6f}")

        # ==========================================
        # 4. 生成 WiresL_B (左向后)
        # ==========================================
        cos_neg = np.cos(np.deg2rad(-self.Theta_deg))
        sin_neg = np.sin(np.deg2rad(-self.Theta_deg))
        path_LB_geo = []

        for p in path_RB_base:
            r_val = self.R_low + p['bump']
            x_rb = r_val * np.cos(np.deg2rad(p['theta']))
            y_rb = r_val * np.sin(np.deg2rad(p['theta']))
            z_rb = p['z']

            x_mir = -x_rb
            y_mir = y_rb
            x_final = x_mir * cos_neg - y_mir * sin_neg
            y_final = x_mir * sin_neg + y_mir * cos_neg
            z_final = z_rb

            data_LB.append(f"{x_final:.6f} {y_final:.6f} {z_final:.6f}")
            path_LB_geo.append({'theta_orig': p['theta'], 'z': z_rb, 'bump': p['bump']})

        # ==========================================
        # 5. 生成 WiresL_F (左向前)
        # ==========================================
        for p in path_LB_geo:
            r_val = self.R_high - p['bump']
            x_rb = r_val * np.cos(np.deg2rad(p['theta_orig']))
            y_rb = r_val * np.sin(np.deg2rad(p['theta_orig']))
            x_mir = -x_rb
            y_mir = y_rb
            x_lb = x_mir * cos_neg - y_mir * sin_neg
            y_lb = x_mir * sin_neg + y_mir * cos_neg

            curr_theta = np.degrees(np.arctan2(y_lb, x_lb))
            theta_lf = curr_theta - self.theta_shift_half
            z_lf = p['z'] - self.z_shift_half

            x_final = r_val * np.cos(np.deg2rad(theta_lf))
            y_final = r_val * np.sin(np.deg2rad(theta_lf))
            data_LF.append(f"{x_final:.6f} {y_final:.6f} {z_lf:.6f}")

        # 写入文件
        self._write_file("WiresR_B.txt", data_RB)
        self._write_file("WiresR_F.txt", data_RF)
        self._write_file("WiresL_B.txt", data_LB)
        self._write_file("WiresL_F.txt", data_LF)
        print("生成完毕。")

    def _write_file(self, fname, data):
        with open(fname, 'w') as f:
            f.write("\n".join(data))


if __name__ == '__main__':
    gen = BraWiGG_Generic_Generator()
    gen.generate_files()