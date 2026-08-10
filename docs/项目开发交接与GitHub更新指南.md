# 项目开发交接与 GitHub 更新指南

> 项目：工行杯金融科技竞赛——消费供给动态授信 MVP  
> 整理日期：2026-08-08  
> 适用对象：项目负责人、后端/算法同学、前端同学及后续接手成员  
> 当前可提交仓库：`D:\LQW\大一下\工行杯！\ICBC-conve-loan`  
> GitHub 最新 ZIP 参考目录：`D:\LQW\大一下\工行杯！\ICBC-conve-loan-main-8.8\ICBC-conve-loan-main`

## 1. 先看结论

1. `ICBC-conve-loan` 是带 `.git` 的真实本地 Git 仓库，远端为 `https://github.com/wes1612/ICBC-conve-loan.git`，后续提交、拉取和推送都应在此目录进行。
2. `ICBC-conve-loan-main-8.8` 是 GitHub ZIP 解压目录，没有 `.git`，只能作为最新文件参考，不能直接 `git pull`、`git commit` 或 `git push`。
3. 不建议把 ZIP 直接覆盖到真实仓库，也不要把 `.git` 复制到 ZIP 中。正确做法是：先把当前后端工作提交到功能分支，再 `fetch/rebase` 最新远端，测试通过后推送分支并发起 Pull Request。
4. 从最初只有目录框架的状态开始，目前已经完成一套可运行的 FastAPI 后端：经营信用评分、规则风险带、异常交易识别、资金缺口预测、聚合分析、Swagger、CORS、模拟数据、自动化测试和前端联调契约。
5. 当前没有真实贷后违约标签，所以不能声称已经训练出真实 `PD` 模型。系统返回 `pd_12m = null`、`pd_status = UNCALIBRATED` 是有意设计，不是功能错误。
6. 前端同学仍负责 UI、组件、图表和交互。本仓库提供稳定 API、OpenAPI、固定响应样例和字段映射，不替代其页面实现。

## 2. 最初项目是什么状态

最初仓库主要是一个协作框架，包含：

- `backend/`、`frontend/`、`data/`、`docs/` 等空目录或说明文件；
- 数据字典、五个测试商户和项目规划文档；
- 后端 README 中只有 FastAPI 初始化建议，没有可运行应用；
- 前端只有 README，没有页面工程；
- 没有 API、请求/响应模型、评分服务、异常识别、资金预测和自动化测试。

在这个基础上，本阶段主要完成了后端、ML 基线与前后端接口契约。

## 3. 当前总体架构

```text
商户结构化/非结构化资料
        │
        ├── 特征计算 ── 经营信用评分 ── 额度/风险带/审核规则
        │
交易明细 ───────────── 规则 + MAD 异常识别 ── 原因码/证据交易
        │
月度现金流 ─────────── 阻尼趋势 + 压力情景 ── P50/P90 资金缺口
        │
        └────────────── full-analysis 聚合接口 ── 前端综合分析页
```

重要原则：

- 分数、风险规则和额度由后端统一计算，前端不得重复实现公式。
- 大模型将来可以生成文字报告，但不能自行决定分数、违约概率、异常结论或额度。
- 五个商户及新增交易/现金流都是开发和验收数据，不是真实银行训练数据。
- 规则命中优先于自动授信；命中一票否决或重大异常时进入人工复核。

## 4. 已完成工作清单

### 4.1 数据规则和版本口径

- 将 v5 数据字典同步到 [`data/数据字典_完善版__含评分规则与消费承接能力_v5.xlsx`](../data/数据字典_完善版__含评分规则与消费承接能力_v5.xlsx)。
- 确认 v5 新增 V09，并调整线上口碑权重与置信度逻辑。
- 发现五商户“预期输出对照表（最终版）”仍包含部分旧口径，因此实现两个版本：
  - `legacy_acceptance`：精确复现现有 Excel 验收结果；
  - `v5_current`：采用 v5 最新规则，作为页面和新接口默认版本。
- 形成完整设计说明：[`docs/机器学习评分模块设计.md`](机器学习评分模块设计.md)。

前端正式请求必须传：

```json
{
  "profile": "v5_current"
}
```

`legacy_acceptance` 只用于回归测试，不应成为生产页面默认值。

### 4.2 FastAPI 应用和接口

应用入口：[`backend/app/main.py`](../backend/app/main.py)

已经提供：

| 方法和路径 | 功能 | 前端使用建议 |
|---|---|---|
| `GET /health` | 健康检查 | 页面启动或联调前检查后端是否在线 |
| `POST /api/v1/ml/score` | 经营信用评分、风险带、审核规则和额度 | 单独刷新评分时使用 |
| `POST /api/v1/ml/anomalies` | 交易异常分、原因码和证据交易 | 异常监控模块使用 |
| `POST /api/v1/ml/cash-gap` | 未来三个月 P50/P90 资金缺口 | 资金缺口图表使用 |
| `POST /api/v1/ml/full-analysis` | 一次返回三个模块 | 综合分析页首选 |
| `POST /api/v1/analyze` | 旧评分兼容路径 | 新页面不建议使用 |

API 路由代码：[`backend/app/api/ml.py`](../backend/app/api/ml.py)

Swagger 地址：

```text
http://127.0.0.1:8000/docs
```

OpenAPI JSON：

```text
http://127.0.0.1:8000/openapi.json
```

### 4.3 统一请求与响应模型

Pydantic 模型位于 [`backend/app/schemas/`](../backend/app/schemas/)：

| 文件 | 主要内容 |
|---|---|
| `merchant.py` | 商户结构化/非结构化输入、数组长度和字段范围校验 |
| `analysis.py` | 经营评分、维度分、额度、置信度、风险带和审核规则输出 |
| `anomaly.py` | 交易明细、异常规则命中和证据交易输出 |
| `cash_gap.py` | 12个月现金流输入和未来3个月 P50/P90 输出 |
| `full_analysis.py` | 综合分析请求、模块状态、总体风险和聚合输出 |

这些文件是接口字段的代码级权威来源；前端不得根据截图自行猜字段名称。

### 4.4 特征工程与经营信用评分

实现文件：

- [`backend/app/ml/feature_engine.py`](../backend/app/ml/feature_engine.py)：统一特征快照；
- [`backend/app/ml/scorecard.py`](../backend/app/ml/scorecard.py)：稳定性、成长性、真实性、消费承接、线上口碑、社媒和投诉评分；
- [`backend/app/ml/config.py`](../backend/app/ml/config.py)：版本化权重和业务阈值；
- [`backend/app/ml/decision_engine.py`](../backend/app/ml/decision_engine.py)：信用等级、风险带、额度、置信度、原因和人工审核规则；
- [`backend/app/services/analysis_service.py`](../backend/app/services/analysis_service.py)：统一评分服务编排。

当前评分输出包括：

- `operating_credit_score`：经营信用分，0～100；
- `credit_grade`：A/B/C/D/E；
- `dimensions`：各维度分；
- `risk_band`：LOW/MEDIUM/HIGH/MANUAL_REVIEW；
- `decision`：APPROVE/MANUAL_REVIEW/DECLINE；
- `review_rules`：命中的 V01～V09、L01～L04；
- `positive_reasons`、`negative_reasons`：主要加减分原因；
- `limit.recommended_limit`：建议额度；
- `confidence`：数据置信度；
- `pd_12m`、`pd_status`：真实违约概率状态。

五商户旧版验收结果已逐项复现；v5 新口径通过独立测试锁定。

### 4.5 违约风险现状

目前完成的是“风险带 + 规则门控”，不是有真实标签训练的 PD 模型。

当前可用：

- 经营信用分；
- LOW/MEDIUM/HIGH/MANUAL_REVIEW 风险带；
- 法人授信、主体一致性、流水、合同发票、数据缺失等人工审核规则；
- `pd_12m = null`；
- `pd_status = UNCALIBRATED`。

后续只有拿到真实历史数据后，才能按以下标签训练：观察时点后 12 个月内最大逾期天数达到 90 天、核销/坏账、信用恶化实质重组或代偿。训练时需按时间切分并做概率校准，不能把五个模拟商户当作违约标签。

### 4.6 异常交易识别

实现文件：

- [`backend/app/ml/anomaly_config.py`](../backend/app/ml/anomaly_config.py)：集中配置阈值和规则贡献；
- [`backend/app/ml/anomaly_engine.py`](../backend/app/ml/anomaly_engine.py)：规则 + MAD 稳健离群检测；
- [`backend/app/schemas/anomaly.py`](../backend/app/schemas/anomaly.py)：请求/响应契约。

已识别的异常类型包括：

- 同日多笔相同整数金额；
- 非营业时段交易集中；
- 单一对手方金额集中；
- 入账后短时间近等额转出；
- 退款、撤销、冲正比例异常；
- MAD 稳健金额离群；
- 收款缺少平台订单关联。

输出不仅包含异常分，还包含 `reason_codes`、中文说明和 `evidence_transaction_ids`。异常结果用于预警和人工复核，不能单独直接拒贷。

### 4.7 资金缺口预测

实现文件：

- [`backend/app/ml/cash_gap_engine.py`](../backend/app/ml/cash_gap_engine.py)；
- [`backend/app/schemas/cash_gap.py`](../backend/app/schemas/cash_gap.py)。

算法基线：

- 读取至少 12 个月经营现金流入/流出；
- 使用近期加权基线和阻尼趋势预测未来三个月；
- 加入当前现金、受限资金、最低安全现金、资本开支和还本付息；
- 输出 P50 基准情景和 P90 压力情景；
- 输出最大缺口、首次缺口月份、未用授信后的剩余融资需求和主要驱动。

前端必须区分：

- `cash_funding_gap`：流动性/融资资金缺口；
- `supply_capacity_gap`：消费供给承接缺口。

两者不是同一个业务概念。

### 4.8 综合分析聚合接口

实现文件：

- [`backend/app/services/full_analysis_service.py`](../backend/app/services/full_analysis_service.py)；
- [`backend/app/schemas/full_analysis.py`](../backend/app/schemas/full_analysis.py)。

前端综合分析页优先调用：

```text
POST /api/v1/ml/full-analysis
```

请求结构：

```json
{
  "merchant": {},
  "anomaly": {},
  "cash_gap": {}
}
```

其中 `merchant` 必填，`anomaly` 和 `cash_gap` 可缺省。缺省时接口仍返回 200：

- 对应结果返回 `null`；
- `module_states` 返回 `NOT_PROVIDED`；
- `data_warnings` 返回缺少资料的中文提示。

前端不能把 `NOT_PROVIDED` 显示成“低风险”或“0分”。

### 4.9 CORS 和本地联调

CORS 配置位于：

- [`backend/app/settings.py`](../backend/app/settings.py)；
- [`backend/app/main.py`](../backend/app/main.py)。

默认允许：

- `http://localhost:3000`；
- `http://127.0.0.1:3000`；
- `http://localhost:5173`；
- `http://127.0.0.1:5173`。

其他端口可通过 `ICBC_CORS_ORIGINS` 配置。生产环境应填写明确域名，不建议设置为 `*`。

### 4.10 模拟数据

数据说明：[`data/ml_simulated/README.md`](../data/ml_simulated/README.md)

已经生成：

- [`data/ml_simulated/transactions.json`](../data/ml_simulated/transactions.json)：五商户共 553 笔模拟交易；
- [`data/ml_simulated/cashflow_monthly.json`](../data/ml_simulated/cashflow_monthly.json)：五商户共 60 个商户月现金流记录。

M005 显式注入重复整数金额、夜间交易、集中对手方、快速进出、退款和订单缺链；M003 注入较高退款。生成脚本固定且可复现：

[`backend/scripts/generate_ml_fixtures.py`](../backend/scripts/generate_ml_fixtures.py)

这些数据只能用于演示、接口联调、异常注入和回归测试。

### 4.11 自动化测试和验收脚本

测试目录：[`backend/tests/`](../backend/tests/)

覆盖：

- 五商户评分和额度验收；
- v5/旧版 profile 差异；
- V09 和低置信度；
- 输入数组、日期、商户 ID 等校验；
- 正常、退款异常和高异常商户；
- P50/P90 资金缺口关系；
- 聚合接口、部分数据缺失和跨商户数据拒绝；
- API、OpenAPI 与 CORS。

截至 2026-08-08：

```text
28 passed
```

常用脚本：

| 文件 | 用途 |
|---|---|
| `scripts/analyze_fixture.py` | 命令行分析单个评分商户 |
| `scripts/generate_ml_fixtures.py` | 重新生成模拟交易和现金流 |
| `scripts/export_frontend_contract.py` | 导出 OpenAPI 和固定前端样例 |
| `scripts/smoke_api.py` | 临时启动 Uvicorn，真实调用全部接口、Swagger 和 CORS |

## 5. 当前如何运行

### 5.1 安装依赖

```powershell
cd "D:\LQW\大一下\工行杯！\ICBC-conve-loan\backend"
python -m venv venv
.\venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r requirements.txt
```

### 5.2 启动后端

```powershell
cd "D:\LQW\大一下\工行杯！\ICBC-conve-loan\backend"
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

访问：

- 健康检查：`http://127.0.0.1:8000/health`；
- Swagger：`http://127.0.0.1:8000/docs`。

### 5.3 运行全部测试

```powershell
cd "D:\LQW\大一下\工行杯！\ICBC-conve-loan"
.\backend\venv\Scripts\python.exe -m pytest -q
```

### 5.4 运行真实 HTTP 冒烟测试

```powershell
cd "D:\LQW\大一下\工行杯！\ICBC-conve-loan\backend"
.\venv\Scripts\python.exe scripts\smoke_api.py
```

## 6. 前端同学需要做什么、参考什么

### 6.1 推荐分工

前端同学负责：

- 根据 UI 初稿搭建 Vue/React 工程；
- 组件、布局、响应式、图表、加载状态和交互；
- 调用后端 API；
- 将错误定位到表单字段；
- 银行端和商户端的信息展示差异；
- 前端工程测试与构建。

后端/算法负责：

- 输入输出契约；
- 特征、分数、额度、风险和原因；
- 异常证据、资金预测；
- 数据校验和错误响应；
- OpenAPI、样例和接口联调；
- 不把业务公式复制到前端。

### 6.2 前端任务—参考文件映射

| 前端要做的事情 | 首先参考 | 必要时再看 |
|---|---|---|
| 理解整体联调流程 | [`docs/前后端联调说明.md`](前后端联调说明.md) | [`backend/README.md`](../backend/README.md) |
| 查看所有 API 字段和类型 | [`docs/api_examples/openapi.json`](api_examples/openapi.json) | `backend/app/schemas/` |
| 先做正常页面 Mock | [`full_analysis_normal_response.json`](api_examples/full_analysis_normal_response.json) | 对应 request 文件 |
| 做人工复核/异常页面 Mock | [`full_analysis_review_response.json`](api_examples/full_analysis_review_response.json) | 对应 request 文件 |
| 查看综合接口路径 | [`backend/app/api/ml.py`](../backend/app/api/ml.py) | `full_analysis_service.py` |
| 理解总体风险如何汇总 | [`backend/app/services/full_analysis_service.py`](../backend/app/services/full_analysis_service.py) | `full_analysis.py` |
| 做评分卡和维度雷达图 | `analysis.py` 的 `AnalysisResult/DimensionScores` | `scorecard.py` 只用于理解，不在前端重算 |
| 做额度卡片 | `analysis.py` 的 `LimitDecision` | `decision_engine.py` |
| 做人工审核规则列表 | `score.review_rules` 固定响应样例 | `decision_engine.py` |
| 做异常原因和证据表 | `anomaly.py`、风险响应样例 | `anomaly_engine.py` |
| 做资金缺口折线图 | `cash_gap.py`、正常/风险响应样例 | `cash_gap_engine.py` |
| 处理资料缺失空状态 | `module_states`、`data_warnings` | `full_analysis.py` |
| 处理 422 错误 | Swagger 响应中的 `detail[].loc/msg/type` | 各请求 schema |
| 排查跨域 | `backend/app/settings.py` | `backend/app/main.py` |
| 做端到端自测 | `scripts/smoke_api.py` | `backend/tests/test_api.py` |

### 6.3 推荐页面模块

综合分析页可按 UI 初稿自由布局，但建议至少覆盖：

1. 商户名称、商户 ID、分析时间和总体风险；
2. 经营信用分、信用等级、决策、置信度；
3. 建议额度、额度倍数、成长加成；
4. 维度雷达图或柱状图；
5. 主要优势、主要风险；
6. 人工审核命中列表；
7. 异常分、原因、证据交易；
8. P50/P90 资金缺口图；
9. 最低安全现金线、当前可用现金和未用授信；
10. 数据不足与补件提示。

### 6.4 前端字段使用注意事项

- 金额统一在展示层格式化为人民币和千分位，不改变后端原值。
- 比例字段确认是 `0～1` 还是 `0～100` 后再格式化，不能直接全部加 `%`。
- 时间使用接口返回的 ISO 日期/时间，不根据数组下标猜月份。
- `MANUAL_REVIEW` 应展示为“人工复核”，不能翻译成“拒绝”。
- `HIGH` 异常表示需要核查，不等于已认定欺诈。
- `pd_12m = null` 要显示“待真实历史数据校准”，不能显示 0%。
- `NOT_PROVIDED` 是资料未提供，不是低风险。
- `review_rules[].message` 和异常 `rule_hits[].message` 已由后端提供，前端不需要自己拼原因。
- 商户端不应展示银行内部反欺诈阈值和全部证据 ID；银行审核端可以展示。
- 前端不能复制 v5 权重、评分阈值、额度公式和异常规则，否则以后后端升级会产生两套口径。
- 优先使用 `/full-analysis`；只有局部刷新才使用三个独立接口。

### 6.5 推荐联调顺序

1. 使用固定 normal response 完成正常页面；
2. 使用固定 review response 完成人工复核、异常和高风险状态；
3. 启动后端并检查 `/health`；
4. 用 normal request 调用 `/full-analysis`；
5. 用 review request 调用 `/full-analysis`；
6. 删除 `anomaly` 或 `cash_gap`，验证空状态；
7. 删除必填字段，验证 422 表单提示；
8. 对照 Swagger 和 OpenAPI 检查字段；
9. 最后进行真实页面联调，不要一开始就把 UI 和接口问题混在一起排查。

## 7. 对 2026-08-08 GitHub 最新 ZIP 的检查

最新 ZIP 相比最初骨架新增 24 个文件，主要包括：

- `data/Data_Dictionary_Revised.xlsx`；
- `data/Five_Testing_Merchants.xlsx`；
- `data/Structured/`：结构化商户、财务税务、发票和月度经营 SQLite 数据及 SQL schema；
- `data/Unstructured/`：评价 SQLite、SQL schema、五商户评论 CSV、Word 材料和词云 PNG。

这些是其他队员的新成果，应通过 `git fetch/rebase` 保留，不应被当前后端目录覆盖。

### 7.1 已发现的可移植性问题

`data/Unstructured/run_unstructured_review_test.py` 写死：

```python
DB_PATH = Path(r"C:\Users\13777\Documents\Codex\2026-08-01\new-chat\outputs\unstructured_reviews\icbc_unstructured_reviews.db")
```

该脚本在其他电脑上不能直接运行。建议后续改为：

```python
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "数据库文件名.db"
```

### 7.2 与当前后端的口径关系

团队已于 2026-08-10 决定删除独立简化评分原型，解决它与 v5 FastAPI 评分引擎的口径冲突。当前约定是：

- `data/Structured/` 只保留结构化数据和 schema，不包含评分规则或评分结果；
- v5 FastAPI 引擎是唯一正式评分实现；
- 前端只调用 `/api/v1/ml/score` 或 `/api/v1/ml/full-analysis`；
- 后续如需接入 SQLite 数据，应把字段转换成 `MerchantAnalysisRequest`，不得维护第二套评分公式。

完整决策见 `docs/v5评分口径统一说明.md`。

非结构化评价数据库和词云可作为后续文本解析、报告和页面展示的数据源；当前后端接收的是已汇总的评价/社媒/投诉指标，尚未直接解析这些 `.docx` 和评论 CSV。

### 7.3 前端最新状态

最新 ZIP 的 `frontend/` 仍只有 README，没有提交页面工程。前端同学的 UI 初稿如果尚未进 Git，应让其使用独立功能分支提交，例如：

```text
feat/frontend-ui
```

不要让前端和后端同学同时直接修改并推送 `main`。

## 8. 安全更新 GitHub 的推荐流程

### 8.1 为什么不要直接使用 ZIP

ZIP 没有提交历史、分支和远端信息。直接在 ZIP 中 `git init` 会生成一套与原仓库历史无关的仓库；直接覆盖真实仓库则可能覆盖已完成的 README、看板和后端文件。

因此：

- ZIP 保留为只读参考；
- 所有 Git 操作在 `ICBC-conve-loan` 中进行；
- 先提交当前工作，再拉取远端最新提交；
- 使用功能分支和 Pull Request。

### 8.2 第一步：确认目录

```powershell
cd "D:\LQW\大一下\工行杯！\ICBC-conve-loan"
git status --short --branch
git remote -v
```

应看到当前分支为 `main`，远端为：

```text
https://github.com/wes1612/ICBC-conve-loan.git
```

### 8.3 第二步：创建后端功能分支

当前改动尚未提交，建议先从现有状态创建分支：

```powershell
git switch -c feat/ml-backend-integration
```

这不会删除或覆盖当前文件，只是让后续提交不直接落到 `main`。

### 8.4 第三步：提交当前后端工作

```powershell
git add README.md backend data docs pytest.ini
git status --short
git diff --cached --stat
git diff --cached --check
```

提交前确认：

- `backend/venv/` 未进入暂存区；
- `__pycache__/`、`.pytest_cache/` 未进入暂存区；
- 没有 `.env`、密钥、密码或访问令牌；
- 暂存区包含后端、模拟数据、v5 数据字典和文档；
- 没有把 ZIP 外层目录整体加入。

然后提交：

```powershell
git commit -m "feat: implement ML scoring anomaly and cash-gap backend"
```

### 8.5 第四步：拉取 GitHub 最新提交并变基

```powershell
git fetch origin
git rebase origin/main
```

这样会把当前后端提交放到 GitHub 最新提交之后，同时保留最新 ZIP 中看到的结构化/非结构化数据成果。

如果没有冲突，继续测试即可。

如果有冲突：

```powershell
git status
```

逐个打开冲突文件，删除 `<<<<<<<`、`=======`、`>>>>>>>` 标记并保留正确内容。当前最可能涉及：

- `backend/README.md`；
- `data/README.md`；
- `docs/PROJECT_BOARD.md`。

解决后：

```powershell
git add 冲突文件路径
git rebase --continue
```

如果不确定如何解决，不要强行覆盖，可执行：

```powershell
git rebase --abort
```

它会回到变基前状态，再让队友或 Codex 协助处理。

### 8.6 第五步：合并后测试

```powershell
.\backend\venv\Scripts\python.exe -m pytest -q
cd backend
.\venv\Scripts\python.exe scripts\smoke_api.py
cd ..
git diff --check
git status --short --branch
```

验收标准：

- 自动化测试全部通过；
- Swagger 能打开；
- `/score`、`/anomalies`、`/cash-gap`、`/full-analysis` 均成功；
- CORS 允许前端开发地址；
- Git 没有未解决冲突。

### 8.7 第六步：推送功能分支

```powershell
git push -u origin feat/ml-backend-integration
```

随后在 GitHub 发起 Pull Request：

```text
feat/ml-backend-integration → main
```

推荐 PR 标题：

```text
feat: 完成 ML 评分、异常识别、资金缺口预测及前端联调接口
```

PR 描述建议写：

- 实现 v5 评分卡和旧版验收 profile；
- 实现异常交易规则 + MAD；
- 实现 P50/P90 三个月资金缺口；
- 新增 full-analysis 聚合接口和 CORS；
- 新增五商户模拟交易/现金流；
- 新增 OpenAPI、固定联调样例和交接文档；
- 测试结果 `28 passed`；
- 真实 PD 尚未校准，`pd_12m` 保持 null。

让至少一名队友检查后再合并到 `main`。

### 8.8 GitHub Desktop 操作对应关系

如果不想使用命令行：

1. 在 GitHub Desktop 选择 **Add Existing Repository**；
2. 路径选择 `D:\LQW\大一下\工行杯！\ICBC-conve-loan`，不要选择 ZIP；
3. 创建分支 `feat/ml-backend-integration`；
4. 检查 Changes，填写提交说明并 Commit；
5. Fetch origin；
6. Update/Rebase branch 到最新 `origin/main`；
7. 在终端运行测试；
8. Publish branch；
9. Create Pull Request。

## 9. 建议的团队 Git 规则

- `main`：只保留可运行、测试通过的代码；
- 后端分支：`feat/ml-backend-integration`；
- 前端分支：`feat/frontend-ui`；
- 数据分支：`feat/structured-data`、`feat/unstructured-data`；
- 修复分支：`fix/...`；
- 所有功能通过 PR 合并；
- 合并前至少运行对应测试；
- 不提交 `venv/`、`node_modules/`、`.env`、令牌和个人绝对路径；
- 不在前端和离线数据脚本中重新实现第二套评分公式；
- 修改 API schema 后重新运行 `export_frontend_contract.py`，并通知前端。

## 10. 尚未完成、不要误称已完成的内容

### 10.1 后端/算法

- 真实贷款表现数据接入；
- 真实 `default_12m` 标签；
- WOE+逻辑回归或 LightGBM PD 模型训练和校准；
- 真实交易级反欺诈监督模型；
- 数据库存储、申请记录和模型预测落库；
- 文件上传、Excel/合同/评价自动解析；
- 用户认证、权限和银行/商户角色隔离；
- 贷后动态重评与漂移监控；
- LLM 授信报告生成；
- 生产部署和安全加固。

### 10.2 前端

- UI 初稿的正式代码实现；
- 商户资料填写和上传页面；
- 银行审核综合分析页；
- 商户改善建议页；
- 图表、空状态、错误状态；
- API Client 和环境变量；
- 角色权限和页面路由；
- 构建、部署和端到端测试。

## 11. 推荐下一阶段顺序

1. 先按第 8 节把后端工作提交到功能分支并与最新 `main` 合并；
2. 修复最新数据脚本中的个人绝对路径；
3. 明确结构化 SQLite、非结构化 SQLite 到 `MerchantAnalysisRequest` 的字段映射；
4. 前端使用固定 JSON 完成综合分析页；
5. 前端切换到 `/full-analysis`；
6. 后端补申请记录/预测结果存储；
7. 生成第一版结构化授信报告；
8. 用 M001、M003、M005 完成正常、风险、异常三种演示路径；
9. 再考虑 LLM 报告、贷后监控和真实 PD 数据升级。

## 12. 最终答辩口径

建议统一表述：

> 当前系统已经完成可解释经营信用评分、规则风险门控、交易异常识别和资金缺口情景预测，并通过五商户端到端验收。现有模拟数据用于验证接口与业务逻辑，不用于伪造真实违约概率；真实 PD 字段保持未校准状态，系统已经预留历史标签接入、时间外验证和概率校准能力。前端通过统一聚合接口展示分数、证据、置信度和资金缺口，所有关键结论均可追溯。

这一表述能够体现算法完整性，同时不会对模拟数据能力作过度承诺。
