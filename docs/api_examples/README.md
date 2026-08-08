# 前端联调样例

本目录由 `backend/scripts/export_frontend_contract.py` 自动生成：

- `openapi.json`：FastAPI 的完整接口契约，可用于生成 TypeScript 类型或 API Client。
- `full_analysis_normal_*`：M001 正常低风险场景。
- `full_analysis_review_*`：M005 异常并转人工复核场景。

不要手工维护生成的 JSON；后端契约修改后重新运行导出脚本，避免前后端样例漂移。

```powershell
cd backend
.\venv\Scripts\python.exe scripts\export_frontend_contract.py
```
