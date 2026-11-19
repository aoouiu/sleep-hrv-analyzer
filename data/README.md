# data/

- `sample_night.csv`：**合成演示数据**，由 `scripts/make_sample.py` 生成，
  仅用于跑通管线。不是真实导出，不要对外宣称是真实数据。
- 真实文件请放这里，但不要提交进 Git（`.gitignore` 已排除 `*.xml`、`*.zip`、`your_*.csv`）：
  - Apple Health：`Export.xml`，用 `src/apple_health.py` 解析
  - 小米 / 华为：厂商隐私中心申请的数据副本，转成 `timestamp,heart_rate_bpm` 的 CSV
