# sleep-hrv-analyzer

用夜间 PPG 心率 + HRV 判断睡眠 / 清醒、估算入睡窗口的最小可行分析管线。

核心假设：**夜间心率能否稳定区分睡眠 / 清醒，并给出有意义的入睡窗口**。
先在 Notebook / 脚本里用数据验证这个假设，跑通后再 Web 化，不从零造轮子。

## 技术路线

- **分析核心：Python**，不用从零实现 HRV 或睡眠分期
  - `NeuroKit2`：R 波检测、HRV 特征（RMSSD / SDNN / pNN50 等）
  - `heartpy`：心率分析工具箱
  - `pyPPG`：PPG 信号标准化分析
  - `BioPsyKit`：基于体动（IMU）的睡眠 / 清醒预测、睡眠端点计算
  - `SleepECG`：基于 HRV 的睡眠分期，自带预训练分类器 + 公开 PSG 数据集下载
- **验证先行**：先用 `scripts/validate_night.py` 跑一晚数据、画图、调阈值
- **Web 是第二阶段**：`app/` 是 Flask + Chart.js 的轻量展示层，
  分析函数和验证阶段是同一份代码，不重复建设

## 目录

```
src/
  apple_health.py   # 解析 Apple Health Export.xml -> 心率 / HRV / 睡眠记录
  hrv.py            # RMSSD / SDNN / pNN50，5 分钟滑动窗口
  sleep_window.py   # 入睡窗口：心率下降 + RMSSD 上升的联合规则
scripts/
  validate_night.py # 一晚数据验证：读 CSV -> 算 HRV -> 画图 -> 输出 JSON
  make_sample.py    # 生成 data/sample_night.csv（合成演示数据，见下）
data/
  sample_night.csv  # 合成演示的一晚数据，仅用于跑通管线
app/
  app.py            # Flask /analyze 接口：上传导出文件 -> 返回 JSON
  templates/index.html  # Chart.js：夜间心率曲线 + 入睡窗口
tests/
  test_hrv.py
```

## 快速开始

```bash
pip install -r requirements.txt
python scripts/validate_night.py --input data/sample_night.csv
# 输出：outputs/night_report.json + outputs/night_plot.png
```

Web 展示（可选）：

```bash
python app/app.py
# 打开 http://127.0.0.1:5000 ，上传 CSV 或 Apple Health Export.xml
```

## 数据来源

按手头设备选一条路，解析器已经按这个口径写好：

| 设备 | 导出路径 | 本项目入口 |
| --- | --- | --- |
| iPhone + Apple Watch | 健康 App -> 导出全部健康数据（`Export.xml` 的 ZIP） | `src/apple_health.py`：提取 `HKQuantityTypeIdentifierHeartRate`、`HeartRateVariabilitySDNN`、`HKCategoryTypeIdentifierSleepAnalysis` |
| 小米 / 华为手环 | 厂商隐私中心申请数据副本（小米多为 Excel/CSV，华为为 JSON） | 先转成 `timestamp,heart_rate_bpm` 的 CSV，再走 `validate_night.py` |
| Gadgetbridge（Android） | 手环直连本地导出数据库 | 同上，转 CSV 后接入 |
| 没有设备 | 公开 PSG 数据集（SleepECG 自带下载） | 先用金标准数据验证算法，不用等自己攒几周数据 |

## 关于 `data/sample_night.csv` —— 请先读这段

这份样本是**合成演示数据**，不是任何人的真实导出：
用脚本按“睡前心率 ~72 bpm、入睡后降到 ~58 bpm、RMSSD 入睡后上升”
的典型形态生成的，目的是让管线、画图和 Web 接口不依赖真实设备也能跑通。

**不要把它当作真实数据发给审核 / 评审。**
真实数据只有一条合法来源：你自己设备的导出文件。
拿到真实导出后，把文件放到 `data/`，跑同一条命令即可替换验证：

```bash
python scripts/validate_night.py --input data/your_night.csv
```

真实导出截图 / 样本的获取方法：iPhone 健康 App -> 右上角头像 ->
导出全部健康数据，解压后把 `Export.xml` 发给解析器；
或在手环厂商隐私中心申请数据副本。

## 当前状态

- [x] Apple Health 解析、心率 + HRV 特征、入睡窗口规则、绘图、Flask 接口骨架
- [ ] 接入真实的一晚 / 多晚导出数据，验证阈值
- [ ] 接入 SleepECG 公开 PSG 数据做对照验证
- [ ] 多晚趋势：恢复评分、入睡窗口稳定性

## 不做的事（MVP 边界）

不做自动同步、实时反馈、厂商 API 聚合（如 Terra）。
先用手动导出的文件证明“分析是否有用”，再谈产品化。
