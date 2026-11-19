# Devin Bot 任务清单 — sleep-hrv-analyzer 第一批

仓库：https://github.com/aoouiu/sleep-hrv-analyzer（分支 master）
现状：Apple Health 解析、RMSSD/SDNN、入睡窗口规则、验证脚本、Flask + Chart.js
已验证：`data/sample_night.csv`（合成演示数据，511 行）跑通，检出入睡 23:20，
与设定值 23:15 差 5 分钟。真实导出尚未接入（无手表，Apple Health 同步 0 条）。

## 给 Devin 的主任务 Prompt（直接复制可用）

> 你是这个仓库的开发工程师。先读 README.md 和 docs/devin-tasks.md，
> 再按顺序做下面的 Issue #1 → #5，一次只做一个，做完一个就提交并跑通验证再做下一个。
>
> 约束：
> - 只改 Issue 里点名的文件，不要重构整个仓库，不要换框架（Python 分析核心 + Flask + Chart.js 不变）。
> - 不要从零实现 HRV 或睡眠分期：优先用 NeuroKit2、heartpy、SleepECG、BioPsyKit 这些成熟库。
> - 不要提交任何真实健康数据：`data/` 里只保留合成样本和小的 fixture，真实 `Export.xml` / `*.zip` / `your_*.csv` 绝不进仓库（`.gitignore` 已排除）。
> - 每个 Issue 做完必须能跑 `python scripts/validate_night.py --input data/sample_night.csv` 且输出的入睡时间仍在 23:10–23:30 之间；新增测试必须用 pytest 跑通。
> - 每个 Issue 结束写一段简短总结：改了什么、怎么验证的、还有什么没做。

---

## Issue #1 — 用逐拍 RR 间期替换分钟级心率反推的 RMSSD（优先做）

**为什么：** 现在 `src/hrv.py:hr_to_rr_ms()` 是拿分钟级心率反推 RR 再算 RMSSD，
只是能跑通管线的近似值，噪声很大（见验证图下半部分的 RMSSD 抖动）。
真实 HRV 必须用逐拍间期算。

**做：**
- 在 `src/hrv.py` 新增 `rr_from_ecg_ppg()`：优先用 NeuroKit2（`nk.ecg_peaks` / `nk.ppg_peaks`）
  检出逐拍间期，NeuroKit 不可用时回退到 heartpy；保留旧的 `hr_to_rr_ms()` 仅作演示回退，并打上 deprecation 注释。
- `windowed_hrv()` 增加参数 `rr_ms=None`：传入逐拍 RR 时直接用它算 RMSSD/SDNN/pNN50，不再反推。
- 在 `scripts/validate_night.py` 增加 `--rr-csv` 可选项（列：`timestamp,rr_ms`），有就走逐拍路径，没有就走现有路径。

**不做：** 不改入睡窗口规则本身，不接 SleepECG（那是 #2）。

**验收：**
- 构造一段合成 RR 序列（例如 800±30 ms 的正弦波动 + 已知突变），RMSSD/SDNN 与手工计算误差 < 1 ms。
- `pytest tests/test_hrv.py` 通过；`validate_night.py` 在样本数据上仍检出 23:10–23:30。

**涉及文件：** `src/hrv.py`、`scripts/validate_night.py`、`tests/test_hrv.py`、`requirements.txt`

## Issue #2 — 接 SleepECG 公开 PSG 数据做对照验证

**为什么：** 只用一晚合成数据调阈值不可信，需要金标准数据回答
“心率能在多大程度上区分睡眠/清醒”。

**做：**
- 新增 `scripts/validate_psg.py`：用 SleepECG 自带功能下载一个公开 PSG 数据集（任选其内置支持的一个），
  跑它自带的预训练 HRV 睡眠分期分类器，输出睡眠/清醒的准确率、精确率、召回率和混淆矩阵。
- 把结果写成 `outputs/psg_validation.md`（数字 + 一句话结论），并和我们自己的
  “心率下降 + RMSSD 上升”规则在同一数据集上对比一次，写进同一份报告。
- 数据集本身不要提交进仓库（下载到 `data/psg/` 并在 `.gitignore` 里排除）。

**不做：** 不自己标注数据训练新模型，不改 `src/sleep_window.py` 的规则。

**验收：**
- `python scripts/validate_psg.py` 能跑完并生成 `outputs/psg_validation.md`，报告里有准确率数字和对比结论。
- README 的“当前状态”里勾选这一项。

**涉及文件：** `scripts/validate_psg.py`（新建）、`.gitignore`、`README.md`

## Issue #3 — Apple Health 解析器硬化 + fixture 测试

**为什么：** 真实 `Export.xml` 很大（几百 MB 常见），现在 `src/apple_health.py` 是一次性
`ET.parse()` 全量读入，缺字段、重复记录、时区混用都会直接崩。

**做：**
- 改用流式解析（`ET.iterparse`，处理完就 `clear()` 元素），内存占用不随文件大小线性增长。
- 处理：缺 `value` / `startDate` 的记录跳过并计数；同一时间戳的重复心率记录去重，保留第一条；
  `startDate` 带时区和不带时区两种格式都能解析，统一转成带时区的 UTC 时间戳输出。
- 新增 `tests/fixtures/export_sample.xml`（手写 20 行以内的小样本，含心率、SDNN、睡眠各 2 条，
  再加 1 条缺字段的坏记录），新增 `tests/test_apple_health.py` 覆盖上述三种情况。

**不做：** 不改输出列名（`timestamp,heart_rate_bpm` 等保持不变），不接小米/华为（那是 #5）。

**验收：**
- `pytest tests/test_apple_health.py` 通过，坏记录被跳过且计数正确。
- 用 10 万行合成 XML 跑解析，内存峰值有记录（写进测试注释或 PR 描述即可）。

**涉及文件：** `src/apple_health.py`、`tests/test_apple_health.py`（新建）、`tests/fixtures/export_sample.xml`（新建）

## Issue #4 — 测试套件改成 pytest + GitHub Actions CI

**为什么：** 现在 `tests/test_hrv.py` 是裸 assert，没有 pytest、没有 CI，
Devin 后面每改一处都没人兜底。

**做：**
- `tests/test_hrv.py` 改成标准 pytest 风格（保留现有两个用例，再补一个
  “RMSSD 对逐拍 RR 序列”的用例，复用 #1 的合成 RR 序列）。
- 新增 `.github/workflows/ci.yml`：Python 3.12，`pip install -r requirements.txt`，
  跑 `pytest -q` 和 `python scripts/validate_night.py --input data/sample_night.csv`，
  任一步失败则 CI 失败。
- `requirements.txt` 增加 `pytest`（放 dev 依赖段并注释）。

**不做：** 不写覆盖率门槛，不接其他 CI 服务。

**验收：**
- 本地 `pytest -q` 通过；推上去后 GitHub Actions 那次运行是绿的，截图或链接写进 PR 描述。

**涉及文件：** `tests/test_hrv.py`、`.github/workflows/ci.yml`（新建）、`requirements.txt`

## Issue #5 — 小米 / 华为手环导出归一化导入器

**为什么：** 只有 Apple Health 一条路，换手环的用户第一行代码就跑不起来。
README 已写明小米多为 Excel/CSV、华为为 JSON、时间戳格式不同。

**做：**
- 新增 `src/importers.py`，两个函数：
  - `from_xiaomi_csv(path)`：读 Excel/CSV，时间戳列转成 `timestamp`，心率列转成 `heart_rate_bpm`。
  - `from_huawei_json(path)`：`pandas.read_json()` 读 JSON，处理华为特有的时间戳格式，转成同一 schema。
- 两个函数输出统一为 `timestamp,heart_rate_bpm` 的 DataFrame，且都能直接喂给
  `scripts/validate_night.py --input`（给脚本加 `--format xiaomi|huawei|csv` 参数）。
- 各加一个 10 行以内的小 fixture（`tests/fixtures/xiaomi_sample.csv`、`huawei_sample.json`）和对应测试。

**不做：** 不做自动同步、不接厂商 API、不碰 Gadgetbridge 数据库解析。

**验收：**
- 两个 fixture 都能转成统一 schema 并跑通 `validate_night.py`，入睡窗口能输出结果（不要求时间准确）。
- README 的数据来源表格里把“转 CSV 后接入”改成“`--format xiaomi|huawei` 直接接入”。

**涉及文件：** `src/importers.py`（新建）、`scripts/validate_night.py`、`tests/test_importers.py`（新建）、`tests/fixtures/`、`README.md`

---

## 顺序与依赖

#1 → #4（#4 依赖 #1 的新用例）→ #2 → #3 → #5。
#2 和 #3 可以并行，#5 最后。
