import {
  Activity,
  BarChart3,
  BellRing,
  BookOpenCheck,
  CalendarCheck2,
  ClipboardCheck,
  FileText,
  ListChecks,
  Loader2,
  MessageSquareText,
  RefreshCw,
  Save,
  Send,
  ShieldCheck,
  Sparkles,
  Wand2,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  applyProjectPlanDraft,
  dismissProjectReminder,
  draftProjectProtocol,
  extractProjectProtocol,
  generateProjectPlanDraftFromProtocol,
  getAgents,
  getDashboard,
  getProjectPlanDrafts,
  getProjectProtocol,
  getProjectReminders,
  getProjects,
  refreshProjectReminders,
  saveProjectProtocol,
  sendChat,
  updateTaskStatus,
} from "./api";
import type {
  AgentId,
  AgentProfile,
  ChatMessage,
  DashboardSummary,
  ItemStatus,
  Project,
  ProjectPlanDraft,
  ProjectProtocol,
  ProjectProtocolUpdate,
  ProjectReminderSummary,
  ReminderType,
  RiskLevel,
} from "./types";

const agentIcons = {
  mentor: BookOpenCheck,
  project_manager: CalendarCheck2,
  study_planner: ClipboardCheck,
  data_analyst: BarChart3,
  writer: FileText,
  reviewer: ShieldCheck,
} satisfies Record<AgentId, typeof BookOpenCheck>;

const riskLabels: Record<RiskLevel, string> = {
  green: "正常",
  orange: "轻微延误",
  red: "严重风险",
};

const statusLabels: Record<ItemStatus, string> = {
  not_started: "未开始",
  in_progress: "进行中",
  blocked: "受阻",
  done: "已完成",
};

const reminderTypeLabels: Record<ReminderType, string> = {
  due_48h: "48 小时提醒",
  due_24h: "24 小时提醒",
  overdue: "逾期",
  blocked: "受阻",
};

const statusOptions: ItemStatus[] = ["not_started", "in_progress", "blocked", "done"];

const protocolFields: Array<{
  key: keyof ProjectProtocolUpdate;
  label: string;
  rows: number;
}> = [
  { key: "research_question", label: "研究问题", rows: 4 },
  { key: "hypothesis", label: "研究假设", rows: 4 },
  { key: "study_type", label: "研究类型", rows: 3 },
  { key: "primary_endpoint", label: "主要终点", rows: 3 },
  { key: "secondary_endpoints", label: "次要终点", rows: 4 },
  { key: "inclusion_criteria", label: "纳入标准", rows: 4 },
  { key: "exclusion_criteria", label: "排除标准", rows: 4 },
  { key: "data_requirements", label: "数据需求", rows: 5 },
  { key: "experiment_workflow", label: "实验流程", rows: 5 },
  { key: "statistical_plan", label: "统计路线", rows: 5 },
  { key: "target_journals", label: "目标期刊", rows: 3 },
  { key: "rhea_milestones", label: "Rhea 里程碑", rows: 4 },
];

type ProtocolSectionId = "core" | "criteria" | "analysis" | "submission";

const protocolFieldMap = Object.fromEntries(
  protocolFields.map((field) => [field.key, field]),
) as Record<keyof ProjectProtocolUpdate, (typeof protocolFields)[number]>;

const protocolSections: Array<{
  id: ProtocolSectionId;
  title: string;
  fields: Array<keyof ProjectProtocolUpdate>;
}> = [
  {
    id: "core",
    title: "核心问题",
    fields: [
      "research_question",
      "hypothesis",
      "study_type",
      "primary_endpoint",
      "secondary_endpoints",
    ],
  },
  {
    id: "criteria",
    title: "病例与数据",
    fields: ["inclusion_criteria", "exclusion_criteria", "data_requirements"],
  },
  {
    id: "analysis",
    title: "流程与统计",
    fields: ["experiment_workflow", "statistical_plan"],
  },
  {
    id: "submission",
    title: "投稿与里程碑",
    fields: ["target_journals", "rhea_milestones"],
  },
];

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function toProtocolUpdate(protocol: ProjectProtocol): ProjectProtocolUpdate {
  const { project_id: _projectId, ...payload } = protocol;
  return payload;
}

function hasProtocolContent(protocol: ProjectProtocol | null): boolean {
  if (!protocol) {
    return false;
  }

  return protocolFields.some(({ key }) => protocol[key].trim().length > 0);
}

function App() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [agents, setAgents] = useState<AgentProfile[]>([]);
  const [selectedAgentId, setSelectedAgentId] = useState<AgentId>("study_planner");
  const [selectedProjectId, setSelectedProjectId] = useState<string>("project-a");
  const [protocol, setProtocol] = useState<ProjectProtocol | null>(null);
  const [planDrafts, setPlanDrafts] = useState<ProjectPlanDraft[]>([]);
  const [selectedPlanDraftId, setSelectedPlanDraftId] = useState<number | null>(null);
  const [reminderSummary, setReminderSummary] = useState<ProjectReminderSummary | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("请帮我制定实验方案");
  const [isLoading, setIsLoading] = useState(true);
  const [isProtocolLoading, setIsProtocolLoading] = useState(false);
  const [isProtocolSaving, setIsProtocolSaving] = useState(false);
  const [isPlanGenerating, setIsPlanGenerating] = useState(false);
  const [isPlanDraftLoading, setIsPlanDraftLoading] = useState(false);
  const [isPlanDraftApplying, setIsPlanDraftApplying] = useState(false);
  const [isReminderLoading, setIsReminderLoading] = useState(false);
  const [showAllTasks, setShowAllTasks] = useState(false);
  const [showAllDraftTasks, setShowAllDraftTasks] = useState(false);
  const [openProtocolSections, setOpenProtocolSections] = useState<
    Record<ProtocolSectionId, boolean>
  >({
    core: true,
    criteria: false,
    analysis: false,
    submission: false,
  });
  const [extractingMessageId, setExtractingMessageId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);
  const [dismissingReminderId, setDismissingReminderId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgentId),
    [agents, selectedAgentId],
  );

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId),
    [projects, selectedProjectId],
  );

  const protocolHasContent = useMemo(() => hasProtocolContent(protocol), [protocol]);

  const selectedPlanDraft = useMemo(
    () => planDrafts.find((draft) => draft.id === selectedPlanDraftId) ?? null,
    [planDrafts, selectedPlanDraftId],
  );

  const visibleTasks = useMemo(() => {
    if (!selectedProject) {
      return [];
    }
    return showAllTasks ? selectedProject.tasks : selectedProject.tasks.slice(0, 3);
  }, [selectedProject, showAllTasks]);

  const visibleDraftTasks = useMemo(() => {
    if (!selectedPlanDraft) {
      return [];
    }
    return showAllDraftTasks ? selectedPlanDraft.tasks : selectedPlanDraft.tasks.slice(0, 3);
  }, [selectedPlanDraft, showAllDraftTasks]);

  const visibleReminders = useMemo(() => {
    if (!reminderSummary) {
      return [];
    }
    return reminderSummary.reminders.slice(0, 3);
  }, [reminderSummary]);

  useEffect(() => {
    loadWorkspace();
  }, []);

  useEffect(() => {
    setShowAllTasks(false);
    setShowAllDraftTasks(false);
    setOpenProtocolSections({
      core: true,
      criteria: false,
      analysis: false,
      submission: false,
    });
  }, [selectedProjectId]);

  useEffect(() => {
    let isCurrent = true;

    async function loadPlanDrafts() {
      if (!selectedProjectId) {
        setPlanDrafts([]);
        setSelectedPlanDraftId(null);
        return;
      }

      setIsPlanDraftLoading(true);
      setError(null);

      try {
        const draftData = await getProjectPlanDrafts(selectedProjectId);
        if (isCurrent) {
          setPlanDrafts(draftData);
          setSelectedPlanDraftId(draftData[0]?.id ?? null);
        }
      } catch (caughtError) {
        if (isCurrent) {
          setError(caughtError instanceof Error ? caughtError.message : "计划草案读取失败。");
          setPlanDrafts([]);
          setSelectedPlanDraftId(null);
        }
      } finally {
        if (isCurrent) {
          setIsPlanDraftLoading(false);
        }
      }
    }

    loadPlanDrafts();

    return () => {
      isCurrent = false;
    };
  }, [selectedProjectId]);

  useEffect(() => {
    let isCurrent = true;

    async function loadReminders() {
      if (!selectedProjectId) {
        setReminderSummary(null);
        return;
      }

      setIsReminderLoading(true);
      setError(null);

      try {
        const reminderData = await getProjectReminders(selectedProjectId);
        if (isCurrent) {
          setReminderSummary(reminderData);
        }
      } catch (caughtError) {
        if (isCurrent) {
          setError(caughtError instanceof Error ? caughtError.message : "Rhea 监控提醒读取失败。");
          setReminderSummary(null);
        }
      } finally {
        if (isCurrent) {
          setIsReminderLoading(false);
        }
      }
    }

    loadReminders();

    return () => {
      isCurrent = false;
    };
  }, [selectedProjectId]);

  useEffect(() => {
    let isCurrent = true;

    async function loadProtocol() {
      if (!selectedProjectId) {
        setProtocol(null);
        return;
      }

      setIsProtocolLoading(true);
      setError(null);

      try {
        const protocolData = await getProjectProtocol(selectedProjectId);
        if (isCurrent) {
          setProtocol(protocolData);
        }
      } catch (caughtError) {
        if (isCurrent) {
          setError(caughtError instanceof Error ? caughtError.message : "研究方案读取失败。");
          setProtocol(null);
        }
      } finally {
        if (isCurrent) {
          setIsProtocolLoading(false);
        }
      }
    }

    loadProtocol();

    return () => {
      isCurrent = false;
    };
  }, [selectedProjectId]);

  async function loadWorkspace() {
    setIsLoading(true);
    setError(null);

    try {
      const [dashboardData, projectData, agentData] = await Promise.all([
        getDashboard(),
        getProjects(),
        getAgents(),
      ]);
      setDashboard(dashboardData);
      setProjects(projectData);
      setAgents(agentData);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "前端无法连接后端服务。");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedInput = input.trim();
    if (!trimmedInput || isSending) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      speaker: "user",
      projectId: selectedProjectId || null,
      content: trimmedInput,
    };

    setMessages((current) => [...current, userMessage]);
    setInput("");
    setIsSending(true);
    setError(null);

    try {
      const response = await sendChat({
        agent_id: selectedAgentId,
        project_id: selectedProjectId || null,
        message: trimmedInput,
      });

      const agentMessage: ChatMessage = {
        id: crypto.randomUUID(),
        speaker: "agent",
        agentId: response.agent_id,
        projectId: response.project_id,
        agentName: response.agent_name,
        content: response.reply,
        suggestedNextActions: response.suggested_next_actions,
      };

      setMessages((current) => [...current, agentMessage]);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "消息发送失败。");
    } finally {
      setIsSending(false);
    }
  }

  async function handleTaskStatusChange(projectId: string, taskId: string, status: ItemStatus) {
    setUpdatingTaskId(taskId);
    setError(null);

    try {
      const updatedProject = await updateTaskStatus(projectId, taskId, status);
      const [dashboardData, reminderData] = await Promise.all([
        getDashboard(),
        getProjectReminders(projectId),
      ]);

      setProjects((current) =>
        current.map((project) => (project.id === updatedProject.id ? updatedProject : project)),
      );
      setDashboard(dashboardData);
      setReminderSummary(reminderData);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "任务状态更新失败。");
    } finally {
      setUpdatingTaskId(null);
    }
  }

  async function handleRefreshReminders() {
    if (!selectedProjectId || isReminderLoading) {
      return;
    }

    setIsReminderLoading(true);
    setError(null);

    try {
      const reminderData = await refreshProjectReminders(selectedProjectId);
      const dashboardData = await getDashboard();
      setReminderSummary(reminderData);
      setDashboard(dashboardData);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Rhea 监控提醒刷新失败。");
    } finally {
      setIsReminderLoading(false);
    }
  }

  async function handleDismissReminder(reminderId: number) {
    if (!selectedProjectId || dismissingReminderId !== null) {
      return;
    }

    setDismissingReminderId(reminderId);
    setError(null);

    try {
      const reminderData = await dismissProjectReminder(selectedProjectId, reminderId);
      setReminderSummary(reminderData);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "提醒归档失败。");
    } finally {
      setDismissingReminderId(null);
    }
  }

  async function handleCreateDraftProtocol() {
    if (!selectedProjectId) {
      return;
    }

    setIsProtocolSaving(true);
    setError(null);

    try {
      const protocolData = await draftProjectProtocol(selectedProjectId);
      setProtocol(protocolData);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "研究方案草案生成失败。");
    } finally {
      setIsProtocolSaving(false);
    }
  }

  async function handleSaveProtocol() {
    if (!selectedProjectId || !protocol) {
      return;
    }

    setIsProtocolSaving(true);
    setError(null);

    try {
      const savedProtocol = await saveProjectProtocol(selectedProjectId, toProtocolUpdate(protocol));
      setProtocol(savedProtocol);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "研究方案保存失败。");
    } finally {
      setIsProtocolSaving(false);
    }
  }

  async function handleExtractProtocolFromMessage(message: ChatMessage) {
    const targetProjectId = message.projectId ?? selectedProjectId;
    if (!targetProjectId || extractingMessageId) {
      return;
    }

    setExtractingMessageId(message.id);
    setError(null);

    try {
      const extractedProtocol = await extractProjectProtocol(targetProjectId, message.content);
      if (targetProjectId !== selectedProjectId) {
        setSelectedProjectId(targetProjectId);
      }
      setProtocol(extractedProtocol);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "研究方案写入失败。");
    } finally {
      setExtractingMessageId(null);
    }
  }

  async function handleGeneratePlanFromProtocol() {
    if (!selectedProjectId || isPlanGenerating) {
      return;
    }

    setIsPlanGenerating(true);
    setError(null);

    try {
      const newDraft = await generateProjectPlanDraftFromProtocol(selectedProjectId);
      setPlanDrafts((current) => [
        newDraft,
        ...current.filter((draft) => draft.id !== newDraft.id),
      ]);
      setSelectedPlanDraftId(newDraft.id);
      setShowAllDraftTasks(false);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "计划草案生成失败。");
    } finally {
      setIsPlanGenerating(false);
    }
  }

  async function handleApplyPlanDraft(draftId: number) {
    if (!selectedProjectId || isPlanDraftApplying) {
      return;
    }

    const shouldApplyPlan = window.confirm("应用该计划草案会替换当前项目的阶段和任务，是否继续？");
    if (!shouldApplyPlan) {
      return;
    }

    setIsPlanDraftApplying(true);
    setError(null);

    try {
      const updatedProject = await applyProjectPlanDraft(selectedProjectId, draftId);
      const [dashboardData, draftData, reminderData] = await Promise.all([
        getDashboard(),
        getProjectPlanDrafts(selectedProjectId),
        getProjectReminders(selectedProjectId),
      ]);

      setProjects((current) =>
        current.map((project) => (project.id === updatedProject.id ? updatedProject : project)),
      );
      setDashboard(dashboardData);
      setPlanDrafts(draftData);
      setReminderSummary(reminderData);
      setSelectedPlanDraftId(draftId);
      setShowAllTasks(false);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "计划草案应用失败。");
    } finally {
      setIsPlanDraftApplying(false);
    }
  }

  function updateProtocolField(fieldName: keyof ProjectProtocolUpdate, value: string) {
    setProtocol((current) => {
      const baseProtocol: ProjectProtocol = current ?? {
        project_id: selectedProjectId,
        research_question: "",
        hypothesis: "",
        study_type: "",
        primary_endpoint: "",
        secondary_endpoints: "",
        inclusion_criteria: "",
        exclusion_criteria: "",
        data_requirements: "",
        experiment_workflow: "",
        statistical_plan: "",
        target_journals: "",
        rhea_milestones: "",
      };

      return {
        ...baseProtocol,
        [fieldName]: value,
      };
    });
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Radiation Therapy SCI Workshop</p>
          <h1>我的研究书房</h1>
        </div>
        <button className="icon-button" type="button" onClick={loadWorkspace} title="刷新工作台">
          <RefreshCw aria-hidden="true" size={18} />
        </button>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      {isLoading ? (
        <section className="loading-state">
          <Loader2 aria-hidden="true" className="spin" size={24} />
          <span>正在连接论文工场...</span>
        </section>
      ) : (
        <div className="workspace-grid">
          <section className="dashboard-band" aria-label="项目总览">
            <div className="manager-panel">
              <CalendarCheck2 aria-hidden="true" size={22} />
              <div>
                <span>{dashboard?.manager_role ?? "全流程实施监控员"}</span>
                <strong>{dashboard?.manager_name ?? "Rhea Chen"}</strong>
                <p>{dashboard?.manager_message}</p>
              </div>
            </div>
            <div className="metric">
              <span className="metric-label">总体完成</span>
              <strong>{dashboard?.overall_completion_percent ?? 0}%</strong>
            </div>
            <div className="metric">
              <span className="metric-label">活跃项目</span>
              <strong>{dashboard?.active_project_count ?? 0}</strong>
            </div>
            <div className={`risk-pill risk-${dashboard?.risk_level ?? "green"}`}>
              <Activity aria-hidden="true" size={16} />
              {riskLabels[dashboard?.risk_level ?? "green"]}
            </div>
            <p>{dashboard?.encouragement}</p>
          </section>

          <section className="projects-column" aria-label="论文项目">
            <div className="section-heading">
              <h2>项目进度</h2>
              <span>{projects.length} 个项目</span>
            </div>

            <div className="project-list">
              {projects.map((project) => (
                <button
                  className={`project-card ${selectedProjectId === project.id ? "selected" : ""}`}
                  key={project.id}
                  type="button"
                  onClick={() => setSelectedProjectId(project.id)}
                >
                  <div className="project-card-head">
                    <span>{project.name}</span>
                    <span className={`risk-dot risk-${project.risk_level}`}>{riskLabels[project.risk_level]}</span>
                  </div>
                  <h3>{project.title}</h3>
                  <p>{project.topic}</p>
                  <div className="progress-row">
                    <div className="progress-track">
                      <span
                        className={`progress-fill risk-${project.risk_level}`}
                        style={{ width: `${project.progress_percent}%` }}
                      />
                    </div>
                    <strong>{project.progress_percent}%</strong>
                  </div>
                  <dl className="project-facts">
                    <div>
                      <dt>当前阶段</dt>
                      <dd>{project.current_phase}</dd>
                    </div>
                    <div>
                      <dt>下一节点</dt>
                      <dd>
                        {formatDate(project.next_due_date)} · {project.next_milestone}
                      </dd>
                    </div>
                  </dl>
                </button>
              ))}
            </div>

            {selectedProject ? (
              <>
                <section className="rhea-monitor-panel" aria-label="Rhea 监控中心">
                  <div className="rhea-monitor-head">
                    <div>
                      <p className="eyebrow">Rhea 监控中心</p>
                      <h3>全流程实施提醒</h3>
                    </div>
                    <button
                      className="icon-button"
                      type="button"
                      onClick={handleRefreshReminders}
                      disabled={isReminderLoading}
                      title="刷新 Rhea 监控"
                    >
                      {isReminderLoading ? (
                        <Loader2 aria-hidden="true" className="spin" size={17} />
                      ) : (
                        <RefreshCw aria-hidden="true" size={17} />
                      )}
                    </button>
                  </div>

                  <div className="rhea-monitor-summary">
                    <div className={`risk-pill risk-${reminderSummary?.risk_level ?? "green"}`}>
                      <BellRing aria-hidden="true" size={16} />
                      {riskLabels[reminderSummary?.risk_level ?? "green"]}
                    </div>
                    <span>{reminderSummary?.active_count ?? 0} 条提醒</span>
                    <span>{reminderSummary?.overdue_count ?? 0} 个逾期</span>
                    <span>{reminderSummary?.blocked_count ?? 0} 个受阻</span>
                  </div>

                  <p className="rhea-monitor-note">
                    {reminderSummary?.manager_note ?? "Rhea 正在读取当前项目的执行状态。"}
                  </p>

                  {isReminderLoading && !reminderSummary ? (
                    <div className="protocol-loading compact">
                      <Loader2 aria-hidden="true" className="spin" size={18} />
                      <span>正在生成 Rhea 监控提醒...</span>
                    </div>
                  ) : visibleReminders.length ? (
                    <div className="rhea-reminder-list">
                      {visibleReminders.map((reminder) => (
                        <article className="rhea-reminder-item" key={reminder.id}>
                          <div>
                            <span className={`status-badge risk-${reminder.severity}`}>
                              {reminderTypeLabels[reminder.reminder_type]}
                            </span>
                            <h4>{reminder.task_title}</h4>
                            <p>{reminder.message}</p>
                            <small>
                              截止：{formatDate(reminder.due_date)} · {reminder.suggested_action}
                            </small>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleDismissReminder(reminder.id)}
                            disabled={dismissingReminderId === reminder.id}
                          >
                            {dismissingReminderId === reminder.id ? (
                              <Loader2 aria-hidden="true" className="spin" size={15} />
                            ) : (
                              <ClipboardCheck aria-hidden="true" size={15} />
                            )}
                            <span>归档</span>
                          </button>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="rhea-monitor-empty">当前没有需要处理的提醒。这个状态很舒服，继续稳稳推进。</p>
                  )}
                </section>

                <div className="task-panel">
                  <div className="task-panel-head">
                    <div>
                      <p className="eyebrow">{selectedProject.name}</p>
                      <h3>本阶段任务</h3>
                      <small>
                        显示 {visibleTasks.length} / {selectedProject.tasks.length}
                      </small>
                    </div>
                    <ListChecks aria-hidden="true" size={20} />
                  </div>

                  <div className="task-list">
                    {visibleTasks.map((task) => (
                      <article className="task-item" key={task.id}>
                        <div className="task-main">
                          <span className={`status-badge status-${task.status}`}>
                            {statusLabels[task.status]}
                          </span>
                          <h4>{task.title}</h4>
                          <p>{task.deliverable}</p>
                          <small>截止：{formatDate(task.due_date)}</small>
                        </div>
                        <select
                          aria-label={`更新 ${task.title} 的状态`}
                          value={task.status}
                          disabled={updatingTaskId === task.id}
                          onChange={(event) =>
                            handleTaskStatusChange(
                              selectedProject.id,
                              task.id,
                              event.target.value as ItemStatus,
                            )
                          }
                        >
                          {statusOptions.map((status) => (
                            <option key={status} value={status}>
                              {statusLabels[status]}
                            </option>
                          ))}
                        </select>
                      </article>
                    ))}
                  </div>

                  {selectedProject.tasks.length > 3 ? (
                    <button
                      className="panel-toggle"
                      type="button"
                      onClick={() => setShowAllTasks((current) => !current)}
                    >
                      {showAllTasks ? "收起任务" : `展开全部 ${selectedProject.tasks.length} 项任务`}
                    </button>
                  ) : null}
                </div>

                <section className="protocol-panel" aria-label="研究方案">
                  <div className="protocol-head">
                    <div>
                      <p className="eyebrow">{selectedProject.name}</p>
                      <h3>研究方案</h3>
                    </div>
                    <div className="protocol-actions">
                      <button
                        type="button"
                        onClick={handleCreateDraftProtocol}
                        disabled={isProtocolLoading || isProtocolSaving}
                        title="生成方案草案"
                      >
                        {isProtocolSaving && !protocolHasContent ? (
                          <Loader2 aria-hidden="true" className="spin" size={16} />
                        ) : (
                          <Wand2 aria-hidden="true" size={16} />
                        )}
                        <span>草案</span>
                      </button>
                      <button
                        type="button"
                        onClick={handleGeneratePlanFromProtocol}
                        disabled={
                          isProtocolLoading ||
                          isProtocolSaving ||
                          isPlanGenerating ||
                          !protocolHasContent
                        }
                        title="生成计划草案"
                      >
                        {isPlanGenerating ? (
                          <Loader2 aria-hidden="true" className="spin" size={16} />
                        ) : (
                          <ListChecks aria-hidden="true" size={16} />
                        )}
                        <span>草案</span>
                      </button>
                      <button
                        type="button"
                        onClick={handleSaveProtocol}
                        disabled={isProtocolLoading || isProtocolSaving || !protocol}
                        title="保存研究方案"
                      >
                        {isProtocolSaving && protocolHasContent ? (
                          <Loader2 aria-hidden="true" className="spin" size={16} />
                        ) : (
                          <Save aria-hidden="true" size={16} />
                        )}
                        <span>保存</span>
                      </button>
                    </div>
                  </div>

                  {isProtocolLoading ? (
                    <div className="protocol-loading">
                      <Loader2 aria-hidden="true" className="spin" size={18} />
                      <span>正在读取研究方案...</span>
                    </div>
                  ) : (
                    <div className="protocol-sections">
                      {protocolSections.map((section) => {
                        const isOpen = openProtocolSections[section.id];
                        return (
                          <section className="protocol-section" key={section.id}>
                            <button
                              className="protocol-section-trigger"
                              type="button"
                              onClick={() =>
                                setOpenProtocolSections((current) => ({
                                  ...current,
                                  [section.id]: !current[section.id],
                                }))
                              }
                            >
                              <span>{section.title}</span>
                              <small>{isOpen ? "收起" : "展开"}</small>
                            </button>
                            {isOpen ? (
                              <div className="protocol-form">
                                {section.fields.map((fieldKey) => {
                                  const field = protocolFieldMap[fieldKey];
                                  return (
                                    <label className="protocol-field" key={field.key}>
                                      <span>{field.label}</span>
                                      <textarea
                                        rows={field.rows}
                                        value={protocol?.[field.key] ?? ""}
                                        onChange={(event) =>
                                          updateProtocolField(field.key, event.target.value)
                                        }
                                      />
                                    </label>
                                  );
                                })}
                              </div>
                            ) : null}
                          </section>
                        );
                      })}
                    </div>
                  )}

                  <div className="plan-draft-panel">
                    <div className="plan-draft-head">
                      <div>
                        <p className="eyebrow">Rhea 执行计划</p>
                        <h4>{selectedPlanDraft ? selectedPlanDraft.version_label : "暂无计划草案"}</h4>
                        <small>
                          {selectedPlanDraft
                            ? `生成于 ${formatDateTime(selectedPlanDraft.created_at)}`
                            : "先生成草案，确认后再应用到当前项目。"}
                        </small>
                      </div>
                      {planDrafts.length > 1 ? (
                        <select
                          aria-label="选择计划草案"
                          value={selectedPlanDraftId ?? ""}
                          onChange={(event) => {
                            setSelectedPlanDraftId(Number(event.target.value));
                            setShowAllDraftTasks(false);
                          }}
                        >
                          {planDrafts.map((draft) => (
                            <option key={draft.id} value={draft.id}>
                              {draft.version_label}
                            </option>
                          ))}
                        </select>
                      ) : null}
                    </div>

                    {isPlanDraftLoading ? (
                      <div className="protocol-loading">
                        <Loader2 aria-hidden="true" className="spin" size={18} />
                        <span>正在读取计划草案...</span>
                      </div>
                    ) : selectedPlanDraft ? (
                      <>
                        <div className="draft-meta">
                          <span>{selectedPlanDraft.phases.length} 个阶段</span>
                          <span>{selectedPlanDraft.tasks.length} 项任务</span>
                          {selectedPlanDraft.applied_at ? <span>已应用</span> : <span>未应用</span>}
                        </div>

                        <div className="draft-preview-grid">
                          <div>
                            <h5>阶段预览</h5>
                            {selectedPlanDraft.phases.slice(0, 3).map((phase) => (
                              <article className="draft-row" key={phase.id}>
                                <strong>{phase.title}</strong>
                                <small>
                                  {formatDate(phase.start_date)} - {formatDate(phase.end_date)}
                                </small>
                              </article>
                            ))}
                            {selectedPlanDraft.phases.length > 3 ? (
                              <small className="draft-more">
                                另有 {selectedPlanDraft.phases.length - 3} 个阶段
                              </small>
                            ) : null}
                          </div>

                          <div>
                            <h5>任务预览</h5>
                            {visibleDraftTasks.map((task) => (
                              <article className="draft-row" key={task.id}>
                                <strong>{task.title}</strong>
                                <small>
                                  {formatDate(task.due_date)} · {statusLabels[task.status]}
                                </small>
                              </article>
                            ))}
                            {selectedPlanDraft.tasks.length > 3 ? (
                              <button
                                className="panel-toggle compact"
                                type="button"
                                onClick={() => setShowAllDraftTasks((current) => !current)}
                              >
                                {showAllDraftTasks ? "收起任务" : `展开全部 ${selectedPlanDraft.tasks.length} 项任务`}
                              </button>
                            ) : null}
                          </div>
                        </div>

                        <button
                          className="apply-draft-button"
                          type="button"
                          onClick={() => handleApplyPlanDraft(selectedPlanDraft.id)}
                          disabled={isPlanDraftApplying}
                        >
                          {isPlanDraftApplying ? (
                            <Loader2 aria-hidden="true" className="spin" size={16} />
                          ) : (
                            <ClipboardCheck aria-hidden="true" size={16} />
                          )}
                          <span>应用该草案</span>
                        </button>
                      </>
                    ) : (
                      <p className="plan-draft-empty">还没有计划草案。点击“草案”后，Rhea 会先生成可预览版本。</p>
                    )}
                  </div>
                </section>
              </>
            ) : null}
          </section>

          <section className="agents-column" aria-label="智能体入口">
            <div className="section-heading">
              <h2>可咨询智能体</h2>
              <span>{agents.length} 位</span>
            </div>

            <div className="agent-list">
              {agents.map((agent) => {
                const Icon = agentIcons[agent.id];
                return (
                  <button
                    className={`agent-button ${selectedAgentId === agent.id ? "selected" : ""}`}
                    key={agent.id}
                    type="button"
                    title={agent.tagline}
                    onClick={() => setSelectedAgentId(agent.id)}
                  >
                    <Icon aria-hidden="true" size={20} />
                    <span>
                      <strong>{agent.name}</strong>
                      <small>{agent.role_name}</small>
                    </span>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="chat-column" aria-label="角色对话">
            <div className="chat-head">
              <div>
                <p className="eyebrow">{selectedAgent?.role_name}</p>
                <h2>{selectedAgent?.name ?? "选择角色"}</h2>
              </div>
              <span className="chat-project-note">关联左侧当前项目</span>
            </div>

            {selectedProject ? (
              <div className="context-strip">
                <Sparkles aria-hidden="true" size={16} />
                <span>{selectedProject.next_milestone}</span>
              </div>
            ) : null}

            <div className="message-list">
              {messages.length === 0 ? (
                <div className="empty-chat">
                  <MessageSquareText aria-hidden="true" size={28} />
                  <p>{selectedAgent?.tagline}</p>
                </div>
              ) : (
                messages.map((message) => (
                  <article className={`message ${message.speaker}`} key={message.id}>
                    <span>{message.speaker === "user" ? "你" : message.agentName}</span>
                    <p>{message.content}</p>
                    {message.suggestedNextActions?.length ? (
                      <ul>
                        {message.suggestedNextActions.map((action) => (
                          <li key={action}>{action}</li>
                        ))}
                      </ul>
                    ) : null}
                    {message.speaker === "agent" && message.agentId === "study_planner" ? (
                      <div className="message-actions">
                        <button
                          type="button"
                          onClick={() => handleExtractProtocolFromMessage(message)}
                          disabled={extractingMessageId !== null}
                          title="写入研究方案"
                        >
                          {extractingMessageId === message.id ? (
                            <Loader2 aria-hidden="true" className="spin" size={15} />
                          ) : (
                            <ClipboardCheck aria-hidden="true" size={15} />
                          )}
                          <span>写入研究方案</span>
                        </button>
                      </div>
                    ) : null}
                  </article>
                ))
              )}
            </div>

            <form className="chat-form" onSubmit={handleSubmit}>
              <input
                aria-label="输入消息"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="输入你想推进的下一步..."
              />
              <button type="submit" disabled={isSending || !input.trim()} title="发送消息">
                {isSending ? <Loader2 aria-hidden="true" className="spin" size={18} /> : <Send aria-hidden="true" size={18} />}
                <span>发送</span>
              </button>
            </form>
          </section>
        </div>
      )}
    </main>
  );
}

export default App;
