# 项目交接记录

更新时间：2026-06-19

## 项目定位

本项目是“放射治疗物理师私人 SCI 论文工场”的本地原型工程。当前目标是先建立可运行、可扩展、可带示例医学数据跑通的多智能体论文工作台，再逐步接入真实科研数据、真实文献检索、深度写作和审稿能力。

## 当前状态

当前 `main` 分支包含未提交改动，主要集中在：

- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/public/sample-data/`
- `shared/sample-data/README.md`
- `docs/`

当前大框架已闭环：

```text
Mentor → Protocol → Data Lin → Alex Writer → Reviewer
```

## 本轮新增重点

- 工作台布局完成：项目横排、智能体横排、左侧对话/任务/Rhea、右侧专家工作区。
- 新增论文流程总览条，5 个阶段可点击跳转。
- 接入预备 DATA：
  - `frontend/public/sample-data/mimic_iv_demo_los_sample.csv`
  - `frontend/public/sample-data/prepared_references.json`
  - `shared/sample-data/README.md`
- Dr. Data Lin 新增：
  - `加载预备 DATA`
  - `一键联调到 Writer`
  - 联调状态提示
  - 自动保存分析记录
- Alex Writer 新增 Methods / Results 草稿和导出。
- Reviewer 新增投稿前审稿清单和导出。
- Vera Protocol 新增方案质量检查和导出。

## 当前验证记录

最近一次验证通过：

```powershell
cd "D:\SCI helper\SCI-helper\frontend"
.\node_modules\.bin\tsc.cmd --noEmit
```

接口验证通过：

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3000/
```

预备 CSV 质控接口通过：

```powershell
$csv = Get-Content -Raw -Encoding UTF8 frontend\public\sample-data\mimic_iv_demo_los_sample.csv
Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/api/projects/project-a/data/quality-report?file_name=mimic_iv_demo_los_sample.csv' -Method POST -ContentType 'text/csv' -Body $csv
```

预备 CSV 统计接口通过：

```powershell
$csv = Get-Content -Raw -Encoding UTF8 frontend\public\sample-data\mimic_iv_demo_los_sample.csv
Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/api/projects/project-a/data/statistics-report?file_name=mimic_iv_demo_los_sample.csv&group_column=gender&outcome_columns=anchor_age,length_of_stay_days' -Method POST -ContentType 'text/csv' -Body $csv
```

分析记录保存接口也已验证过，返回 HTTP 200。

## 手动验收清单

建议在浏览器中按以下顺序手动验收：

1. 打开 `http://127.0.0.1:3000/`。
2. 确认 Project A / Project B 横向排列。
3. 确认 5 个智能体横向排列。
4. 查看“论文流程总览”，点击每个阶段，确认可切换到对应智能体。
5. 点击 `Prof. RadOnc Mentor`。
6. 点击 `加载预备引用`，确认候选引用清单出现。
7. 点击 `Dr. Vera Protocol`。
8. 查看“方案质量检查”，确认显示完成度、风险项和导出按钮。
9. 点击 `Dr. Data Lin`。
10. 点击 `一键联调到 Writer`。
11. 确认状态依次出现：
    - 正在加载预备 DATA
    - 正在生成质控报告
    - 正在生成统计草案
    - 正在保存分析记录
    - 已切换到 Alex Writer
12. 在 Alex Writer 中确认 Methods / Results 草稿出现。
13. 点击 `导出结果`，确认可下载 `methods-results-draft.md`。
14. 回到 Dr. Data Lin，确认“已保存报告”里可恢复记录。
15. 点击 `Rev. Dr. Helena Skov`。
16. 查看投稿前审稿清单，确认有高风险 / 需复核 / 已通过汇总。
17. 点击 `导出清单`，确认可下载 `pre-submission-review.md`。

## 当前限制

- 当前预备 CSV 是 ICU/EHR 示例数据，不是放疗专科数据；用于流程联调，不代表正式课题数据。
- 当前统计路线仍以规则型和描述性统计为主，自主选择分析方法尚未实现。
- Reviewer 是规则型自查，不替代真实同行评审。
- Writer 尚未完成 Discussion、Abstract、投稿模板和风格学习。
- Codex 内置浏览器控制在当前 Windows 沙箱中曾报权限错误，因此部分 UI 点击仍建议人工验收。

## 本地启动方式

后端：

```powershell
cd "D:\SCI helper\SCI-helper\backend"
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd "D:\SCI helper\SCI-helper\frontend"
npm.cmd run dev -- --host 127.0.0.1 --port 3000
```

## 提交前建议

1. 跑 `tsc --noEmit`。
2. 打开前端页面确认 `200`。
3. 跑预备 CSV 质控和统计接口。
4. 人工跑一遍手动验收清单。
5. 确认 `git diff` 只包含本轮前端、样本数据和文档改动。
