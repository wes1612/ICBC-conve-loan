# Backend

Python + FastAPI 的消费供给动态授信后端。当前已实现：

- v5 结构化/非结构化特征计算；
- 稳定性、成长性、真实性、消费承接、口碑、社媒、投诉评分；
- 综合经营评分、额度计算、置信度和当前可计算的人工审核规则；
- `legacy_acceptance` 与 `v5_current` 两个版本化规则 profile；
- 五个模拟商户验收测试；
- 规则 + MAD 的交易异常识别及证据链；
- 阻尼趋势 + 压力情景的未来三个月 P50/P90 资金缺口预测；
- 五商户 553 笔模拟交易和 60 个月度现金流记录；
- 评分、异常、资金缺口三个版本化 ML 接口。

## ML 接口

| 接口 | 作用 | 当前算法 |
|---|---|---|
| `POST /api/v1/ml/score` | 经营信用评分、风险带、额度与审核规则 | v5 可解释评分卡 + 规则门控 |
| `POST /api/v1/ml/anomalies` | 交易异常分、原因码与证据交易 | 确定性规则 + MAD 稳健离群检测 |
| `POST /api/v1/ml/cash-gap` | 未来三个月 P50/P90 资金缺口 | 加权基线 + 阻尼趋势 + 压力情景 |
| `POST /api/v1/ml/full-analysis` | 一次返回三个模块，支持部分资料暂缺 | 聚合编排，不新增黑箱判断 |
| `POST /api/v1/analyze` | 旧评分路径兼容接口 | 与 `/api/v1/ml/score` 相同 |

当前没有真实贷后违约标签，因此 `pd_12m` 始终返回 `null`，`pd_status` 为 `UNCALIBRATED`。模拟明细用于开发和异常注入验收，不用于声称已经训练真实违约/欺诈模型。

## 本地安装与启动

```powershell
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install --index-url https://pypi.org/simple -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

启动后访问：

- 健康检查：`http://127.0.0.1:8000/health`
- Swagger：`http://127.0.0.1:8000/docs`

## 运行验收

```powershell
python -m pytest -q
python scripts/analyze_fixture.py M001 --profile legacy_acceptance
python scripts/analyze_fixture.py M005 --profile v5_current
python scripts/generate_ml_fixtures.py
python scripts/export_frontend_contract.py
python scripts/smoke_api.py
```

`smoke_api.py` 会临时启动本地 Uvicorn，真实调用三个 ML HTTP 接口和 Swagger/OpenAPI，结束后自动关闭服务。

`legacy_acceptance` 用于精确复现现有五商户 Excel 对照表；`v5_current` 使用 v5 最新口碑权重、严格置信度和 V09，作为后续页面默认版本。

## 规则来源

评分引擎规则基线为 `../data/数据字典_完善版__含评分规则与消费承接能力_v5.xlsx`；v4 仅为历史版本：

- `评分规则_打分卡`：变量的打分区间和权重；
- `额度映射规则`：综合分到倍数、成长性扩张加成和最终额度；
- `人工审核规则`：V01-V09 与 L01-L04。

`../data/五个测试商户_结构化与非结构化数据.xlsx` 的“预期输出对照表(最终版)”用于 `legacy_acceptance` 验收。v5 已修改口碑权重并新增 V09，因此 `v5_current` 的部分结果会与旧对照表不同，差异已由自动化测试锁定。
