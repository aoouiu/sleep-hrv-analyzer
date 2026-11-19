"""入睡窗口估计：心率下降 + RMSSD 上升的联合规则。

思路（待真实数据验证的初版阈值）：
- 取睡前清醒基线：窗口开始前 30 分钟的平均心率 / RMSSD。
- 入睡 = 连续 3 个 5 分钟窗口同时满足：
  心率比基线低 >= 5 bpm，且 RMSSD 比基线高 >= 20%。
- 入睡窗口 = 第一个满足窗口的起点到下一个窗口起点之间。

这只是可验证的起点，不是结论。阈值要在几晚真实数据上调，
或改用 SleepECG 的预训练分类器做对照。
"""
import pandas as pd


def estimate_sleep_onset(windowed: pd.DataFrame, hr_drop_bpm=5.0, rmssd_rise_pct=0.20) -> dict:
    if windowed.empty or len(windowed) < 6:
        return {"sleep_onset": None, "reason": "not enough windows"}

    w = windowed.reset_index(drop=True)
    baseline_hr = w["hr_mean"].iloc[:6].mean()
    baseline_rmssd = w["rmssd_ms"].iloc[:6].mean()

    for i in range(6, len(w) - 2):
        chunk = w.iloc[i : i + 3]
        # 用 3 个窗口的均值判断，不用逐窗口最小值：
        # 分钟级心率反推的 RMSSD 噪声很大，逐窗口卡阈值会把真入睡点漏掉。
        hr_ok = baseline_hr - chunk["hr_mean"].mean() >= hr_drop_bpm
        rmssd_ok = chunk["rmssd_ms"].mean() / baseline_rmssd - 1.0 >= rmssd_rise_pct
        if hr_ok and rmssd_ok:
            return {
                "sleep_onset": str(w["window_start"].iloc[i]),
                "baseline_hr_bpm": round(float(baseline_hr), 1),
                "baseline_rmssd_ms": round(float(baseline_rmssd), 1),
                "onset_hr_bpm": round(float(chunk["hr_mean"].iloc[0]), 1),
                "onset_rmssd_ms": round(float(chunk["rmssd_ms"].iloc[0]), 1),
                "rule": f"hr_drop>={hr_drop_bpm}bpm for 3x5min AND rmssd_rise>={rmssd_rise_pct:.0%}",
            }
    return {"sleep_onset": None, "reason": "no 3-window run met the rule"}
