"""解析 Apple Health 导出文件 Export.xml。

来源：iPhone 健康 App -> 右上角头像 -> 导出全部健康数据，
解压 ZIP 后得到 export.xml。

提取三类记录：
- HKQuantityTypeIdentifierHeartRate（心率，bpm）
- HKQuantityTypeIdentifierHeartRateVariabilitySDNN（HRV SDNN，ms）
- HKCategoryTypeIdentifierSleepAnalysis（睡眠分析，InBed / Asleep*）

用法：
    python -m src.apple_health data/export.xml --out data/apple_health_night.csv
"""
import argparse
import xml.etree.ElementTree as ET

import pandas as pd

HEART_RATE = "HKQuantityTypeIdentifierHeartRate"
HRV_SDNN = "HKQuantityTypeIdentifierHeartRateVariabilitySDNN"
SLEEP = "HKCategoryTypeIdentifierSleepAnalysis"


def parse_export_xml(path: str) -> dict[str, pd.DataFrame]:
    tree = ET.parse(path)
    root = tree.getroot()

    hr_rows, hrv_rows, sleep_rows = [], [], []
    for rec in root.iter("Record"):
        rtype = rec.get("type")
        start = rec.get("startDate")
        end = rec.get("endDate")
        if rtype == HEART_RATE:
            hr_rows.append({"timestamp": start, "heart_rate_bpm": float(rec.get("value"))})
        elif rtype == HRV_SDNN:
            hrv_rows.append({"timestamp": start, "sdnn_ms": float(rec.get("value"))})
        elif rtype == SLEEP:
            sleep_rows.append(
                {"start": start, "end": end, "value": rec.get("value"), "source": rec.get("sourceName")}
            )

    def _df(rows, time_col="timestamp"):
        df = pd.DataFrame(rows)
        if not df.empty:
            df[time_col] = pd.to_datetime(df[time_col])
            df = df.sort_values(time_col).reset_index(drop=True)
        return df

    return {
        "heart_rate": _df(hr_rows),
        "hrv_sdnn": _df(hrv_rows),
        "sleep": _df(sleep_rows, "start"),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("xml_path")
    ap.add_argument("--out", default="data/apple_health_night.csv")
    args = ap.parse_args()

    out = parse_export_xml(args.xml_path)
    hr = out["heart_rate"]
    print(f"heart_rate: {len(hr)} rows")
    print(f"hrv_sdnn:   {len(out['hrv_sdnn'])} rows")
    print(f"sleep:      {len(out['sleep'])} rows")
    if not hr.empty:
        print(hr.head())
        hr.to_csv(args.out, index=False)
        print(f"saved -> {args.out}")
