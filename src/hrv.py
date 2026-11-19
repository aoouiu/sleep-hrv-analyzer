"""HRV 特征：RMSSD / SDNN / pNN50。

输入是逐拍间期（RR 间期，ms）或 1 分钟级心率序列。
真实管线里 RR 间期由 NeuroKit2 / heartpy 从 ECG/PPG 检出；
这里先实现不依赖重型库的纯 numpy 版本，方便在 Notebook 里快速验证。
"""
import numpy as np


def rmssd(rr_ms: np.ndarray) -> float:
    """相邻 RR 间期差值的均方根，单位 ms。副交感活性的常用指标。"""
    rr = np.asarray(rr_ms, dtype=float)
    rr = rr[np.isfinite(rr)]
    if len(rr) < 3:
        return float("nan")
    return float(np.sqrt(np.mean(np.diff(rr) ** 2)))


def sdnn(rr_ms: np.ndarray) -> float:
    rr = np.asarray(rr_ms, dtype=float)
    rr = rr[np.isfinite(rr)]
    if len(rr) < 3:
        return float("nan")
    return float(np.std(rr, ddof=1))


def pnn50(rr_ms: np.ndarray) -> float:
    """相邻 RR 差值 > 50 ms 的比例，%。"""
    rr = np.asarray(rr_ms, dtype=float)
    rr = rr[np.isfinite(rr)]
    if len(rr) < 3:
        return float("nan")
    return float(np.mean(np.abs(np.diff(rr)) > 50.0) * 100.0)


def hr_to_rr_ms(hr_bpm: np.ndarray) -> np.ndarray:
    """心率（bpm）-> RR 间期（ms）的近似换算，仅用于演示数据。

    注意：由分钟级心率反推的 RR 不能替代逐拍 RR，
    真实 HRV 必须用逐拍间期算，这里只是为了让 sample 数据能跑通窗口统计。
    """
    hr = np.asarray(hr_bpm, dtype=float)
    return 60000.0 / np.clip(hr, 30, 200)


def windowed_hrv(timestamps, hr_bpm, window="5min"):
    """5 分钟滑动窗口的 HRV + 平均心率。返回 DataFrame。"""
    import pandas as pd

    df = pd.DataFrame({"timestamp": pd.to_datetime(timestamps), "hr": hr_bpm})
    df = df.set_index("timestamp").sort_index()
    out = []
    for start, grp in df.resample(window):
        if len(grp) < 3:
            continue
        rr = hr_to_rr_ms(grp["hr"].to_numpy())
        out.append(
            {
                "window_start": start,
                "hr_mean": float(grp["hr"].mean()),
                "rmssd_ms": rmssd(rr),
                "sdnn_ms": sdnn(rr),
            }
        )
    return pd.DataFrame(out)
