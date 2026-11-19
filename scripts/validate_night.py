"""一晚数据验证：读 CSV -> 5 分钟窗口 HRV -> 入睡窗口 -> 画图 + JSON。

用法：
    python scripts/validate_night.py --input data/sample_night.csv
    python scripts/validate_night.py --input data/your_night.csv
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.hrv import windowed_hrv
from src.sleep_window import estimate_sleep_onset

matplotlib.use("Agg")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/sample_night.csv")
    ap.add_argument("--out-dir", default="outputs")
    args = ap.parse_args()

    df = pd.read_csv(args.input, parse_dates=["timestamp"])
    w = windowed_hrv(df["timestamp"], df["heart_rate_bpm"].to_numpy())
    onset = estimate_sleep_onset(w)

    report = {
        "input": args.input,
        "rows": len(df),
        "range": [str(df["timestamp"].iloc[0]), str(df["timestamp"].iloc[-1])],
        "hr_mean_bpm": round(float(df["heart_rate_bpm"].mean()), 1),
        "hr_min_bpm": round(float(df["heart_rate_bpm"].min()), 1),
        "hr_max_bpm": round(float(df["heart_rate_bpm"].max()), 1),
        "rmssd_mean_ms": round(float(w["rmssd_ms"].mean()), 1) if not w.empty else None,
        "sleep_onset": onset,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "night_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # 图：夜间心率 + 5 分钟窗口 RMSSD，标出估计的入睡点
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(df["timestamp"], df["heart_rate_bpm"], lw=0.8)
    axes[0].set_ylabel("Heart rate (bpm)")
    axes[0].set_title("Night heart rate and RMSSD (5-min windows)")
    axes[1].plot(w["window_start"], w["rmssd_ms"], marker="o", ms=2, lw=0.8)
    axes[1].set_ylabel("RMSSD (ms)")
    if onset.get("sleep_onset"):
        t = pd.to_datetime(onset["sleep_onset"])
        for ax in axes:
            ax.axvline(t, color="red", ls="--", lw=1)
            ax.text(t, ax.get_ylim()[1] * 0.92, " estimated onset", color="red", fontsize=9)
    fig.tight_layout()
    fig.savefig(out_dir / "night_plot.png", dpi=150)
    print(f"saved -> {out_dir / 'night_report.json'} and {out_dir / 'night_plot.png'}")


if __name__ == "__main__":
    main()
