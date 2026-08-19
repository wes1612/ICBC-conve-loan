# 金融参数接入说明

本次修改把“贷给谁、为什么贷、贷多少/多久/怎么还、靠什么判断还得起、如何留痕审计”嵌入现有网站和 FastAPI 聚合接口。修改只新增产品解释层，不改 v5 评分卡、异常识别和资金缺口预测的核心算法。

## 已接入内容

- 申请页新增申请期限、资金用途、主要还款来源，与申请金额一起传入后端。
- 后端 `POST /api/v1/ml/full-analysis` 新增四组输出：
  - `eligibility`：首期试点行业准入、补件/人工复核/范围外判断。
  - `loan_terms`：建议额度、额度区间、期限、还款方式、循环额度、提款/续贷/调额规则、用途匹配提示。
  - `repayment_capacity`：月均经营流入/流出、固定成本覆盖、P90资金缺口、偿债能力结论和证据。
  - `audit_trail`：授权版本、授权时间、授权来源、材料哈希、评分/规则/模型版本。
- 授权页显示授权版本、授权时间和数据使用范围。
- 结果页商户视角把“建议额度”升级为“授信方案”，并展示还款能力摘要。
- 银行审核台新增准入判断、授信产品参数、偿债能力拆解和合规审计留痕。

## 主要文件

- `backend/app/schemas/full_analysis.py`：扩展申请入参和聚合返回契约。
- `backend/app/services/loan_product_service.py`：新增授信产品参数、准入、偿债能力和审计留痕生成逻辑。
- `backend/app/services/full_analysis_service.py`：把新增产品层接入综合分析编排。
- `frontend/src/types.ts`：同步新增前后端类型。
- `frontend/src/data/fixtures.ts`：演示申请数据补充用途、期限和还款来源。
- `frontend/src/pages/IdentityPage.tsx`：新增金融参数输入。
- `frontend/src/pages/AuthorizePage.tsx`：新增授权版本和时间展示。
- `frontend/src/pages/ResultsPage.tsx`：新增授信方案、偿债能力、准入和审计展示。
- `frontend/src/styles.css`：新增对应布局样式，兼容移动端和打印。

## 运行检查

后端：

```powershell
cd "E:\Codex\ICBC-conve-loan-feature-ai-assistant-summary\backend"
.\venv\Scripts\python.exe -m pytest -q
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

前端：

```powershell
cd "E:\Codex\ICBC-conve-loan-feature-ai-assistant-summary\frontend"
npm install
npm run dev
```

浏览器打开前端终端显示的本地地址，按“申请首页 → 基本信息上传 → 身份核验 → 经营数据 → 相关数据授权 → 授信报告”跑通。授权页必须勾选银行经营流水、美团订单与评价、公开工商信息，并确认授权后才能提交。

## 后续建议

- 把 `loan_terms` 规则参数外置为 JSON 或数据库配置，便于后续按政策、行业和地区调整。
- 新增正式申请记录表，持久化 `application`、`audit_trail`、材料哈希和审核动作。
- 对政策推荐增加政策库字段：适用地区、适用行业、有效期、所需材料、工行可协助动作。
- 将贷后监控 KPI 拆成单独模块，不在本次 MVP 里强行堆到授信页。
