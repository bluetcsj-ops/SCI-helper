# Frontend

React 前端应用目录。

## 计划职责

- 展示“我的研究书房”主控台。
- 展示 Project A / Project B 的论文进度。
- 提供五个 Agent 的快捷入口。
- 提供温暖、专业、低焦虑的对话界面。

## 原型实现策略

第一版优先完成可用界面和后端 API 联调，视觉风格保持温暖、清晰、专业，后续再逐步细化动效和完整交互。

## 本地运行

确保后端已运行在 `http://localhost:8000`，然后执行：

```powershell
cd "J:\Radiation Therapy SCI assitant\frontend"
npm.cmd install
npm.cmd run dev
```

启动后访问：

```text
http://localhost:3000
```

如需修改后端地址，可创建 `.env.local`：

```text
VITE_API_BASE_URL=http://localhost:8000
```
