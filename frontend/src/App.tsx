import {
  Activity,
  BarChart3,
  BellRing,
  BookOpenCheck,
  CalendarCheck2,
  ClipboardCheck,
  Download,
  FileText,
  ListChecks,
  Loader2,
  MessageSquareText,
  RefreshCw,
  Save,
  Send,
  ShieldCheck,
  Sparkles,
  Upload,
  Wand2,
} from "lucide-react";
import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";

import {
  applyProjectPlanDraft,
  dismissProjectReminder,
  draftProjectProtocol,
  extractProjectProtocol,
  generateProjectPlanDraftFromProtocol,
  getAgents,
  getCurrentUser,
  getDataAnalysisRecords,
  getDataAuditLogs,
  getDataRequirements,
  getDashboard,
  getProjectAccess,
  getProjectPlanDrafts,
  getProjectProtocol,
  getProjectReminders,
  getProjects,
  refreshProjectReminders,
  saveDataAnalysisRecord,
  saveProjectProtocol,
  sendChat,
  updateTaskStatus,
  uploadDataQualityReport,
  uploadDataStatisticsReport,
  uploadFormalTestReport,
} from "./api";
import type {
  AgentId,
  AgentProfile,
  ChartSpec,
  ChatMessage,
  DataAuditLog,
  DataAnalysisRecord,
  DataQualityReport,
  DataRequirementSpec,
  DataStatisticsReport,
  DashboardSummary,
  FormalTestConfirmation,
  ItemStatus,
  Project,
  ProjectAccessLevel,
  ProjectAccessPolicy,
  ProjectPlanDraft,
  ProjectProtocol,
  ProjectProtocolUpdate,
  ProjectReminderSummary,
  ReminderType,
  RiskLevel,
  UserProfile,
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

const dataRiskLabels: Record<RiskLevel, string> = {
  green: "低风险",
  orange: "需复核",
  red: "高风险",
};

const projectAccessLabels: Record<ProjectAccessLevel, string> = {
  viewer: "只读",
  editor: "可编辑",
  owner: "负责人",
};

const dataAuditActionLabels: Record<string, string> = {
  quality_report_generated: "生成质控报告",
  statistics_report_generated: "生成统计草案",
  statistics_blocked_privacy_risk: "阻止统计草案",
  formal_test_executed: "执行正式检验",
  formal_test_blocked: "阻止正式检验",
  analysis_record_saved: "保存分析记录",
};

type FormalTestConfirmationKey = Exclude<keyof FormalTestConfirmation, "confirmed_by" | "notes">;

const formalTestConfirmationItems: Array<{
  key: FormalTestConfirmationKey;
  label: string;
  detail: string;
}> = [
  {
    key: "design_confirmed",
    label: "研究设计已确认",
    detail: "已明确独立样本、配对样本或重复测量关系。",
  },
  {
    key: "endpoints_confirmed",
    label: "终点定义已确认",
    detail: "主要/次要终点与当前结局列一致。",
  },
  {
    key: "deidentified_confirmed",
    label: "脱敏状态已确认",
    detail: "CSV 不含可直接识别患者的信息。",
  },
  {
    key: "missing_data_reviewed",
    label: "缺失处理已复核",
    detail: "已接受当前有效样本量和缺失值处理方式。",
  },
  {
    key: "assumptions_reviewed",
    label: "统计假设已复核",
    detail: "已检查分布、方差、异常值和临床合理性。",
  },
  {
    key: "multiplicity_reviewed",
    label: "多重比较已复核",
    detail: "多个结局或多组比较已有解释边界。",
  },
];

function createFormalTestConfirmation(confirmedBy = ""): FormalTestConfirmation {
  return {
    confirmed_by: confirmedBy,
    design_confirmed: false,
    endpoints_confirmed: false,
    deidentified_confirmed: false,
    missing_data_reviewed: false,
    assumptions_reviewed: false,
    multiplicity_reviewed: false,
    notes: "",
  };
}

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

type ChartStyleId = "journalBlue" | "mono" | "highContrast";

const chartStyles: Record<
  ChartStyleId,
  {
    label: string;
    titleColor: string;
    textColor: string;
    mutedColor: string;
    barColor: string;
    trackColor: string;
    backgroundColor: string;
    borderColor: string;
  }
> = {
  journalBlue: {
    label: "期刊蓝",
    titleColor: "#243040",
    textColor: "#4f6074",
    mutedColor: "#667085",
    barColor: "#2f7197",
    trackColor: "#e5e7eb",
    backgroundColor: "#ffffff",
    borderColor: "#cbd5e1",
  },
  mono: {
    label: "单色",
    titleColor: "#111827",
    textColor: "#374151",
    mutedColor: "#6b7280",
    barColor: "#111827",
    trackColor: "#e5e7eb",
    backgroundColor: "#ffffff",
    borderColor: "#9ca3af",
  },
  highContrast: {
    label: "高对比",
    titleColor: "#111827",
    textColor: "#1f2937",
    mutedColor: "#4b5563",
    barColor: "#b91c1c",
    trackColor: "#f3f4f6",
    backgroundColor: "#ffffff",
    borderColor: "#111827",
  },
};

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

function formatChartValue(value: number): string {
  return new Intl.NumberFormat("zh-CN", {
    maximumFractionDigits: 2,
  }).format(value);
}

function formatPValue(value?: number | null): string {
  if (value === undefined || value === null) {
    return "未计算";
  }
  if (value < 0.001) {
    return "<0.001";
  }
  return value.toFixed(4);
}

function escapeSvgText(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function sanitizeFileName(value: string): string {
  return value.replace(/[<>:"/\\|?*\x00-\x1F]/g, "-").replace(/\s+/g, "-").slice(0, 80) || "chart";
}

function wrapText(value: string, lineLength: number): string[] {
  const chunks: string[] = [];
  let remaining = value.trim();
  while (remaining.length > lineLength) {
    chunks.push(remaining.slice(0, lineLength));
    remaining = remaining.slice(lineLength);
  }
  if (remaining) {
    chunks.push(remaining);
  }
  return chunks;
}

function buildChartSvg(chart: ChartSpec, chartStyle: ChartStyleId): string {
  const style = chartStyles[chartStyle];
  const width = 960;
  const rowHeight = 52;
  const plotTop = 126;
  const barX = 228;
  const barWidth = 500;
  const valueX = 752;
  const narrativeLines = wrapText(chart.narrative, 58);
  const height = Math.max(340, plotTop + chart.points.length * rowHeight + 98 + narrativeLines.length * 22);
  const maxValue = Math.max(...chart.points.map((point) => Math.abs(point.value)), 1);
  const escapedTitle = escapeSvgText(chart.title);
  const escapedSubtitle = escapeSvgText(`${chart.x_label} · ${chart.y_label}`);

  const rows = chart.points
    .map((point, index) => {
      const y = plotTop + index * rowHeight;
      const fillWidth = Math.max(Math.abs(point.value) / maxValue * barWidth, 2);
      const valueText = `${formatChartValue(point.value)}${point.note ? ` · ${point.note}` : ""}`;
      return `
  <g>
    <text x="40" y="${y + 17}" font-size="17" fill="${style.titleColor}">${escapeSvgText(point.label)}</text>
    <rect x="${barX}" y="${y}" width="${barWidth}" height="20" rx="4" fill="${style.trackColor}"/>
    <rect x="${barX}" y="${y}" width="${fillWidth}" height="20" rx="4" fill="${style.barColor}"/>
    <text x="${valueX}" y="${y + 17}" font-size="16" fill="${style.textColor}">${escapeSvgText(valueText)}</text>
  </g>`;
    })
    .join("");

  const narrativeY = plotTop + chart.points.length * rowHeight + 50;
  const narrative = narrativeLines
    .map(
      (line, index) =>
        `<text x="40" y="${narrativeY + index * 22}" font-size="16" fill="${style.textColor}">${escapeSvgText(line)}</text>`,
    )
    .join("\n  ");

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="title desc">
  <title id="title">${escapedTitle}</title>
  <desc id="desc">${escapeSvgText(chart.narrative)}</desc>
  <rect width="100%" height="100%" fill="${style.backgroundColor}"/>
  <text x="40" y="50" font-family="Arial, 'Microsoft YaHei', sans-serif" font-size="28" font-weight="700" fill="${style.titleColor}">${escapedTitle}</text>
  <text x="40" y="82" font-family="Arial, 'Microsoft YaHei', sans-serif" font-size="17" fill="${style.textColor}">${escapedSubtitle}</text>
  <line x1="${barX}" y1="104" x2="${barX + barWidth}" y2="104" stroke="${style.borderColor}" stroke-width="1"/>
  <text x="${barX}" y="96" font-family="Arial, 'Microsoft YaHei', sans-serif" font-size="14" fill="${style.mutedColor}">${escapeSvgText(chart.y_label)}</text>
  <text x="40" y="96" font-family="Arial, 'Microsoft YaHei', sans-serif" font-size="14" fill="${style.mutedColor}">${escapeSvgText(chart.x_label)}</text>
  <g font-family="Arial, 'Microsoft YaHei', sans-serif">
${rows}
  </g>
  <text x="40" y="${narrativeY - 26}" font-family="Arial, 'Microsoft YaHei', sans-serif" font-size="16" font-weight="700" fill="${style.titleColor}">图表说明</text>
  ${narrative}
</svg>
`;
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
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [projectAccess, setProjectAccess] = useState<ProjectAccessPolicy | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<AgentId>("study_planner");
  const [selectedProjectId, setSelectedProjectId] = useState<string>("project-a");
  const [protocol, setProtocol] = useState<ProjectProtocol | null>(null);
  const [planDrafts, setPlanDrafts] = useState<ProjectPlanDraft[]>([]);
  const [selectedPlanDraftId, setSelectedPlanDraftId] = useState<number | null>(null);
  const [reminderSummary, setReminderSummary] = useState<ProjectReminderSummary | null>(null);
  const [dataRequirementSpec, setDataRequirementSpec] = useState<DataRequirementSpec | null>(null);
  const [analysisRecords, setAnalysisRecords] = useState<DataAnalysisRecord[]>([]);
  const [dataAuditLogs, setDataAuditLogs] = useState<DataAuditLog[]>([]);
  const [qualityReport, setQualityReport] = useState<DataQualityReport | null>(null);
  const [statisticsReport, setStatisticsReport] = useState<DataStatisticsReport | null>(null);
  const [uploadedCsvFile, setUploadedCsvFile] = useState<File | null>(null);
  const [selectedGroupColumn, setSelectedGroupColumn] = useState("");
  const [selectedOutcomeColumns, setSelectedOutcomeColumns] = useState<string[]>([]);
  const [selectedChartStyle, setSelectedChartStyle] = useState<ChartStyleId>("journalBlue");
  const [formalTestConfirmation, setFormalTestConfirmation] = useState<FormalTestConfirmation>(
    createFormalTestConfirmation(),
  );
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("请帮我制定实验方案");
  const [isLoading, setIsLoading] = useState(true);
  const [isProtocolLoading, setIsProtocolLoading] = useState(false);
  const [isProtocolSaving, setIsProtocolSaving] = useState(false);
  const [isPlanGenerating, setIsPlanGenerating] = useState(false);
  const [isPlanDraftLoading, setIsPlanDraftLoading] = useState(false);
  const [isPlanDraftApplying, setIsPlanDraftApplying] = useState(false);
  const [isReminderLoading, setIsReminderLoading] = useState(false);
  const [isDataLoading, setIsDataLoading] = useState(false);
  const [isAnalysisRecordLoading, setIsAnalysisRecordLoading] = useState(false);
  const [isAnalysisRecordSaving, setIsAnalysisRecordSaving] = useState(false);
  const [isDataAuditLogLoading, setIsDataAuditLogLoading] = useState(false);
  const [isCsvUploading, setIsCsvUploading] = useState(false);
  const [isStatisticsLoading, setIsStatisticsLoading] = useState(false);
  const [isFormalTestLoading, setIsFormalTestLoading] = useState(false);
  const [isWriterDrafting, setIsWriterDrafting] = useState(false);
  const [showAllTasks, setShowAllTasks] = useState(false);
  const [showAllDraftTasks, setShowAllDraftTasks] = useState(false);
  const [showAllDataRequirements, setShowAllDataRequirements] = useState(false);
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

  const shouldShowProtocolWorkspace = selectedAgentId === "study_planner";
  const shouldShowDataWorkspace = selectedAgentId === "data_analyst";

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

  const visibleDataRequirements = useMemo(() => {
    if (!dataRequirementSpec) {
      return [];
    }
    return showAllDataRequirements
      ? dataRequirementSpec.items
      : dataRequirementSpec.items.slice(0, 6);
  }, [dataRequirementSpec, showAllDataRequirements]);

  const numericColumnOptions = useMemo(() => {
    return qualityReport?.columns.filter((column) => column.inferred_type === "numeric") ?? [];
  }, [qualityReport]);

  const groupColumnOptions = useMemo(() => {
    return (
      qualityReport?.columns.filter(
        (column) =>
          column.unique_count > 1 &&
          column.unique_count <= 12 &&
          column.missing_percent < 100 &&
          column.inferred_type !== "empty",
      ) ?? []
    );
  }, [qualityReport]);

  const privacyReport = qualityReport?.privacy_report ?? null;
  const hasBlockingPrivacyRisk = privacyReport?.risk_level === "red";
  const canEditSelectedProject = projectAccess?.can_edit ?? true;
  const formalTestReport = statisticsReport?.formal_test_report ?? null;
  const isFormalTestReady = useMemo(() => {
    return (
      formalTestConfirmation.confirmed_by.trim().length > 0 &&
      formalTestConfirmationItems.every((item) => formalTestConfirmation[item.key])
    );
  }, [formalTestConfirmation]);

  useEffect(() => {
    loadWorkspace();
  }, []);

  useEffect(() => {
    setShowAllTasks(false);
    setShowAllDraftTasks(false);
    setShowAllDataRequirements(false);
    setProjectAccess(null);
    setQualityReport(null);
    setStatisticsReport(null);
    setDataAuditLogs([]);
    setUploadedCsvFile(null);
    setSelectedGroupColumn("");
    setSelectedOutcomeColumns([]);
    setFormalTestConfirmation(createFormalTestConfirmation(currentUser?.display_name ?? ""));
    setOpenProtocolSections({
      core: true,
      criteria: false,
      analysis: false,
      submission: false,
    });
  }, [selectedProjectId]);

  useEffect(() => {
    if (currentUser && !formalTestConfirmation.confirmed_by.trim()) {
      setFormalTestConfirmation((current) => ({
        ...current,
        confirmed_by: currentUser.display_name,
      }));
    }
  }, [currentUser, formalTestConfirmation.confirmed_by]);

  useEffect(() => {
    let isCurrent = true;

    async function loadProjectAccess() {
      if (!selectedProjectId) {
        setProjectAccess(null);
        return;
      }

      try {
        const access = await getProjectAccess(selectedProjectId);
        if (isCurrent) {
          setProjectAccess(access);
        }
      } catch (caughtError) {
        if (isCurrent) {
          setProjectAccess(null);
          setError(caughtError instanceof Error ? caughtError.message : "项目权限读取失败。");
        }
      }
    }

    loadProjectAccess();

    return () => {
      isCurrent = false;
    };
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

  useEffect(() => {
    let isCurrent = true;

    async function loadDataRequirements() {
      if (!selectedProjectId) {
        setDataRequirementSpec(null);
        return;
      }

      setIsDataLoading(true);
      setError(null);

      try {
        const requirementData = await getDataRequirements(selectedProjectId);
        if (isCurrent) {
          setDataRequirementSpec(requirementData);
        }
      } catch (caughtError) {
        if (isCurrent) {
          setError(caughtError instanceof Error ? caughtError.message : "数据需求读取失败。");
          setDataRequirementSpec(null);
        }
      } finally {
        if (isCurrent) {
          setIsDataLoading(false);
        }
      }
    }

    loadDataRequirements();

    return () => {
      isCurrent = false;
    };
  }, [selectedProjectId]);

  useEffect(() => {
    let isCurrent = true;

    async function loadAnalysisRecords() {
      if (!selectedProjectId) {
        setAnalysisRecords([]);
        return;
      }

      setIsAnalysisRecordLoading(true);
      setError(null);

      try {
        const records = await getDataAnalysisRecords(selectedProjectId);
        if (isCurrent) {
          setAnalysisRecords(records);
        }
      } catch (caughtError) {
        if (isCurrent) {
          setError(caughtError instanceof Error ? caughtError.message : "分析记录读取失败。");
          setAnalysisRecords([]);
        }
      } finally {
        if (isCurrent) {
          setIsAnalysisRecordLoading(false);
        }
      }
    }

    loadAnalysisRecords();

    return () => {
      isCurrent = false;
    };
  }, [selectedProjectId]);

  useEffect(() => {
    let isCurrent = true;

    async function loadAuditLogs() {
      if (!selectedProjectId) {
        setDataAuditLogs([]);
        return;
      }

      setIsDataAuditLogLoading(true);

      try {
        const logs = await getDataAuditLogs(selectedProjectId);
        if (isCurrent) {
          setDataAuditLogs(logs);
        }
      } catch (caughtError) {
        if (isCurrent) {
          setError(caughtError instanceof Error ? caughtError.message : "审计日志读取失败。");
          setDataAuditLogs([]);
        }
      } finally {
        if (isCurrent) {
          setIsDataAuditLogLoading(false);
        }
      }
    }

    loadAuditLogs();

    return () => {
      isCurrent = false;
    };
  }, [selectedProjectId]);

  async function loadWorkspace() {
    setIsLoading(true);
    setError(null);

    try {
      const [dashboardData, projectData, agentData, userData] = await Promise.all([
        getDashboard(),
        getProjects(),
        getAgents(),
        getCurrentUser(),
      ]);
      setDashboard(dashboardData);
      setProjects(projectData);
      setAgents(agentData);
      setCurrentUser(userData);
      if (projectData.length && !projectData.some((project) => project.id === selectedProjectId)) {
        setSelectedProjectId(projectData[0].id);
      }
      if (!projectData.length) {
        setSelectedProjectId("");
      }
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "前端无法连接后端服务。");
    } finally {
      setIsLoading(false);
    }
  }

  async function refreshDataRequirements(projectId: string) {
    const requirementData = await getDataRequirements(projectId);
    setDataRequirementSpec(requirementData);
  }

  async function refreshDataAuditLogs(projectId = selectedProjectId) {
    if (!projectId) {
      return;
    }

    try {
      const logs = await getDataAuditLogs(projectId);
      setDataAuditLogs(logs);
    } catch {
      // Audit refresh should not interrupt the main data workflow.
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
    if (!canEditSelectedProject) {
      return;
    }

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
    if (!selectedProjectId || isReminderLoading || !canEditSelectedProject) {
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
    if (!selectedProjectId || dismissingReminderId !== null || !canEditSelectedProject) {
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
    if (!selectedProjectId || !canEditSelectedProject) {
      return;
    }

    setIsProtocolSaving(true);
    setError(null);

    try {
      const protocolData = await draftProjectProtocol(selectedProjectId);
      setProtocol(protocolData);
      await refreshDataRequirements(selectedProjectId);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "研究方案草案生成失败。");
    } finally {
      setIsProtocolSaving(false);
    }
  }

  async function handleSaveProtocol() {
    if (!selectedProjectId || !protocol || !canEditSelectedProject) {
      return;
    }

    setIsProtocolSaving(true);
    setError(null);

    try {
      const savedProtocol = await saveProjectProtocol(selectedProjectId, toProtocolUpdate(protocol));
      setProtocol(savedProtocol);
      await refreshDataRequirements(selectedProjectId);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "研究方案保存失败。");
    } finally {
      setIsProtocolSaving(false);
    }
  }

  async function handleExtractProtocolFromMessage(message: ChatMessage) {
    const targetProjectId = message.projectId ?? selectedProjectId;
    if (!targetProjectId || extractingMessageId || !canEditSelectedProject) {
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
      await refreshDataRequirements(targetProjectId);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "研究方案写入失败。");
    } finally {
      setExtractingMessageId(null);
    }
  }

  async function handleGeneratePlanFromProtocol() {
    if (!selectedProjectId || isPlanGenerating || !canEditSelectedProject) {
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
    if (!selectedProjectId || isPlanDraftApplying || !canEditSelectedProject) {
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

  async function handleCsvUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file || !selectedProjectId || isCsvUploading || !canEditSelectedProject) {
      return;
    }

    setIsCsvUploading(true);
    setError(null);

    try {
      const report = await uploadDataQualityReport(selectedProjectId, file);
      const numericDefaults = report.columns
        .filter((column) => column.inferred_type === "numeric")
        .map((column) => column.name)
        .slice(0, 2);
      const groupDefault =
        report.columns.find(
          (column) =>
            column.unique_count > 1 &&
            column.unique_count <= 12 &&
            column.missing_percent < 100 &&
            column.inferred_type !== "empty" &&
            column.inferred_type !== "numeric",
        )?.name ?? "";

      setUploadedCsvFile(file);
      setQualityReport(report);
      setStatisticsReport(null);
      setSelectedOutcomeColumns(numericDefaults);
      setSelectedGroupColumn(groupDefault);
      setFormalTestConfirmation(createFormalTestConfirmation(currentUser?.display_name ?? ""));
      setSelectedAgentId("data_analyst");
      await refreshDataAuditLogs(selectedProjectId);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "CSV 质量检查失败。");
    } finally {
      setIsCsvUploading(false);
    }
  }

  function handleOutcomeColumnToggle(columnName: string) {
    setSelectedOutcomeColumns((current) => {
      if (current.includes(columnName)) {
        return current.filter((name) => name !== columnName);
      }
      return [...current, columnName].slice(0, 6);
    });
    setStatisticsReport(null);
    setFormalTestConfirmation(createFormalTestConfirmation(currentUser?.display_name ?? ""));
  }

  async function handleGenerateStatisticsReport() {
    if (!selectedProjectId || !uploadedCsvFile || isStatisticsLoading || !canEditSelectedProject) {
      return;
    }

    setIsStatisticsLoading(true);
    setError(null);

    try {
      const report = await uploadDataStatisticsReport(
        selectedProjectId,
        uploadedCsvFile,
        selectedGroupColumn,
        selectedOutcomeColumns,
      );
      setStatisticsReport(report);
      setFormalTestConfirmation(createFormalTestConfirmation(currentUser?.display_name ?? ""));
      setSelectedAgentId("data_analyst");
      await refreshDataAuditLogs(selectedProjectId);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "统计草案生成失败。");
    } finally {
      setIsStatisticsLoading(false);
    }
  }

  function handleFormalTestConfirmationToggle(key: FormalTestConfirmationKey) {
    setFormalTestConfirmation((current) => ({
      ...current,
      [key]: !current[key],
    }));
  }

  async function handleExecuteFormalTests() {
    if (
      !selectedProjectId ||
      !uploadedCsvFile ||
      !statisticsReport ||
      isFormalTestLoading ||
      !canEditSelectedProject
    ) {
      return;
    }

    const formalGroupColumn = statisticsReport.group_column;
    if (!formalGroupColumn) {
      setError("正式检验前请先选择分组列，并重新生成统计草案。");
      return;
    }

    if (!isFormalTestReady) {
      setError("请先填写确认人，并完成所有正式检验确认项。");
      return;
    }

    setIsFormalTestLoading(true);
    setError(null);

    try {
      const report = await uploadFormalTestReport(
        selectedProjectId,
        uploadedCsvFile,
        formalGroupColumn,
        statisticsReport.numeric_summaries.map((summary) => summary.column),
        formalTestConfirmation,
      );
      setStatisticsReport((current) =>
        current
          ? {
              ...current,
              formal_test_report: report,
              next_step: report.next_step,
            }
          : current,
      );
      await refreshDataAuditLogs(selectedProjectId);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "正式检验执行失败。");
    } finally {
      setIsFormalTestLoading(false);
    }
  }

  function buildWriterHandoffMessage(): string {
    if (!selectedProject || !qualityReport || !statisticsReport) {
      return "";
    }

    const numericSummaryText = statisticsReport.numeric_summaries
      .slice(0, 6)
      .map(
        (summary) =>
          `- ${summary.column}: n=${summary.n}, mean=${summary.mean}, SD=${summary.std_dev}, median=${summary.median}, range=${summary.min}-${summary.max}`,
      )
      .join("\n");
    const groupSummaryText = statisticsReport.group_comparisons
      .slice(0, 4)
      .map((comparison) => `- ${comparison.interpretation}`)
      .join("\n");
    const chartSummaryText = statisticsReport.chart_specs
      .slice(0, 4)
      .map((chart) => `- ${chart.title}: ${chart.narrative}`)
      .join("\n");
    const formalTestText = statisticsReport.formal_test_report?.results
      .map((result) => `- ${result.outcome_column}: ${result.interpretation}`)
      .join("\n");

    return [
      "请基于以下 Dr. Data Lin 的 CSV 质控、描述性统计和图表摘要，撰写一版 SCI 论文 Results 段落草稿。",
      "要求：使用简体中文；不要编造 P 值、置信区间或未提供的数据；只有下方正式检验结果中已经给出的 P 值可以引用，未执行的检验请列为待补充。",
      "",
      `项目：${selectedProject.name} - ${selectedProject.title}`,
      `研究主题：${selectedProject.topic}`,
      "",
      "数据质控摘要：",
      `- 文件：${qualityReport.file_name}`,
      `- 行数/列数：${qualityReport.row_count} 行，${qualityReport.column_count} 列`,
      `- 字段匹配：${qualityReport.matched_required_fields.length} 个必需字段已匹配`,
      `- 缺少字段：${qualityReport.missing_required_fields.join("、") || "暂无"}`,
      `- 质控问题数：${qualityReport.issues.length}`,
      `- 脱敏检查：${qualityReport.privacy_report?.summary ?? "未生成隐私检查摘要"}`,
      "",
      "方法草案：",
      statisticsReport.methods_draft,
      "",
      "结果草案：",
      statisticsReport.results_draft,
      "",
      "数值摘要：",
      numericSummaryText || "- 暂无",
      "",
      "分组描述：",
      groupSummaryText || "- 未指定分组或可用分组不足",
      "",
      "图表摘要：",
      chartSummaryText || "- 暂无",
      "",
      "正式检验结果：",
      formalTestText || "- 尚未执行正式检验；请不要编造 P 值。",
      "",
      "请输出：1）Results 段落草稿；2）需要回到数据表补充或正式检验的项目清单。",
    ].join("\n");
  }

  async function handleSendAnalysisToWriter() {
    if (!selectedProjectId || !qualityReport || !statisticsReport || isWriterDrafting) {
      return;
    }

    const handoffMessage = buildWriterHandoffMessage();
    if (!handoffMessage) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      speaker: "user",
      agentId: "writer",
      projectId: selectedProjectId,
      content: "请根据 Dr. Data Lin 的质控、统计和图表摘要生成 Results 段落草稿。",
    };

    setSelectedAgentId("writer");
    setMessages((current) => [...current, userMessage]);
    setIsWriterDrafting(true);
    setError(null);

    try {
      const response = await sendChat({
        agent_id: "writer",
        project_id: selectedProjectId,
        message: handoffMessage,
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
      setError(caughtError instanceof Error ? caughtError.message : "结果段落草稿生成失败。");
    } finally {
      setIsWriterDrafting(false);
    }
  }

  async function handleSaveAnalysisRecord() {
    if (!selectedProjectId || !qualityReport || isAnalysisRecordSaving || !canEditSelectedProject) {
      return;
    }

    setIsAnalysisRecordSaving(true);
    setError(null);

    try {
      const savedRecord = await saveDataAnalysisRecord(selectedProjectId, {
        file_name: qualityReport.file_name,
        quality_report: qualityReport,
        statistics_report: statisticsReport,
      });
      setAnalysisRecords((current) => [
        savedRecord,
        ...current.filter((record) => record.id !== savedRecord.id),
      ]);
      await refreshDataAuditLogs(selectedProjectId);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "分析记录保存失败。");
    } finally {
      setIsAnalysisRecordSaving(false);
    }
  }

  function handleRestoreAnalysisRecord(record: DataAnalysisRecord) {
    setQualityReport(record.quality_report);
    setStatisticsReport(record.statistics_report ?? null);
    setUploadedCsvFile(null);
    setSelectedGroupColumn(record.statistics_report?.group_column ?? "");
    setSelectedOutcomeColumns(
      record.statistics_report?.numeric_summaries.map((summary) => summary.column).slice(0, 6) ?? [],
    );
    setFormalTestConfirmation(
      record.statistics_report?.formal_test_report?.confirmation ??
        createFormalTestConfirmation(currentUser?.display_name ?? ""),
    );
    setSelectedAgentId("data_analyst");
  }

  function handleDownloadChartSvg(chart: ChartSpec) {
    const svg = buildChartSvg(chart, selectedChartStyle);
    const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    try {
      link.href = url;
      link.download = `${sanitizeFileName(chart.title)}.svg`;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  async function handleDownloadChartPng(chart: ChartSpec) {
    const svg = buildChartSvg(chart, selectedChartStyle);
    const svgBlob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const svgUrl = URL.createObjectURL(svgBlob);

    try {
      const image = new Image();
      const imageLoaded = new Promise<void>((resolve, reject) => {
        image.onload = () => resolve();
        image.onerror = () => reject(new Error("图表 PNG 导出失败。"));
      });
      image.src = svgUrl;
      await imageLoaded;

      const canvas = document.createElement("canvas");
      canvas.width = image.naturalWidth || 960;
      canvas.height = image.naturalHeight || 540;
      const context = canvas.getContext("2d");
      if (!context) {
        throw new Error("当前浏览器无法创建图表画布。");
      }
      context.fillStyle = "#ffffff";
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0);

      const pngBlob = await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob((blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error("图表 PNG 导出失败。"));
          }
        }, "image/png");
      });
      const pngUrl = URL.createObjectURL(pngBlob);
      const link = document.createElement("a");
      try {
        link.href = pngUrl;
        link.download = `${sanitizeFileName(chart.title)}.png`;
        document.body.appendChild(link);
        link.click();
        link.remove();
      } finally {
        URL.revokeObjectURL(pngUrl);
      }
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "图表 PNG 导出失败。");
    } finally {
      URL.revokeObjectURL(svgUrl);
    }
  }

  function handleOpenChartPdfView(chart: ChartSpec) {
    const svg = buildChartSvg(chart, selectedChartStyle);
    const inlineSvg = svg.replace(/^<\?xml[^>]*>\s*/, "");
    const printWindow = window.open("", "_blank");
    if (!printWindow) {
      setError("浏览器阻止了打印窗口，请允许弹窗后重试。");
      return;
    }

    printWindow.document.write(`<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>${escapeSvgText(chart.title)}</title>
    <style>
      body { margin: 0; background: #ffffff; }
      main { width: min(100%, 960px); margin: 0 auto; }
      svg { width: 100%; height: auto; display: block; }
      @page { margin: 14mm; }
      @media print { body { print-color-adjust: exact; -webkit-print-color-adjust: exact; } }
    </style>
  </head>
  <body>
    <main>${inlineSvg}</main>
    <script>
      window.addEventListener("load", () => {
        setTimeout(() => window.print(), 150);
      });
    </script>
  </body>
</html>`);
    printWindow.document.close();
  }

  function handleDownloadAnalysisParametersJson() {
    if (!qualityReport || !statisticsReport) {
      return;
    }

    const parameters = statisticsReport.analysis_parameters ?? {
      source_file_name: qualityReport.file_name,
      row_count: qualityReport.row_count,
      group_column: statisticsReport.group_column ?? null,
      outcome_columns: statisticsReport.numeric_summaries.map((summary) => summary.column),
      generated_chart_ids: statisticsReport.chart_specs.map((chart) => chart.id),
      quality_rule_version: "quality-v1",
      statistics_method_version: "descriptive-v1",
      chart_spec_version: "svg-bar-v1",
      raw_csv_saved: false,
    };
    const payload = {
      project_id: selectedProjectId,
      file_name: qualityReport.file_name,
      created_from: "Dr. Data Lin data workspace",
      parameters,
      quality_summary: {
        row_count: qualityReport.row_count,
        column_count: qualityReport.column_count,
        issue_count: qualityReport.issues.length,
        missing_required_fields: qualityReport.missing_required_fields,
      },
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${sanitizeFileName(qualityReport.file_name)}-analysis-parameters.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function handleDownloadReproducibleScript() {
    const scriptAsset = statisticsReport?.reproducible_script;
    if (!scriptAsset) {
      return;
    }

    const blob = new Blob([scriptAsset.script], {
      type: "text/x-python;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = scriptAsset.file_name || "reproducible-analysis.py";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Radiation Therapy SCI Workshop</p>
          <h1>我的研究书房</h1>
        </div>
        <div className="topbar-actions">
          <div className="user-access-chip">
            <ShieldCheck aria-hidden="true" size={16} />
            <div>
              <strong>{currentUser?.display_name ?? "演示用户"}</strong>
              <small>
                {currentUser?.role ?? "researcher"} ·{" "}
                {projectAccess
                  ? projectAccessLabels[projectAccess.access_level]
                  : selectedProjectId
                    ? "读取权限中"
                    : "无项目"}
              </small>
            </div>
          </div>
          <button className="icon-button" type="button" onClick={loadWorkspace} title="刷新工作台">
            <RefreshCw aria-hidden="true" size={18} />
          </button>
        </div>
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
                {!canEditSelectedProject ? (
                  <div className="access-readonly-banner">
                    <ShieldCheck aria-hidden="true" size={16} />
                    <span>当前项目为只读权限，可以查看方案、提醒和数据报告，但不能修改或上传数据。</span>
                  </div>
                ) : null}

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
                      disabled={isReminderLoading || !canEditSelectedProject}
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
                            disabled={dismissingReminderId === reminder.id || !canEditSelectedProject}
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
                          disabled={updatingTaskId === task.id || !canEditSelectedProject}
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

                {shouldShowProtocolWorkspace ? (
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
                        disabled={isProtocolLoading || isProtocolSaving || !canEditSelectedProject}
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
                          !protocolHasContent ||
                          !canEditSelectedProject
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
                        disabled={isProtocolLoading || isProtocolSaving || !protocol || !canEditSelectedProject}
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
                                         disabled={!canEditSelectedProject}
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
                          disabled={isPlanDraftApplying || !canEditSelectedProject}
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
                ) : null}

                {shouldShowDataWorkspace ? (
                <section className="data-panel" aria-label="Dr. Data Lin 数据工作区">
                  <div className="data-head">
                    <div>
                      <p className="eyebrow">Dr. Data Lin</p>
                      <h3>数据需求与 CSV 质控</h3>
                      <small>{dataRequirementSpec?.next_step ?? "先读取当前项目的数据需求。"}</small>
                    </div>
                    <BarChart3 aria-hidden="true" size={20} />
                  </div>

                  {isDataLoading ? (
                    <div className="protocol-loading compact">
                      <Loader2 aria-hidden="true" className="spin" size={18} />
                      <span>正在生成数据需求清单...</span>
                    </div>
                  ) : (
                    <>
                      <div className="data-requirement-meta">
                        <span>{dataRequirementSpec?.items.length ?? 0} 个字段需求</span>
                        <span>
                          {dataRequirementSpec?.generated_from_protocol ? "来自研究方案" : "默认模板"}
                        </span>
                      </div>

                      <div className="requirement-list">
                        {visibleDataRequirements.map((item) => (
                          <article className="requirement-item" key={item.id}>
                            <div>
                              <strong>{item.label}</strong>
                              <small>{item.rationale}</small>
                            </div>
                            <span>{item.required ? "必需" : "建议"}</span>
                          </article>
                        ))}
                      </div>

                      {(dataRequirementSpec?.items.length ?? 0) > 6 ? (
                        <button
                          className="panel-toggle compact"
                          type="button"
                          onClick={() => setShowAllDataRequirements((current) => !current)}
                        >
                          {showAllDataRequirements
                            ? "收起字段"
                            : `展开全部 ${dataRequirementSpec?.items.length ?? 0} 个字段`}
                        </button>
                      ) : null}
                    </>
                  )}

                  <div className="data-upload-row">
                    <label
                      className={`file-upload-button ${
                        isCsvUploading || !canEditSelectedProject ? "disabled" : ""
                      }`}
                    >
                      {isCsvUploading ? (
                        <Loader2 aria-hidden="true" className="spin" size={16} />
                      ) : (
                        <Upload aria-hidden="true" size={16} />
                      )}
                      <span>{isCsvUploading ? "检查中" : "上传 CSV"}</span>
                      <input
                        type="file"
                        accept=".csv,text/csv"
                        disabled={isCsvUploading || !canEditSelectedProject}
                        onChange={handleCsvUpload}
                      />
                    </label>
                  </div>

                  {qualityReport ? (
                    <div className="data-report">
                      <div className="data-report-head">
                        <div>
                          <h4>{qualityReport.file_name}</h4>
                          <small>{qualityReport.summary_for_writer}</small>
                        </div>
                      </div>

                      <div className="data-report-metrics">
                        <span>{qualityReport.row_count} 行</span>
                        <span>{qualityReport.column_count} 列</span>
                        <span>{qualityReport.matched_required_fields.length} 个字段匹配</span>
                        <span>{qualityReport.issues.length} 个问题</span>
                      </div>

                      {privacyReport ? (
                        <div className={`privacy-report-panel risk-${privacyReport.risk_level}`}>
                          <div className="privacy-report-head">
                            <div>
                              <strong>脱敏与隐私检查</strong>
                              <small>{privacyReport.summary}</small>
                            </div>
                            <span>{dataRiskLabels[privacyReport.risk_level]}</span>
                          </div>
                          <div className="privacy-report-metrics">
                            <span>规则 {privacyReport.policy_version}</span>
                            <span>扫描 {privacyReport.scanned_row_count} 行</span>
                            <span>{privacyReport.raw_data_saved ? "原始 CSV 已保存" : "原始 CSV 未保存"}</span>
                          </div>
                          {privacyReport.findings.length ? (
                            <div className="privacy-finding-list">
                              {privacyReport.findings.slice(0, 4).map((finding) => (
                                <article
                                  className="privacy-finding-item"
                                  key={`${finding.category}-${finding.column ?? "file"}-${finding.evidence}`}
                                >
                                  <span className={`status-badge risk-${finding.severity}`}>
                                    {dataRiskLabels[finding.severity]}
                                  </span>
                                  <div>
                                    <strong>{finding.column ?? "文件级风险"}</strong>
                                    <p>{finding.evidence}</p>
                                    <small>{finding.recommendation}</small>
                                  </div>
                                </article>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      ) : null}

                      {qualityReport.missing_required_fields.length ? (
                        <div className="data-warning-block">
                          <strong>缺少关键字段</strong>
                          <p>{qualityReport.missing_required_fields.slice(0, 6).join("、")}</p>
                        </div>
                      ) : (
                        <div className="data-ok-block">
                          <strong>关键字段覆盖良好</strong>
                          <p>当前 CSV 已覆盖数据需求清单中的必需字段。</p>
                        </div>
                      )}

                      {qualityReport.issues.length ? (
                        <div className="data-issue-list">
                          {qualityReport.issues.slice(0, 3).map((issue) => (
                            <article className="data-issue-item" key={`${issue.message}-${issue.column ?? "file"}`}>
                              <span className={`status-badge risk-${issue.severity}`}>
                                {riskLabels[issue.severity]}
                              </span>
                              <div>
                                <strong>{issue.column ?? "文件级问题"}</strong>
                                <p>{issue.message}</p>
                                <small>{issue.suggested_action}</small>
                              </div>
                            </article>
                          ))}
                        </div>
                      ) : null}

                      <div className="column-quality-list">
                        {qualityReport.columns.slice(0, 4).map((column) => (
                          <article className="column-quality-item" key={column.name}>
                            <div>
                              <strong>{column.name}</strong>
                              <small>
                                {column.inferred_type} · 缺失 {column.missing_percent}% · 唯一值{" "}
                                {column.unique_count}
                              </small>
                            </div>
                            {column.numeric_summary ? (
                              <span>
                                {column.numeric_summary.min} - {column.numeric_summary.max}
                              </span>
                            ) : (
                              <span>{column.sample_values[0] ?? "空列"}</span>
                            )}
                          </article>
                        ))}
                      </div>

                      <div className="statistics-panel">
                        <div className="statistics-head">
                          <div>
                            <p className="eyebrow">探索性统计</p>
                            <h4>描述性统计草案</h4>
                          </div>
                          <button
                            className="statistics-button"
                            type="button"
                            onClick={handleGenerateStatisticsReport}
                            disabled={
                              isStatisticsLoading ||
                              !uploadedCsvFile ||
                              numericColumnOptions.length === 0 ||
                              hasBlockingPrivacyRisk ||
                              !canEditSelectedProject
                            }
                          >
                            {isStatisticsLoading ? (
                              <Loader2 aria-hidden="true" className="spin" size={16} />
                            ) : (
                              <BarChart3 aria-hidden="true" size={16} />
                            )}
                            <span>生成统计草案</span>
                          </button>
                        </div>

                        <div className="statistics-controls">
                          <label>
                            <span>分组列</span>
                            <select
                              value={selectedGroupColumn}
                              disabled={!canEditSelectedProject}
                              onChange={(event) => {
                                setSelectedGroupColumn(event.target.value);
                                setStatisticsReport(null);
                                setFormalTestConfirmation(
                                  createFormalTestConfirmation(currentUser?.display_name ?? ""),
                                );
                              }}
                            >
                              <option value="">不分组</option>
                              {groupColumnOptions.map((column) => (
                                <option key={column.name} value={column.name}>
                                  {column.name}
                                </option>
                              ))}
                            </select>
                          </label>

                          <div className="outcome-picker">
                            <span>结局列</span>
                            <div>
                              {numericColumnOptions.length ? (
                                numericColumnOptions.slice(0, 8).map((column) => (
                                  <label key={column.name}>
                                    <input
                                      type="checkbox"
                                      checked={selectedOutcomeColumns.includes(column.name)}
                                      disabled={!canEditSelectedProject}
                                      onChange={() => handleOutcomeColumnToggle(column.name)}
                                    />
                                    <span>{column.name}</span>
                                  </label>
                                ))
                              ) : (
                                <small>当前 CSV 暂无可分析数值列。</small>
                              )}
                            </div>
                          </div>
                        </div>

                        {statisticsReport ? (
                          <div className="statistics-report">
                            <div className="statistics-copy-block">
                              <strong>方法草案</strong>
                              <p>{statisticsReport.methods_draft}</p>
                            </div>
                            <div className="statistics-copy-block">
                              <strong>结果草案</strong>
                              <p>{statisticsReport.results_draft}</p>
                            </div>

                            <div className="stat-summary-list">
                              {statisticsReport.numeric_summaries.slice(0, 4).map((summary) => (
                                <article className="stat-summary-item" key={summary.column}>
                                  <strong>{summary.column}</strong>
                                  <span>n={summary.n}</span>
                                  <span>均值 {summary.mean}</span>
                                  <span>SD {summary.std_dev}</span>
                                  <span>中位数 {summary.median}</span>
                                </article>
                              ))}
                            </div>

                            {(statisticsReport.distribution_checks?.length ||
                              statisticsReport.test_recommendations?.length) ? (
                              <div className="stat-guidance-panel">
                                <div className="stat-guidance-head">
                                  <div>
                                    <strong>正式统计边界</strong>
                                    <small>仅给出检验建议，不自动计算 P 值</small>
                                  </div>
                                  <span>{statisticsReport.test_recommendations?.length ?? 0} 项建议</span>
                                </div>

                                {statisticsReport.distribution_checks?.length ? (
                                  <div className="distribution-check-list">
                                    {statisticsReport.distribution_checks.slice(0, 4).map((check) => (
                                      <article className="distribution-check-item" key={check.column}>
                                        <div>
                                          <strong>{check.column}</strong>
                                          <span>{check.normality_signal}</span>
                                        </div>
                                        <p>{check.recommendation}</p>
                                        <small>
                                          n={check.n} · 缺失 {check.missing_count} · 偏态提示{" "}
                                          {check.skewness_hint ?? "NA"}
                                        </small>
                                      </article>
                                    ))}
                                  </div>
                                ) : null}

                                {statisticsReport.test_recommendations?.length ? (
                                  <div className="test-recommendation-list">
                                    {statisticsReport.test_recommendations.slice(0, 4).map((recommendation) => (
                                      <article
                                        className="test-recommendation-item"
                                        key={recommendation.outcome_column}
                                      >
                                        <div>
                                          <strong>{recommendation.outcome_column}</strong>
                                          <span>
                                            {recommendation.group_column
                                              ? `按 ${recommendation.group_column} 分组`
                                              : "未设置分组"}
                                          </span>
                                        </div>
                                        <p>{recommendation.candidate_tests.join(" / ")}</p>
                                        <small>{recommendation.p_value_boundary}</small>
                                      </article>
                                    ))}
                                  </div>
                                ) : null}
                              </div>
                            ) : null}

                            <div className="formal-test-panel">
                              <div className="formal-test-head">
                                <div>
                                  <p className="eyebrow">人工确认</p>
                                  <h4>正式假设检验</h4>
                                  <small>确认研究设计、脱敏和统计假设后才会计算 P 值。</small>
                                </div>
                                <span>{formalTestReport ? formalTestReport.method_version : "待确认"}</span>
                              </div>

                              <label className="formal-test-confirmed-by">
                                <span>确认人</span>
                                <input
                                  type="text"
                                  value={formalTestConfirmation.confirmed_by}
                                  disabled={!canEditSelectedProject}
                                  onChange={(event) =>
                                    setFormalTestConfirmation((current) => ({
                                      ...current,
                                      confirmed_by: event.target.value,
                                    }))
                                  }
                                  placeholder="填写执行前确认人"
                                />
                              </label>

                              <div className="formal-test-checklist">
                                {formalTestConfirmationItems.map((item) => (
                                  <label key={item.key}>
                                    <input
                                      type="checkbox"
                                      checked={formalTestConfirmation[item.key]}
                                      disabled={!canEditSelectedProject}
                                      onChange={() => handleFormalTestConfirmationToggle(item.key)}
                                    />
                                    <span>
                                      <strong>{item.label}</strong>
                                      <small>{item.detail}</small>
                                    </span>
                                  </label>
                                ))}
                              </div>

                              <label className="formal-test-notes">
                                <span>确认备注</span>
                                <textarea
                                  rows={3}
                                  value={formalTestConfirmation.notes}
                                  disabled={!canEditSelectedProject}
                                  onChange={(event) =>
                                    setFormalTestConfirmation((current) => ({
                                      ...current,
                                      notes: event.target.value,
                                    }))
                                  }
                                  placeholder="例如：两组独立样本，主要终点为计划剂量误差。"
                                />
                              </label>

                              <button
                                className="formal-test-button"
                                type="button"
                                onClick={handleExecuteFormalTests}
                                disabled={
                                  isFormalTestLoading ||
                                  !uploadedCsvFile ||
                                  !statisticsReport.group_column ||
                                  !isFormalTestReady ||
                                  hasBlockingPrivacyRisk ||
                                  !canEditSelectedProject
                                }
                              >
                                {isFormalTestLoading ? (
                                  <Loader2 aria-hidden="true" className="spin" size={16} />
                                ) : (
                                  <Activity aria-hidden="true" size={16} />
                                )}
                                <span>确认并执行正式检验</span>
                              </button>

                              {!uploadedCsvFile ? (
                                <p className="formal-test-note">
                                  恢复历史分析记录后，如需重新执行正式检验，需要重新上传同一份脱敏 CSV。
                                </p>
                              ) : null}
                              {!statisticsReport.group_column ? (
                                <p className="formal-test-note">
                                  正式检验需要先选择分组列，并重新生成统计草案。
                                </p>
                              ) : null}

                              {formalTestReport ? (
                                <div className="formal-test-results">
                                  <div className="formal-test-summary">
                                    <strong>{formalTestReport.audit_summary}</strong>
                                    <small>
                                      确认人：{formalTestReport.confirmation.confirmed_by} · 原始 CSV{" "}
                                      {formalTestReport.raw_csv_saved ? "已保存" : "未保存"}
                                    </small>
                                  </div>

                                  {formalTestReport.results.map((result) => (
                                    <article
                                      className={`formal-test-result status-${result.status}`}
                                      key={`${result.outcome_column}-${result.test_name}`}
                                    >
                                      <div>
                                        <strong>{result.outcome_column}</strong>
                                        <span>{result.test_name}</span>
                                      </div>
                                      <p>{result.interpretation}</p>
                                      <div className="formal-test-metrics">
                                        <span>P={formatPValue(result.p_value)}</span>
                                        <span>df={result.degrees_of_freedom?.toFixed(2) ?? "NA"}</span>
                                        <span>d={result.effect_size?.toFixed(2) ?? "NA"}</span>
                                        <span>{result.group_labels.join(" / ")}</span>
                                      </div>
                                      {result.warnings.length ? (
                                        <small>{result.warnings.join("；")}</small>
                                      ) : null}
                                    </article>
                                  ))}
                                </div>
                              ) : null}
                            </div>

                            {statisticsReport.group_comparisons.length ? (
                              <div className="group-comparison-list">
                                {statisticsReport.group_comparisons.slice(0, 2).map((comparison) => (
                                  <article
                                    className="group-comparison-item"
                                    key={`${comparison.group_column}-${comparison.column}`}
                                  >
                                    <strong>{comparison.column}</strong>
                                    <p>{comparison.interpretation}</p>
                                  </article>
                                ))}
                              </div>
                            ) : null}

                            {statisticsReport.chart_specs.length ? (
                              <div className="chart-export-toolbar">
                                <label>
                                  <span>图表样式</span>
                                  <select
                                    value={selectedChartStyle}
                                    onChange={(event) =>
                                      setSelectedChartStyle(event.target.value as ChartStyleId)
                                    }
                                  >
                                    {Object.entries(chartStyles).map(([styleId, style]) => (
                                      <option key={styleId} value={styleId}>
                                        {style.label}
                                      </option>
                                    ))}
                                  </select>
                                </label>
                              </div>
                            ) : null}

                            {statisticsReport.chart_specs.length ? (
                              <div className="chart-preview-list">
                                {statisticsReport.chart_specs.map((chart) => {
                                  const maxValue = Math.max(
                                    ...chart.points.map((point) => Math.abs(point.value)),
                                    1,
                                  );

                                  return (
                                    <article className="chart-preview-card" key={chart.id}>
                                      <div className="chart-preview-head">
                                        <div>
                                          <strong>{chart.title}</strong>
                                          <small>
                                            {chart.x_label} · {chart.y_label}
                                          </small>
                                        </div>
                                        <div className="chart-preview-actions">
                                          <span>{chart.chart_type === "histogram" ? "分布" : "条形"}</span>
                                          <button
                                            type="button"
                                            onClick={() => handleDownloadChartSvg(chart)}
                                            title="导出 SVG"
                                          >
                                            <Download aria-hidden="true" size={14} />
                                            <span>SVG</span>
                                          </button>
                                          <button
                                            type="button"
                                            onClick={() => handleDownloadChartPng(chart)}
                                            title="导出 PNG"
                                          >
                                            <Download aria-hidden="true" size={14} />
                                            <span>PNG</span>
                                          </button>
                                          <button
                                            type="button"
                                            onClick={() => handleOpenChartPdfView(chart)}
                                            title="打开打印视图，可另存为 PDF"
                                          >
                                            <FileText aria-hidden="true" size={14} />
                                            <span>PDF</span>
                                          </button>
                                        </div>
                                      </div>

                                      <div className="chart-bars" role="img" aria-label={chart.title}>
                                        {chart.points.map((point) => (
                                          <div className="chart-bar-row" key={`${chart.id}-${point.label}`}>
                                            <span className="chart-bar-label">{point.label}</span>
                                            <div
                                              className="chart-bar-track"
                                              style={{
                                                background: chartStyles[selectedChartStyle].trackColor,
                                              }}
                                            >
                                              <span
                                                className="chart-bar-fill"
                                                style={{
                                                  width: `${Math.max(
                                                    Math.abs(point.value) / maxValue * 100,
                                                    4,
                                                  )}%`,
                                                  background: chartStyles[selectedChartStyle].barColor,
                                                }}
                                              />
                                            </div>
                                            <span className="chart-bar-value">
                                              {formatChartValue(point.value)}
                                              {point.note ? ` · ${point.note}` : ""}
                                            </span>
                                          </div>
                                        ))}
                                      </div>

                                      <p>{chart.narrative}</p>
                                    </article>
                                  );
                                })}
                              </div>
                            ) : null}

                            <div className="analysis-parameters-panel">
                              <div className="analysis-parameters-head">
                                <div>
                                  <strong>可复现参数</strong>
                                  <small>
                                    {statisticsReport.analysis_parameters?.source_file_name ??
                                      qualityReport.file_name}
                                  </small>
                                </div>
                                <button
                                  type="button"
                                  onClick={handleDownloadAnalysisParametersJson}
                                  title="导出参数 JSON"
                                >
                                  <Download aria-hidden="true" size={14} />
                                  <span>JSON</span>
                                </button>
                              </div>
                              <div className="analysis-parameter-grid">
                                <span>
                                  分组：
                                  {statisticsReport.analysis_parameters?.group_column ??
                                    statisticsReport.group_column ??
                                    "不分组"}
                                </span>
                                <span>
                                  结局：
                                  {(
                                    statisticsReport.analysis_parameters?.outcome_columns ??
                                    statisticsReport.numeric_summaries.map((summary) => summary.column)
                                  ).join("、")}
                                </span>
                                <span>
                                  统计：
                                  {statisticsReport.analysis_parameters?.statistics_method_version ??
                                    "descriptive-v1"}
                                </span>
                                <span>
                                  图表：
                                  {statisticsReport.analysis_parameters?.chart_spec_version ?? "svg-bar-v1"}
                                </span>
                                <span>
                                  原始 CSV：
                                  {statisticsReport.analysis_parameters?.raw_csv_saved ? "已保存" : "未保存"}
                                </span>
                              </div>
                            </div>

                            {statisticsReport.reproducible_script ? (
                              <div className="repro-script-panel">
                                <div className="repro-script-head">
                                  <div>
                                    <strong>可复现实验脚本</strong>
                                    <small>{statisticsReport.reproducible_script.file_name}</small>
                                  </div>
                                  <button
                                    type="button"
                                    onClick={handleDownloadReproducibleScript}
                                    title="下载 Python 脚本"
                                  >
                                    <Download aria-hidden="true" size={14} />
                                    <span>PY</span>
                                  </button>
                                </div>
                                <div className="repro-script-meta">
                                  <span>{statisticsReport.reproducible_script.language}</span>
                                  <span>
                                    输入：{statisticsReport.reproducible_script.input_file_placeholder}
                                  </span>
                                  <span>不计算 P 值</span>
                                </div>
                                <pre>
                                  {statisticsReport.reproducible_script.script
                                    .split("\n")
                                    .slice(0, 10)
                                    .join("\n")}
                                </pre>
                              </div>
                            ) : null}

                            <button
                              className="writer-handoff-button"
                              type="button"
                              onClick={handleSendAnalysisToWriter}
                              disabled={isWriterDrafting}
                            >
                              {isWriterDrafting ? (
                                <Loader2 aria-hidden="true" className="spin" size={16} />
                              ) : (
                                <FileText aria-hidden="true" size={16} />
                              )}
                              <span>交给 Alex Writer</span>
                            </button>

                            <button
                              className="analysis-record-button"
                              type="button"
                              onClick={handleSaveAnalysisRecord}
                              disabled={isAnalysisRecordSaving || !canEditSelectedProject}
                            >
                              {isAnalysisRecordSaving ? (
                                <Loader2 aria-hidden="true" className="spin" size={16} />
                              ) : (
                                <Save aria-hidden="true" size={16} />
                              )}
                              <span>保存分析记录</span>
                            </button>

                            <p className="data-empty">{statisticsReport.next_step}</p>
                          </div>
                        ) : null}
                      </div>
                    </div>
                  ) : (
                    <p className="data-empty">上传脱敏 CSV 后，这里会显示字段覆盖、缺失率、数值范围和写作摘要。</p>
                  )}

                  <div className="analysis-records-panel">
                    <div className="analysis-records-head">
                      <div>
                        <p className="eyebrow">分析记录</p>
                        <h4>已保存报告</h4>
                      </div>
                      <span>{analysisRecords.length} 条</span>
                    </div>

                    {isAnalysisRecordLoading ? (
                      <div className="protocol-loading compact">
                        <Loader2 aria-hidden="true" className="spin" size={18} />
                        <span>正在读取分析记录...</span>
                      </div>
                    ) : analysisRecords.length ? (
                      <div className="analysis-record-list">
                        {analysisRecords.slice(0, 3).map((record) => (
                          <article className="analysis-record-item" key={record.id}>
                            <div>
                              <strong>{record.file_name}</strong>
                              <small>
                                {formatDateTime(record.created_at)} · {record.row_count} 行 ·{" "}
                                {record.issue_count} 个问题 · {record.chart_count} 张图
                              </small>
                            </div>
                            <button type="button" onClick={() => handleRestoreAnalysisRecord(record)}>
                              恢复
                            </button>
                          </article>
                        ))}
                      </div>
                    ) : (
                      <p className="data-empty">还没有保存的分析记录。</p>
                    )}
                  </div>

                  <div className="data-audit-panel">
                    <div className="data-audit-head">
                      <div>
                        <p className="eyebrow">脱敏审计</p>
                        <h4>数据操作日志</h4>
                      </div>
                      <span>{dataAuditLogs.length} 条</span>
                    </div>

                    {isDataAuditLogLoading ? (
                      <div className="protocol-loading compact">
                        <Loader2 aria-hidden="true" className="spin" size={18} />
                        <span>正在读取审计日志...</span>
                      </div>
                    ) : dataAuditLogs.length ? (
                      <div className="data-audit-list">
                        {dataAuditLogs.slice(0, 5).map((log) => (
                          <article className="data-audit-item" key={log.id}>
                            <span className={`status-badge risk-${log.risk_level}`}>
                              {dataRiskLabels[log.risk_level]}
                            </span>
                            <div>
                              <strong>{dataAuditActionLabels[log.action] ?? log.action}</strong>
                              <small>
                                {formatDateTime(log.created_at)}
                                {log.file_name ? ` · ${log.file_name}` : ""}
                                {log.raw_data_saved ? " · 原始 CSV 已保存" : " · 未保存原始 CSV"}
                              </small>
                              <p>{log.summary}</p>
                            </div>
                          </article>
                        ))}
                      </div>
                    ) : (
                      <p className="data-empty">还没有审计日志。上传 CSV 后会自动记录。</p>
                    )}
                  </div>
                </section>
                ) : null}

                {!shouldShowProtocolWorkspace && !shouldShowDataWorkspace ? (
                  <section className="expert-placeholder-panel" aria-label="专家功能提示">
                    <div>
                      <p className="eyebrow">{selectedAgent?.role_name ?? "专家功能"}</p>
                      <h3>{selectedAgent?.name ?? "选择一位专家"}</h3>
                    </div>
                    <p>
                      当前专家主要通过右侧对话推进工作。选择 Dr. Vera Protocol 会显示研究方案，
                      选择 Dr. Data Lin 会显示数据工作区。
                    </p>
                  </section>
                ) : null}
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
                          disabled={extractingMessageId !== null || !canEditSelectedProject}
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
