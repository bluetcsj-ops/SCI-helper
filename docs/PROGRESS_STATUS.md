# 当前模块进度表

更新日期：2026-06-16

## 总体判断

当前项目已经形成“单用户本地科研助手原型”，其中 Dr. Data Lin 数据分析工作区完成度最高；Prof. RadOnc Mentor、Alex Writer、Rev. Dr. Helena Skov 仍以角色定义和局部原型为主，离完整路线目标还有明显差距。

## 分模块进度

### 1. Prof. RadOnc Mentor（虚拟导师）

- 已完成：
  - 角色定义
  - Agent 注册与基础对话入口
- 未完成：
  - 研究趋势数据库
  - 2019-2024 趋势展示
  - 2025-2030 趋势预测
  - 能力问卷
  - 设备/数据/能力画像分析
  - 2-3 个课题推荐卡
  - 《研究方向建议书》
- 当前结论：
  - 这条线此前基本还未进入“可用”状态，应作为下一优先级补齐

### 2. Project Manager Rhea（项目督促员）

- 已完成：
  - 项目面板基础结构
  - 阶段/任务/提醒原型
  - 计划草稿生成与应用
  - 风险提醒展示
- 部分完成：
  - 项目进度仪表盘
  - 提醒刷新与归档
- 未完成：
  - Telegram / Email 真实发送
  - 自动重排期
  - 双项目资源冲突计算
- 当前结论：
  - 原型可演示，但还不是完整督促系统

### 3. Dr. Data Lin（数据分析师）

- 已完成：
  - 数据需求清单
  - CSV 上传与字段覆盖检查
  - 缺失率、唯一值、数值范围质控
  - 脱敏与隐私风险检查
  - 数据操作审计日志
  - 描述统计草稿
  - 候选检验建议
  - 图表预览与 SVG 导出
  - 可复现实验脚本导出
  - 正式检验人工确认流程
  - 正式检验原型：
    - Welch t
    - 宽表配对 t
    - 长表两条件配对 t
    - 长表 Friedman
    - 单因素 ANOVA
    - Welch ANOVA
    - Kruskal-Wallis
  - 事后比较：
    - Tukey HSD 风格
    - Games-Howell 风格
    - Dunn 风格
    - 配对秩和风格
  - 多重比较校正：
    - Holm-Bonferroni
    - Benjamini-Hochberg FDR
  - 重复测量 ANOVA 设计识别与边界判断（`rm_anova`）
- 未完成：
  - SciPy 安装后的精度路径实测
  - 完整 repeated-measures ANOVA 统计量计算
  - 混合效应模型
  - 更强专用统计库复核
- 是否影响整体使用：
  - 不构成当前全局主阻塞
  - 影响的是统计严谨度上限，不影响原型继续向虚拟导师和写作助手扩展
- 当前结论：
  - 这是目前最成熟的一条产品线

### 4. Alex Writer（SCI 写作助手）

- 已完成：
  - 与数据分析结果的基础衔接
  - Results 摘要交接原型
- 未完成：
  - 写作风格学习
  - 文献真实检索与引用管理
  - Introduction / Methods / Discussion 全链路写作
  - 期刊模板排版与投稿清单
- 当前结论：
  - 仍处于早期原型阶段

### 5. Rev. Dr. Helena Skov（审稿官）

- 已完成：
  - 角色定义
  - Agent 注册与基础对话入口
- 未完成：
  - 模拟审稿报告
  - AI 痕迹审查
  - Response to Reviewers 草稿
- 当前结论：
  - 基本尚未落地

### 6. 平台与基础设施

- 已完成：
  - 前后端原型
  - SQLite 持久化
  - 项目权限原型
  - 本地单用户使用路径
- 部分完成：
  - DeepSeek / OpenAI 可切换的基础调用结构
- 未完成：
  - PostgreSQL / Redis / Celery
  - Telegram / Email
  - 真实文献检索
  - 代码执行沙箱产品化
- 当前结论：
  - 当前更接近“可运行原型”，还不是完整平台

## 当前优先级建议

1. 先补 Prof. RadOnc Mentor 的最小可用版本：趋势展示、能力问卷、课题推荐卡
2. 再补 Alex Writer 的 Methods / Results 连贯草稿能力
3. 最后回到 Dr. Data Lin 的高阶统计增强：完整 repeated-measures ANOVA、mixed effects model、SciPy 精度复核
