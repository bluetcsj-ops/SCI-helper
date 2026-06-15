# 放射治疗物理师私人 SCI 论文工场

这是一个面向放疗物理师的多智能体 SCI 论文生产平台原型工程。当前阶段先建立可运行、可扩展的工程骨架，再逐步接入真实模型、项目管理、数据分析、写作、审稿、提醒与部署能力。

## 快速入口

- [使用方法](docs/USER_GUIDE.md)
- [项目交接记录](docs/HANDOFF.md)
- [项目范围说明](docs/PROJECT_SCOPE.md)
- [架构设计草案](docs/ARCHITECTURE.md)
- [开发计划](docs/DEVELOPMENT_PLAN.md)

## 当前原型状态

当前 v0.1 原型已经支持：

- FastAPI 后端服务。
- React + Vite 前端页面。
- Project A / Project B 演示项目。
- 五个可咨询智能体角色配置。
- Rhea Chen 常驻仪表盘，作为全流程实施监控员。
- 默认 DeepSeek Agent 真实回复，调用失败或未配置 key 时自动回退模拟回复。
- OpenAI 端保留为可选切换。
- 聊天记录写入 SQLite。
- 任务状态更新，项目进度和风险自动计算。
- Rhea 本地监控中心，可根据任务截止日期和受阻状态生成提醒，并支持归档处理。
- Project Protocol 研究方案模块，可为每个项目生成草案、编辑并保存结构化实验方案。
- Dr. Vera Protocol 的长回复可一键抽取并写入 Project Protocol。
- Rhea 可根据 Project Protocol 生成项目执行计划草案，用户预览确认后再应用到当前阶段、任务、截止日期和交付物。

## 工程目录

- `backend/`：FastAPI 后端服务，负责 API、智能体编排、项目状态、任务管理、聊天和研究方案持久化。
- `frontend/`：React 前端应用，负责“我的研究书房”、项目仪表盘、研究方案表单和角色对话界面。
- `shared/`：预留给前后端共享类型、协议草案与提示词资产。
- `infra/`：预留给部署、数据库、队列、通知服务等基础设施配置。
- `docs/`：产品、架构、迭代计划和工程约定文档。
- `My SCI article/`：用户既往论文资料目录，后续可作为写作风格学习的数据来源。

## 本地启动

启动后端：

```powershell
cd "J:\Radiation Therapy SCI assitant\backend"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动前端：

```powershell
cd "J:\Radiation Therapy SCI assitant\frontend"
npm.cmd run dev
```

访问前端：

```text
http://localhost:3000
```

后端接口文档：

```text
http://localhost:8000/docs
```

本地数据库默认文件：

```text
backend/sci_workshop.db
```

## 原型阶段原则

1. 先保证工程结构清晰、可运行、可扩展。
2. 每个功能优先做可验证的薄切片，再逐步增强。
3. 医学数据和论文内容必须可追溯，不编造数据，不编造文献。
4. 涉及真实 DICOM、临床数据和投稿材料前，必须补齐脱敏、权限、审计和加密策略。
