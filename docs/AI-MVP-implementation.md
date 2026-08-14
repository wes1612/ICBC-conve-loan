# AI MVP 实现说明

本版本按商赛范围实现两条旁路 AI 工作流，不改动评分、额度、异常识别、资金缺口和审核门控。

## 接口

```text
POST /api/v1/assistant/messages
POST /api/v1/ai/report-summary
```

- 流程助手只接收当前五步状态、材料解析状态、授权状态和审核过的本地知识。
- 报告解读只接收现有 `FullAnalysisResult`，不接收原始上传文件。
- 报告解读使用固定 Pydantic 结构，并校验证据编号、阿拉伯数字和禁止的放款承诺。
- 未配置 Key、超时、供应商失败或输出校验失败时，接口明确返回不可用；原有流程不受影响。

## 配置

在后端进程中配置：

```text
ICBC_OPENAI_API_KEY=...
ICBC_AI_MODEL=gpt-5.6-terra
ICBC_AI_TIMEOUT_SECONDS=30
```

也兼容标准 `OPENAI_API_KEY`。模型名只存在于后端环境变量中，两条工作流使用不同提示词和输出契约。

## 本地知识

```text
backend/app/knowledge/
├── workflow_faq.json
├── material_requirements.json
└── score_explanations.json
```

知识文件带版本号。MVP 不使用 RAG；知识量扩大后可以替换加载层，而无需改变前端接口。

## 前端降级

- 五步主流程和原授信报告始终可用。
- AI 调用失败时显示“智能解读暂不可用”。
- 不生成固定答案冒充模型返回。
- 报告页的 AI 智能解读需要用户主动点击，避免开发环境重复调用和无意消耗额度。

## 审计

成功调用会记录工作流、商户编号、模型、提示词版本和供应商响应编号；日志不记录 API Key 或原始上传文件内容。
