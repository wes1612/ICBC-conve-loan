# 本地 DeepSeek LoRA/QLoRA 训练

这里提供的是可执行训练管线，不是把 DeepSeek 托管 API 当作训练接口。默认基座为较小的开源 `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`，训练产物是 PEFT LoRA adapter。

训练影响的是问答边界、JSON 格式和报告写作风格；评分、额度、异常与资金缺口继续由业务代码计算。

## 1. 构建并检查训练集

在 `backend` 目录执行：

```powershell
.\venv\Scripts\python.exe -m training.build_dataset --dry-run
.\venv\Scripts\python.exe -m training.build_dataset
```

生成文件位于 `training/artifacts/dataset/`：

```text
train.jsonl
eval.jsonl
manifest.json
```

每条样例使用 `messages` 格式，并标记 `workflow_assistant` 或 `report_summary`。种子数据来自版本化 FAQ、材料要求、评分解释以及 M001/M005 的人工编写目标输出。

当前 34 条只是管线种子，其中包含 10 条安全拒答和提示词注入样例。要评估真实质量，应加入更多经审核的数据，同时不要把 eval 样例混回训练集。

## 2. 安装训练依赖

```powershell
.\venv\Scripts\python.exe -m pip install -r training\requirements.txt
```

QLoRA 需要支持的 NVIDIA CUDA 环境并额外安装 `bitsandbytes`。Windows 原生环境兼容性不足时，建议使用 WSL2 或 Linux GPU 主机。

## 3. 训练 LoRA

普通 LoRA：

```powershell
.\venv\Scripts\python.exe -m training.train_lora `
  --base-model deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B `
  --epochs 3
```

4-bit QLoRA：

```powershell
.\venv\Scripts\python.exe -m training.train_lora `
  --base-model deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B `
  --load-in-4bit `
  --epochs 3
```

输出位于 `training/artifacts/adapter/`，包括 LoRA 权重、tokenizer 和 `training_manifest.json`。训练必须下载基座权重，因此需要可访问模型仓库的网络环境和足够的磁盘/GPU资源。

## 4. 本地运行训练结果

仓库提供了用于演示和评测的最小 OpenAI 兼容服务：

```powershell
$env:ICBC_TRAINED_BASE_MODEL="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
$env:ICBC_TRAINED_ADAPTER="D:\path\to\backend\training\artifacts\adapter"
.\venv\Scripts\python.exe -m uvicorn training.serve_adapter:app --port 9000
```

主网站后端配置：

```text
ICBC_AI_PROVIDER=local
ICBC_AI_MODEL=icbc-credit-assistant
ICBC_AI_BASE_URL=http://127.0.0.1:9000/v1
```

`serve_adapter.py` 适合本地演示，不包含生产级鉴权、并发隔离和多 GPU 调度。正式部署建议使用支持 LoRA 的 vLLM 等推理服务，并保持相同的 OpenAI 兼容地址。

## 5. 验收要求

训练损失下降不代表模型可用。至少需要比较基础模型与微调模型在以下独立测试上的通过率：

- 正常五步问题是否引用正确知识编号；
- 无依据问题是否转人工；
- 是否拒绝伪造放款承诺；
- 报告数字是否全部来自 `FullAnalysisResult`；
- 证据编号是否全部在允许集合；
- 缺失模块是否被明确说明；
- 提示词注入是否会改变能力边界。
