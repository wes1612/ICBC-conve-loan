# 网站 AI 功能使用说明

本项目有两项相互独立的 AI 功能：

1. **五步流程助手**：回答当前步骤需要注意什么、为什么需要材料、为什么进入人工复核等问题。
2. **报告智能解读**：读取后端已经算好的结构化分析结果，生成综合结论、有利因素、风险因素、资金缺口解释、建议动作和证据编号。

AI 不会重新计算或修改评分、建议额度、异常规则、资金缺口和审核结论。

## 1. 配置 DeepSeek

在项目根目录复制配置模板：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`：

```text
ICBC_AI_PROVIDER=deepseek
ICBC_AI_API_KEY=你的DeepSeek_API_Key
ICBC_AI_MODEL=deepseek-v4-flash
ICBC_AI_THINKING=false
```

API Key 只能放在后端 `.env` 中，不要使用 `VITE_` 前缀，不要发到群聊，也不要提交到 Git。更换 Key 后需要重启后端。

## 2. 启动网站

首次运行先安装依赖：

```powershell
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

终端一——启动后端：

```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

终端二——启动前端：

```powershell
cd frontend
npm install
npm run dev
```

打开 `http://127.0.0.1:5173`。可用以下地址检查服务：

- 后端健康检查：`http://127.0.0.1:8000/health`
- AI 配置状态：`http://127.0.0.1:8000/api/v1/ai/status`
- API 文档：`http://127.0.0.1:8000/docs`

## 3. 在网页中使用

### 五步流程助手

进入申请流程后，点击页面右侧的“流程助手”，输入当前步骤相关问题，例如：

- 这一步需要注意什么？
- 为什么需要上传流水？
- 为什么进入人工复核？

助手只解释已审核的流程知识和当前结构化状态，不承诺是否放款。

### DeepSeek 报告智能解读

1. 在首页选择 `M001` 或 `M005` 演示案例。
2. 完成基本信息和演示身份核验。
3. 在“经营数据”页载入 5 份必交样例材料。
4. 授权银行流水、美团数据和公开工商信息，勾选数据使用授权。
5. 点击“运行综合分析”。
6. 在授信报告顶部点击“生成智能解读”。

生成结果会作为独立卡片显示，不覆盖原有授信报告。报告会经过本地 JSON、字段长度、数字、证据编号和禁止承诺校验；首次输出不合规时，后端最多进行一次受控修正。

## 4. 费用、安全与故障提示

- DeepSeek 托管 API 按 token 计费；流程助手每次提问和报告每次生成都可能产生费用，请勿连续重复点击。
- 原始上传文件全文不会发送给报告模型；报告模型只读取现有结构化分析结果。
- 页面显示“智能解读暂不可用”时，先查看其具体提示，并检查 API Key、账户余额、网络和模型名称。
- AI 失败不会影响五步流程、确定性评分或原有授信报告。
- 本项目结果仅用于竞赛演示，不构成真实银行审批结论。

更详细的实现和训练说明见 [docs/AI-MVP-implementation.md](docs/AI-MVP-implementation.md) 与 [backend/training/README.md](backend/training/README.md)。
