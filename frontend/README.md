# 融策前端

基于 React、TypeScript 与 Vite 的小微动态授信演示前端。页面由 `P1_3.fig`、`P4_6.fig` 的六个草稿流程演化而来，并按后端 v0.2.0 契约完成字段与状态对齐。

## 页面流程

1. 申请首页与 M001 / M005 联调场景选择
2. 企业主体资料
3. 法人核验演示（当前不采集影像）
4. 经营资料清单（明确 12 个月现金流要求）
5. 数据授权与综合分析
6. 商户摘要 / 银行审核台

## 启动

```powershell
cd frontend
pnpm install
pnpm dev
```

默认访问 `http://localhost:5173`，默认后端地址为 `http://127.0.0.1:8000`。如需修改：

```powershell
Copy-Item .env.example .env.local
$env:VITE_API_BASE_URL="http://你的后端地址"
pnpm dev
```

## 联调行为

- 启动时调用 `GET /health` 检查后端。
- 分析时优先调用 `POST /api/v1/ml/full-analysis`。
- 后端离线或请求失败时，回退到 `docs/api_examples/` 中的固定正常/人工复核响应，并在结果页明确标为“固定联调样例”。
- 请求固定使用 `profile: v5_current`。
- `NOT_PROVIDED` 会显示为空状态，不会显示为低风险或 0 分。
- `pd_12m = null` 显示为“待历史数据校准”，不会换算为 0%。
- 商户摘要不展示全部异常证据交易；银行审核台才展示证据明细。

文件上传解析、真实活体认证、审核意见落库、PDF/LLM 报告生成尚未由后端实现，页面中均以待接入状态呈现。
