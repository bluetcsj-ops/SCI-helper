# Backend

FastAPI 后端服务目录。

## 职责

- 提供项目、任务、仪表盘和 Agent 对话 API。
- 管理五个可咨询智能体的角色配置。
- 通过 Orchestrator 协调智能体工作流。
- 使用 SQLite 保存项目、任务和聊天记录。
- 默认使用 DeepSeek API 生成真实 Agent 回复；未配置 key 时自动回退模拟回复。

## 数据库

当前后端已接入 SQLite 本地持久化。默认数据库文件为：

```text
backend/sci_workshop.db
```

如果数据库为空，应用启动时会自动写入 Project A / Project B 初始数据。

## LLM 配置

默认真实 Agent 调用走 DeepSeek：

```text
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的 DeepSeek API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

OpenAI 端仍保留。如需切回 OpenAI：

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=你的 OpenAI API Key
OPENAI_MODEL=gpt-4o
```

如果当前 provider 没有配置 API key，系统会自动回退到模拟回复。

## 本地运行

建议先创建虚拟环境，再安装依赖：

```powershell
cd "J:\Radiation Therapy SCI assitant\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后可访问：

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/api/agents/`
- `GET http://localhost:8000/api/projects/`
- `GET http://localhost:8000/api/dashboard/`
- `POST http://localhost:8000/api/chat/`

## API 示例

```json
{
  "agent_id": "study_planner",
  "project_id": "project-a",
  "message": "请帮我制定实验方案"
}
```
