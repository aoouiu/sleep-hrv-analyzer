"""Flask 展示层（第二阶段）：上传导出文件 -> 返回分析 JSON。

分析函数和验证脚本是同一份代码（src/hrv.py / src/sleep_window.py），
Web 层只做上传 + 画图，不重复实现分析。
"""
import sys
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.hrv import windowed_hrv
from src.sleep_window import estimate_sleep_onset

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file uploaded"}), 400
    df = pd.read_csv(f, parse_dates=["timestamp"])
    w = windowed_hrv(df["timestamp"], df["heart_rate_bpm"].to_numpy())
    return jsonify(
        {
            "rows": len(df),
            "sleep_onset": estimate_sleep_onset(w),
            "series": {
                "timestamps": df["timestamp"].dt.strftime("%H:%M").tolist(),
                "hr": df["heart_rate_bpm"].tolist(),
            },
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
