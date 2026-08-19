# policy-introduction

本目录新增了一个 MVP 级“消费政策库”，用于支撑网站最后一页的“可申请消费政策 + 工行消费引介方案”。它不是静态文案库，而是后端可以读取、匹配、排序和解释的结构化 data 模块。

## 设计原则

1. 政策搜索或 AI 只能生成候选，不能直接向商户承诺可申请。
2. 网站展示的 ACTIVE 政策必须保留来源链接、更新时间、有效期和人工确认要求。
3. 地方消费券、培训补贴、稳岗补贴等强地域政策先以 DRAFT 模板进入库，待每周人工核验后再转 ACTIVE。
4. 工行优势不单独空泛展示，而是绑定到每条政策的申请动作、支付核销、消费引流和贷后监控数据回流。

## 新增文件

- `data/policies/policies.json`：政策条目库，含国家级政策和地方模板政策。
- `data/policies/policy_rules.json`：政策匹配规则，连接商户画像、授信结论、资金用途和评分维度。
- `data/policies/bank_programs.json`：工行消费引介方案，包括个人账户定向券、企业员工福利券、信用卡/数字人民币满减、平台曝光修复。
- `backend/app/services/policy_match_service.py`：后端匹配服务。
- `backend/scripts/validate_policy_database.py`：政策库结构校验和过期检查脚本。
- `backend/app/schemas/full_analysis.py`：`FullAnalysisResult` 新增 `policy_recommendations`。
- `frontend/src/pages/ResultsPage.tsx`：优先使用后端政策推荐结果生成政策卡和消费引介卡。

## 当前政策来源

本次种子库参考了以下公开来源：

- 财政部等四部门《关于优化实施服务业经营主体贷款贴息政策的通知》（财金〔2026〕5号）：服务业经营主体贷款贴息。
- 商务部等部门数字消费指导意见：数字消费券、数字人民币消费红包、生活服务数字化。
- 商务部等9部门零售业创新发展意见：线上引流+线下成交、数字人民币核销、平台技术赋能。
- 税务部门公开问答：小微企业和个体工商户税费优惠、六税两费减半等。

## 每周更新机制

建议每周执行一次：

1. 检索国家、省、市、区商务、人社、税务、财政、市场监管部门，以及工行、平台、行业协会通知。
2. 把新发现政策先录入 `DRAFT`，补齐来源、适用行业、有效期、材料清单、申报窗口。
3. 运行校验脚本：

```powershell
cd "E:\Codex\ICBC-conve-loan-feature-ai-assistant-summary\backend"
.\venv\Scripts\python.exe scripts\validate_policy_database.py
```

4. 人工确认政策确实适用于目标城市、行业和主体后，将 `status` 从 `DRAFT` 改为 `ACTIVE`。
5. 对已过期政策改为 `EXPIRED`，不要直接删除；保留历史版本便于审计。
6. 重新导出前端契约：

```powershell
.\venv\Scripts\python.exe scripts\export_frontend_contract.py
```

## 与网站流程的关系

申请页收集行业、资金用途、申请金额和还款来源；后端评分后，`policy_match_service` 会综合：

- 行业和资金用途；
- 综合授信结论；
- 风险带和人工复核状态；
- 消费承接能力、口碑和材料完整度；
- 政策有效期和本地确认要求。

最终在 `/api/v1/ml/full-analysis` 返回 `policy_recommendations`，前端结果页据此展示：

- 推荐政策卡；
- 工行可协助动作；
- 消费引介方案；
- 材料清单和风险提示。

## 当前边界

当前版本不实现无人值守自动爬虫入库。原因是银行场景下政策推荐必须可追溯、可解释、可复核。后续如果需要自动化，可以新增候选发现脚本，但候选仍应进入 DRAFT 队列，经人工审核后再推荐给商户。