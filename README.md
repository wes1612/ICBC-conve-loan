# 消费供给动态授信 MVP

面向平台型小微商户（美容美发、宠物服务等服务型商户为首批试点行业）的消费供给动态授信方案：
用平台经营数据 + 工行账户与交易数据 + 线下经营数据，替代传统抵押物/财务报表/长期企业信用记录，
为缺少这些的小微商户提供小额、短期、循环、动态调整的经营授信，并用"消费供给缺口"衡量商户还能承接多少消费需求。

核心流程：**商户提交材料 → 系统分析（评分引擎 + LLM材料解析）→ 输出模拟授信及消费策略 → 银行端持续监控**（详见 `docs/流程图.webp`）。

## 最新开发与交接文档

- [模拟网站使用说明](docs/模拟网站使用说明.md)：本地启动、M001/M005 完整演示流程、材料上传、商户端/银行端入口、端口切换及常见问题。
- [项目开发交接与 GitHub 更新指南](docs/项目开发交接与GitHub更新指南.md)：已完成后端、目录与代码索引、前端注意事项、最新 ZIP 差异及安全提交/合并步骤。
- [前后端联调说明](docs/前后端联调说明.md)：API 字段到 UI 的映射、状态语义、CORS、错误处理和联调顺序。
- [后端运行说明](backend/README.md)：安装、启动、测试、Swagger 和脚本命令。
- [AI MVP 实现说明](docs/AI-MVP-implementation.md)：两条 AI 工作流、配置、降级与审计边界。

> 根 README 下方仍保留最初项目规划作为历史背景；当前实际进度以上述交接文档、后端 README 和项目看板为准。

## 团队分工

| 角色 | 负责内容 |
|---|---|
| 产品（你） | 产品需求、业务逻辑、数据字典、测试案例、页面文案 |
| 队员A | 技术架构、前端框架、项目仓库 |
| 队员B | 数据处理、LLM调用、评分规则实现 |

## 仓库结构

```
.
├── frontend/       # 前端项目（React/Next.js，队员A负责初始化）
├── backend/        # 后端项目（Python + FastAPI，队员B负责初始化）
├── data/           # 数据字典与测试商户数据（已就绪，见 data/README.md）
├── docs/           # 产品文档、开发计划、流程图
└── .github/        # Issue模板等协作配置
```

## 技术栈（建议，如无既定方案）

- 前端：React 或 Next.js
- 后端：Python + FastAPI
- 数据库：SQLite（本地/MVP阶段）或 Supabase（需要托管时）
- 图表：常见前端图表库（如 Recharts / Chart.js）
- AI：服务端调用大模型 API（合同/评价解析、报告生成、风险原因归纳）
- 协作：GitHub（本仓库）

## 本地启动（占位，待队员A/B初始化项目后补全）

```bash
# 前端
cd frontend
npm install
npm run dev

# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## 当前进度（第一周）

- [x] MVP需求文档
- [x] 结构化 + 非结构化数据字典（`data/`，含评分规则打分卡、额度映射规则、人工审核规则）
- [x] 评分与额度规则（含消费供给信用相关设计：消费承接能力评分、成长性扩张加成）
- [x] 5个测试商户（结构化+非结构化全量数据，见 `data/`）
- [ ] 页面低保真原型
- [x] GitHub仓库骨架（本仓库）
- [ ] 前端/后端项目初始化（队员A/B）

详细任务清单见 `docs/PROJECT_BOARD.md`，建议直接搬进 GitHub Projects 看板。
