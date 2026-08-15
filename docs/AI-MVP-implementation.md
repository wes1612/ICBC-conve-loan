# DeepSeek AI 与本地微调实现

当前代码将“模型推理”“本地训练”“业务规则”分开：

- DeepSeek 托管 API 或本地微调模型只负责流程问答和报告文字生成；
- 评分、额度、异常、资金缺口和审核门控继续由现有确定性代码计算；
- CSV、Excel、文本型 PDF/Word 由后端本地读取，原始全文不直接发送给模型；
- M001/M005 业务指标仍是明确标注的竞赛样例，不冒充真实银行、税务或 OCR 结果。

## 运行接口

```text
GET  /api/v1/ai/status
POST /api/v1/assistant/messages
POST /api/v1/ai/report-summary
POST /api/v1/materials/parse
```

流程助手使用当前五步状态、材料状态和审核过的本地知识。报告解读只读取现有 `FullAnalysisResult`。两个工作流都使用固定 Pydantic 契约，并继续校验证据编号、数字和禁止的放款承诺。

## 使用 DeepSeek 托管 API

复制 `.env.example` 为项目根目录下的本地 `.env`，后端启动时会自动读取；也可以直接在后端进程环境中配置（进程环境变量优先）：

```text
ICBC_AI_PROVIDER=deepseek
ICBC_AI_API_KEY=你的 DeepSeek API Key
ICBC_AI_MODEL=deepseek-v4-flash
ICBC_AI_THINKING=false
```

DeepSeek 使用 OpenAI 兼容的 Chat Completions JSON 模式；JSON 返回后仍由本地 Pydantic 二次校验。模型名、供应商、提示词版本、来源版本、响应编号和 token 用量写入审计日志，但不记录 API Key 或原始文件全文。

## 使用训练出的本地模型

训练步骤、数据格式和启动命令见 [`backend/training/README.md`](../backend/training/README.md)。训练完成后启动本地兼容服务，再配置：

```text
ICBC_AI_PROVIDER=local
ICBC_AI_MODEL=icbc-credit-assistant
ICBC_AI_BASE_URL=http://127.0.0.1:9000/v1
```

这样网站接口和前端不需要改动，即可在 DeepSeek 托管 API 与本地 LoRA 模型之间切换。

## 材料读取边界

`POST /api/v1/materials/parse` 真实执行扩展名、大小、Base64、文件签名、SHA256 和压缩包安全上限检查，并支持：

- CSV：编码、行列、数字单元格和月份读取；
- XLS/XLSX：工作表、有效行、数字单元格和月份读取；
- DOCX：段落与表格文字读取；
- 文本型 PDF：页数与文字读取；
- PNG/JPEG 或扫描 PDF：明确提示需要 OCR，不返回伪造识别结果。

非预置商户会返回 `simulated: false` 的真实读取摘要，同时将主体匹配标为未核验。M001/M005 为了保持竞赛验收口径，仍返回 `simulated: true` 的固定业务指标。

## 训练边界

仓库内置 34 条种子样例（含安全拒答与提示词注入样例）只能证明数据构建和训练管线可执行，不能证明模型已经达到金融生产质量。正式微调前至少应：

1. 对训练样例去标识化，不放入身份证号、银行卡号、联系方式或原始客户文件；
2. 扩充经业务人员审核的流程问答、拒答、提示词注入和报告样例；
3. 将评测集与训练集严格分离；
4. 对证据编号、数字一致性、人工复核和禁止承诺做自动化验收；
5. 即使微调成功，也不得把评分规则藏进模型权重或让模型覆盖代码结果。

## 降级

- 未配置 Key、本地模型未启动、超时或输出校验失败时，AI 接口返回不可用；
- 原有五步流程、评分与普通授信报告始终可用；
- 报告 AI 解读必须由用户主动点击，不自动反复调用收费接口。
