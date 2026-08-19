# Structured 数据目录

本目录是结构化数据样本，不是独立评分系统。

## 保留内容

`icbc_structured_tax_rules.db` 和 `icbc_structured_tax_rules_schema.sql` 只包含：

- 商户基础信息；
- 财务、税务快照；
- 发票校验结果；
- 月度经营序列；
- 税务汇总查询视图。

这些数据可用于字段映射、接口联调和后续 ETL 开发。

## 评分口径

项目唯一正式评分实现位于 `backend/app/ml/`，以 v5 数据字典和 `v5_current` 口径为准。前端只调用：

- `POST /api/v1/ml/score`；
- `POST /api/v1/ml/full-analysis`。

不要在 SQLite、数据处理脚本或前端中重新实现权重、阈值、额度映射和人工复核规则。若要让本目录的数据参与评分，应编写字段适配器，将它们转换为后端 API 的请求模型。
