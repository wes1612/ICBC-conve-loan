# ML 模拟明细数据

本目录数据由 `backend/scripts/generate_ml_fixtures.py` 根据五个测试商户确定性生成，仅用于比赛 MVP 开发、接口联调和异常注入验收。

- `transactions.json`：五商户交易明细；M005 注入重复整数金额、非营业时段、集中对手方、快速进出、退款和订单缺链等异常。
- `cashflow_monthly.json`：五商户连续 12 个月经营现金流及未来三个月计划支出。

这些记录不是真实银行数据，不能用于声称模型已经基于真实违约或欺诈标签完成训练。

重新生成：

```powershell
cd backend
python scripts/generate_ml_fixtures.py
```
