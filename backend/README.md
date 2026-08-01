# Backend

由队员B初始化（建议 Python + FastAPI）。初始化命令参考：

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install fastapi uvicorn python-dotenv
pip freeze > requirements.txt
```

评分引擎实现请直接对照 `../data/数据字典_完善版__含评分规则与消费承接能力_v4.xlsx` 里的三个sheet：

- `评分规则_打分卡`：每个变量的打分区间和权重，可直接翻译成 if/elif
- `额度映射规则`：综合分→倍数、成长性扩张加成、最终额度公式
- `人工审核规则`：一票否决条件（V01-V08）和低置信度转人工条件（L01-L04）

`../data/五个测试商户_结构化与非结构化数据.xlsx` 的"预期输出对照表(最终版)"sheet是验收标准——
你算出来的中间变量、四个子评分、综合分、额度、置信度、触发规则，应该和这张表里的数字一致。
