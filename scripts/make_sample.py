"""生成 data/sample_night.csv：合成演示的一晚数据。

形态（典型夜间曲线，非真实记录）：
- 22:30-23:15 清醒：心率 ~72 bpm，小幅波动
- 23:15 入睡：心率在 ~20 分钟内降到 ~58 bpm，此后整夜 55-62 bpm
- 05:30 左右一次短暂醒转：心率短暂升到 ~68 bpm
- 06:45 起床前：心率回升到 ~70 bpm

每分钟 1 个点，含 timestamp, heart_rate_bpm 两列。
不要把这份文件当作真实数据使用，见 README 和 data/README.md。
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
start = pd.Timestamp("2026-11-19 22:30")
minutes = pd.date_range(start, periods=8 * 60 + 31, freq="1min")

hr = []
for t in minutes:
    mins = (t - start).total_seconds() / 60
    if mins < 45:  # 清醒
        base = 72
    elif mins < 65:  # 入睡过渡
        base = 72 - (mins - 45) * 0.7
    elif 300 <= mins < 315:  # 凌晨短暂醒转
        base = 68
    elif mins >= 495:  # 起床前
        base = 70
    else:  # 睡眠
        base = 58 + 2 * np.sin(mins / 45.0)
    hr.append(base + rng.normal(0, 1.8))

df = pd.DataFrame({"timestamp": minutes, "heart_rate_bpm": np.round(hr, 1)})
df.to_csv("data/sample_night.csv", index=False)
print(f"wrote data/sample_night.csv: {len(df)} rows, {df['timestamp'].iloc[0]} -> {df['timestamp'].iloc[-1]}")
print(df.describe())
