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
  getMentorEvidenceReviews,
  getMentorRecommendations,
  getMentorTrendSnapshot,
  getProjectAccess,
  getProjectPlanDrafts,
  getProjectProtocol,
  getProjectReminders,
  getProjects,
  getWriterIntroductionDraft,
  refreshProjectReminders,
  saveDataAnalysisRecord,
  saveMentorEvidenceReview,
  saveProjectProtocol,
  saveWriterIntroductionDraft,
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
  FormalTestResult,
  ItemStatus,
  MentorEvidenceItem,
  MentorEvidenceReview,
  MentorEvidenceReviewUpdate,
  MentorRecommendationCard,
  MentorRecommendationResponse,
  MentorTrendSnapshot,
  PairwiseComparisonResult,
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
  WriterIntroductionDraft,
  WriterIntroductionDraftUpdate,
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

const pipelineStatusLabels: Record<PipelineStepStatus, string> = {
  not_started: "未开始",
  in_progress: "进行中",
  ready: "已就绪",
  risk: "有风险",
};

const reminderTypeLabels: Record<ReminderType, string> = {
  due_48h: "48 小时提醒",
  due_24h: "24 小时提醒",
  overdue: "逾期",
  blocked: "受阻",
};

const statusOptions: ItemStatus[] = ["not_started", "in_progress", "blocked", "done"];
const preparedDataSamplePath = "/sample-data/mimic_iv_demo_los_sample.csv";
const preparedDataSampleFileName = "mimic_iv_demo_los_sample.csv";

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
type MentorProgrammingLevel = "none" | "basic" | "intermediate" | "advanced";

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
type PairedDataLayout = "wide" | "long";
type PairedAnalysis = "paired_t" | "friedman" | "rm_anova";
type MultiplicityCorrection = "holm" | "fdr";

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

function formatFormalStatistic(result: FormalTestResult): string {
  if (result.statistic === undefined || result.statistic === null) {
    return "统计量=NA";
  }
  let label = "统计量";
  if (result.test_name.includes("ANOVA")) {
    label = "F";
  } else if (result.test_name.includes("Friedman")) {
    label = "Q";
  } else if (result.test_name.includes("Kruskal")) {
    label = "H";
  } else if (result.test_name.includes("t")) {
    label = "t";
  }
  return `${label}=${result.statistic.toFixed(2)}`;
}

function formatFormalDegreesOfFreedom(result: FormalTestResult): string {
  if (result.degrees_of_freedom === undefined || result.degrees_of_freedom === null) {
    return "df=NA";
  }
  const numeratorDf = result.degrees_of_freedom.toFixed(
    Number.isInteger(result.degrees_of_freedom) ? 0 : 2,
  );
  if (
    result.denominator_degrees_of_freedom !== undefined &&
    result.denominator_degrees_of_freedom !== null
  ) {
    const denominatorDf = result.denominator_degrees_of_freedom.toFixed(
      Number.isInteger(result.denominator_degrees_of_freedom) ? 0 : 2,
    );
    return `df=${numeratorDf}, ${denominatorDf}`;
  }
  return `df=${numeratorDf}`;
}

function formatFormalEffectSize(result: FormalTestResult): string {
  let label = "d";
  if (result.test_name.includes("ANOVA")) {
    label = "η²";
  } else if (result.test_name.includes("Friedman")) {
    label = "W";
  } else if (result.test_name.includes("Kruskal")) {
    label = "ε²";
  } else if (result.test_name.includes("配对")) {
    label = "dz";
  }
  if (result.effect_size === undefined || result.effect_size === null) {
    return `${label}=NA`;
  }
  return `${label}=${result.effect_size.toFixed(2)}`;
}

function formatPairwiseStatistic(result: PairwiseComparisonResult): string {
  if (result.statistic === undefined || result.statistic === null) {
    return "统计量=NA";
  }
  const label = result.test_name.includes("Tukey") || result.test_name.includes("Games-Howell")
    ? "q"
    : result.test_name.includes("秩和") || result.test_name.includes("Dunn")
      ? "Z"
      : "t";
  return `${label}=${result.statistic.toFixed(2)}`;
}

function formatPairwiseEffectSize(result: PairwiseComparisonResult): string {
  if (result.effect_size === undefined || result.effect_size === null) {
    return "效应量=NA";
  }
  const label = result.test_name.includes("秩和") || result.test_name.includes("Dunn") ? "r" : "d";
  return `${label}=${result.effect_size.toFixed(2)}`;
}

function formatPairwiseCorrectionLabel(result: PairwiseComparisonResult): string {
  return result.correction_method === "Benjamini-Hochberg FDR" ? "FDR P" : "Holm P";
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

function mentorCardToProtocolUpdate(card: MentorRecommendationCard): ProjectProtocolUpdate {
  return {
    research_question: card.research_question,
    hypothesis: `围绕“${card.title}”，假设该研究路线能够识别有临床或流程意义的放疗物理差异，并形成可复核的剂量学、效率或质量控制证据。`,
    study_type: "单中心回顾性放疗物理研究；首轮以脱敏结构化数据和可复现分析流程为主，后续可扩展为多中心或前瞻性验证。",
    primary_endpoint: "主要终点应从推荐卡的数据路径中选择一个最能回答研究问题的指标，例如计划质量、OAR 保护、QA 结果、流程耗时或模型性能。",
    secondary_endpoints: "次要终点可包括靶区覆盖、剂量梯度、适形指数、均匀性指数、计划复杂度、处理时间、返工率、亚组稳定性和敏感性分析。",
    inclusion_criteria: "纳入已完成标准治疗或质控流程、关键计划/剂量/结构数据完整、可追溯计划系统版本、并已完成脱敏的数据记录。",
    exclusion_criteria: "排除关键字段缺失、计划或影像质量不可复核、治疗流程中断、数据来源不一致、以及存在直接身份标识或脱敏不充分风险的记录。",
    data_requirements: card.data_pathway,
    experiment_workflow: [card.methods_route, ...card.first_milestones].join("\n"),
    statistical_plan: card.statistical_plan,
    target_journals: card.target_journals.join("、"),
    rhea_milestones: card.first_milestones.join("\n"),
  };
}

function formatMentorEvidenceStatus(status: string): string {
  const labels: Record<string, string> = {
    local_template: "本地证据模板",
    pubmed: "PubMed 检索结果",
    pubmed_crossref: "PubMed + Crossref 候选",
    crossref: "Crossref 检索结果",
    external_pending: "待真实检索复核",
  };
  return labels[status] ?? status;
}

function formatMentorReviewStatus(status: string): string {
  const labels: Record<string, string> = {
    unreviewed: "未人工复核",
    reviewed: "已人工复核",
    rejected: "已排除",
  };
  return labels[status] ?? status;
}

function formatMentorReviewUsage(evidence: MentorEvidenceItem): string {
  const usages = [
    evidence.use_in_introduction ? "Introduction" : null,
    evidence.use_in_discussion ? "Discussion" : null,
  ].filter(Boolean);
  return usages.length ? usages.join(" / ") : "暂未指定";
}

function formatMentorCitationDetails(evidence: MentorEvidenceItem): string {
  const volumeIssue = evidence.volume
    ? `${evidence.volume}${evidence.issue ? `(${evidence.issue})` : ""}`
    : evidence.issue
      ? `(${evidence.issue})`
      : "";
  const details = [
    evidence.authors?.length ? `作者：${evidence.authors.join(", ")}` : null,
    volumeIssue ? `卷期：${volumeIssue}` : null,
    evidence.page ? `页码/编号：${evidence.page}` : null,
  ].filter(Boolean);
  return details.length ? details.join(" · ") : "作者、卷期和页码待补充";
}

type IntroductionDraftField =
  | "background_paragraph"
  | "gap_paragraph"
  | "objective_paragraph";

type IntroductionCitationBindings = Record<IntroductionDraftField, string[]>;

const introductionDraftFields: IntroductionDraftField[] = [
  "background_paragraph",
  "gap_paragraph",
  "objective_paragraph",
];

const introductionDraftFieldLabels: Record<IntroductionDraftField, string> = {
  background_paragraph: "背景段",
  gap_paragraph: "研究空白段",
  objective_paragraph: "研究目的段",
};

interface IntroductionCitationUsage {
  key: string;
  label: string;
  count: number;
  sections: string[];
}

interface IntroductionCitationMatch {
  key: string;
  label: string;
}

interface IntroductionUsedReference {
  usage: IntroductionCitationUsage;
  cardTitle?: string;
  evidenceIndex?: number;
  evidence?: MentorEvidenceItem;
}

function isLikelyIdentifierColumn(columnName: string): boolean {
  return /(^id$|_id$|subject|hadm|patient|record|encounter|accession)/i.test(columnName);
}

function preferredNumericColumns(columns: DataQualityReport["columns"]): string[] {
  const numericColumns = columns.filter((column) => column.inferred_type === "numeric");
  const preferredColumns = numericColumns.filter((column) => !isLikelyIdentifierColumn(column.name));
  return (preferredColumns.length ? preferredColumns : numericColumns)
    .map((column) => column.name)
    .slice(0, 2);
}

function buildPreparedReferenceReport(): MentorRecommendationResponse {
  const retrievedAt = new Date().toISOString();
  return {
    profile_summary: "已加载预备 DATA 引用包，用于验证 Mentor 到 Alex Writer 的真实引用闭环。",
    resource_diagnosis: [
      "当前引用来自公开医学数据源和数据集主论文，适合先验证引用标记、字段绑定和导出流程。",
      "这些引用用于产品联调，不代表当前放疗课题的最终核心文献清单。",
    ],
    matched_strengths: [
      "引用包含 DOI、期刊、年份和候选 Vancouver 格式，Alex Writer 可以直接进行字段级引用质控。",
      "CSV 样本与引用来源一致，便于同时测试数据和写作链路。",
    ],
    recommendations: [
      {
        title: "预备 DATA 真实医学数据源",
        research_question: "公开去标识化 EHR demo 数据能否支撑当前 CSV 质控、统计草案和写作引用流程联调？",
        why_fit: "MIMIC-IV Demo 是公开医学数据样本，文件体量小，字段结构真实，适合避免空流程演示。",
        data_pathway: "使用 MIMIC-IV Demo 的 patients 和 admissions 表派生住院天数联调 CSV。",
        methods_route: "先完成字段质控、描述性统计和正式检验边界检查，再交给 Alex Writer 生成 Methods/Results 草稿。",
        statistical_plan: "以 length_of_stay_days 和 anchor_age 为数值结局，以 gender 或 admission_type 作为示例分组变量。",
        innovation_point: "将真实公开数据源、可追溯引用和本地论文工作流打通，验证端到端产品闭环。",
        feasibility_note: "该数据包只用于联调；正式放疗论文仍需替换为本中心伦理批准后的真实研究数据。",
        risk_flags: [
          "MIMIC-IV Demo 是 ICU/EHR 数据，不是放疗计划数据。",
          "公开 demo 仍需按 PhysioNet 要求引用来源。",
        ],
        first_milestones: [
          "加载预备 CSV 并生成质控报告",
          "生成统计草案并检查正式检验条件",
          "在 Alex Writer 中插入并保存引用标记",
        ],
        target_journals: ["Scientific Data", "PhysioNet", "JAMIA Open"],
        evidence_items: [
          {
            source_type: "prepared_data_reference",
            evidence_status: "public_dataset",
            retrieved_at: retrievedAt,
            external_url: "https://physionet.org/content/mimic-iv-demo/2.2/",
            crossref_url: "https://doi.org/10.13026/dp1f-ex47",
            pmid: null,
            title: "MIMIC-IV Clinical Database Demo",
            journal: "PhysioNet",
            publication_year: "2024",
            doi: "10.13026/dp1f-ex47",
            citation_text: "MIMIC-IV Clinical Database Demo. PhysioNet. doi:10.13026/dp1f-ex47.",
            vancouver_citation: "MIMIC-IV Clinical Database Demo. PhysioNet. doi:10.13026/dp1f-ex47.",
            authors: [],
            volume: null,
            issue: null,
            page: null,
            publication_types: ["Dataset"],
            review_status: "reviewed",
            review_note: "预备 DATA 来源引用，用于联调。",
            reviewer: "SCI helper",
            full_text_checked: true,
            use_in_introduction: true,
            use_in_discussion: false,
            search_query: "MIMIC-IV Clinical Database Demo PhysioNet",
            evidence_summary: "MIMIC-IV Clinical Database Demo 是 PhysioNet 上的公开演示数据集，可用于产品流程联调。",
            recommendation_signal: "适合验证 CSV 质控、统计草案和引用追溯流程。",
            limitation: "该 demo 不是放疗专科数据，只能作为医学数据流程联调样本。",
          },
          {
            source_type: "prepared_data_reference",
            evidence_status: "public_article",
            retrieved_at: retrievedAt,
            external_url: "https://www.nature.com/articles/s41597-022-01899-x",
            crossref_url: "https://doi.org/10.1038/s41597-022-01899-x",
            pmid: null,
            title: "MIMIC-IV, a freely accessible electronic health record dataset",
            journal: "Scientific Data",
            publication_year: "2023",
            doi: "10.1038/s41597-022-01899-x",
            citation_text:
              "Johnson AEW, Bulgarelli L, Shen L, Gayles A, Shammout A, Horng S, et al. MIMIC-IV, a freely accessible electronic health record dataset. Scientific Data. 2023. doi:10.1038/s41597-022-01899-x.",
            vancouver_citation:
              "Johnson AEW, Bulgarelli L, Shen L, Gayles A, Shammout A, Horng S, et al. MIMIC-IV, a freely accessible electronic health record dataset. Sci Data. 2023;10:1. doi:10.1038/s41597-022-01899-x.",
            authors: ["Johnson AEW", "Bulgarelli L", "Shen L", "Gayles A", "Shammout A", "Horng S"],
            volume: "10",
            issue: null,
            page: "1",
            publication_types: ["Journal Article"],
            review_status: "reviewed",
            review_note: "MIMIC-IV 数据集主论文。",
            reviewer: "SCI helper",
            full_text_checked: true,
            use_in_introduction: true,
            use_in_discussion: false,
            search_query: "MIMIC-IV freely accessible electronic health record dataset",
            evidence_summary: "该论文描述 MIMIC-IV 去标识化电子健康记录数据集的结构和开放研究用途。",
            recommendation_signal: "适合作为公开医学 CSV 样本的数据集家族引用。",
            limitation: "用于数据源说明，不替代具体研究问题的领域文献。",
          },
          {
            source_type: "prepared_data_reference",
            evidence_status: "public_article",
            retrieved_at: retrievedAt,
            external_url: "https://physionet.org/about/citation/",
            crossref_url: "https://doi.org/10.1161/01.CIR.101.23.e215",
            pmid: "10851218",
            title: "PhysioNet: The Research Resource for Complex Physiologic Signals",
            journal: "Circulation",
            publication_year: "2000",
            doi: "10.1161/01.CIR.101.23.e215",
            citation_text:
              "Goldberger AL, Amaral LAN, Glass L, Hausdorff JM, Ivanov PC, Mark RG, et al. PhysioNet: The Research Resource for Complex Physiologic Signals. Circulation. 2000. doi:10.1161/01.CIR.101.23.e215.",
            vancouver_citation:
              "Goldberger AL, Amaral LAN, Glass L, Hausdorff JM, Ivanov PC, Mark RG, et al. PhysioNet: The Research Resource for Complex Physiologic Signals. Circulation. 2000;101(23):e215-e220. doi:10.1161/01.CIR.101.23.e215.",
            authors: ["Goldberger AL", "Amaral LAN", "Glass L", "Hausdorff JM", "Ivanov PC", "Mark RG"],
            volume: "101",
            issue: "23",
            page: "e215-e220",
            publication_types: ["Journal Article"],
            review_status: "reviewed",
            review_note: "PhysioNet 平台引用。",
            reviewer: "SCI helper",
            full_text_checked: true,
            use_in_introduction: true,
            use_in_discussion: false,
            search_query: "PhysioNet Research Resource Complex Physiologic Signals",
            evidence_summary: "该论文是 PhysioNet 平台的标准引用。",
            recommendation_signal: "适合说明公开医学数据源平台来源。",
            limitation: "平台引用需与具体数据集引用共同使用。",
          },
        ],
      },
    ],
    next_steps: [
      "在 Dr. Data Lin 中加载预备 CSV。",
      "在 Alex Writer 中插入候选引用并保存草稿。",
      "导出引用清单，确认 DOI/PMID/Vancouver 链路完整。",
    ],
  };
}

function buildWriterMethodsResultsDraft(
  qualityReport: DataQualityReport | null,
  statisticsReport: DataStatisticsReport | null,
): WriterMethodsResultsDraft | null {
  if (!qualityReport || !statisticsReport) {
    return null;
  }

  const formalTestReport = statisticsReport.formal_test_report ?? null;
  const numericLines = statisticsReport.numeric_summaries.slice(0, 6).map(
    (summary) =>
      `${summary.column}: n=${summary.n}, mean=${summary.mean}, SD=${summary.std_dev}, median=${summary.median}, range=${summary.min}-${summary.max}`,
  );
  const groupLines = statisticsReport.group_comparisons
    .slice(0, 4)
    .map((comparison) => comparison.interpretation);
  const formalTestLines = formalTestReport?.results.length
    ? formalTestReport.results.map((result) =>
        [
          `${result.outcome_column}: ${result.interpretation}`,
          `检验：${result.test_name}`,
          `P=${formatPValue(result.p_value)}`,
          formatFormalEffectSize(result),
          result.warnings.length ? `注意：${result.warnings.join("；")}` : null,
        ]
          .filter(Boolean)
          .join("；"),
      )
    : ["尚未执行正式检验；Results 草稿不得编造 P 值、置信区间或显著性结论。"];
  const chartLines = statisticsReport.chart_specs.slice(0, 5).map(
    (chart) => `${chart.title}: ${chart.narrative}`,
  );
  const missingItems = [
    qualityReport.missing_required_fields.length
      ? `数据需求缺少字段：${qualityReport.missing_required_fields.join("、")}`
      : null,
    qualityReport.issues.length ? `CSV 质控仍有 ${qualityReport.issues.length} 个问题需复核。` : null,
    qualityReport.privacy_report?.risk_level === "red"
      ? "脱敏检查为高风险，不能进入正式统计或论文写作。"
      : null,
    formalTestReport ? null : "正式假设检验尚未执行；论文 Results 中只能保留描述性统计和待检验提示。",
    statisticsReport.next_step || null,
  ].filter(Boolean) as string[];

  return {
    methodsParagraphs: [
      `本联调数据来自 ${qualityReport.file_name}，共 ${qualityReport.row_count} 行、${qualityReport.column_count} 列。CSV 上传后先执行字段类型识别、缺失率检查、关键字段覆盖检查和脱敏风险扫描；原始 CSV 不在系统中持久化保存。`,
      statisticsReport.methods_draft,
      formalTestReport
        ? `正式检验在人工确认研究设计、终点定义、脱敏状态、缺失处理、统计假设和多重比较边界后执行；当前方法版本为 ${formalTestReport.method_version}。`
        : "当前尚未执行正式假设检验；Methods 中应将 P 值相关分析列为待补充或预设统计计划。",
    ],
    resultsParagraphs: [
      statisticsReport.results_draft,
      numericLines.length
        ? `描述性统计摘要：${numericLines.join("；")}。`
        : "当前 CSV 未生成可写入 Results 的数值描述性统计。",
      groupLines.length
        ? `分组描述显示：${groupLines.join("；")}。`
        : "当前未设置有效分组列，Results 暂不写入组间比较描述。",
      formalTestReport
        ? `正式检验摘要：${formalTestLines.join("；")}。`
        : "正式检验尚未执行，因此 Results 草稿不报告 P 值或显著性结论。",
    ],
    formalTestLines,
    chartLines,
    missingItems,
  };
}

function buildReviewerChecks(params: {
  protocolHasContent: boolean;
  protocol: ProjectProtocol | null;
  qualityReport: DataQualityReport | null;
  statisticsReport: DataStatisticsReport | null;
  writerMethodsResultsDraft: WriterMethodsResultsDraft | null;
  writerIntroductionDraftForm: WriterIntroductionDraftUpdate;
  citationIssueCount: number;
  candidateReferenceCount: number;
  reminderSummary: ProjectReminderSummary | null;
}): ReviewerCheckItem[] {
  const {
    protocolHasContent,
    protocol,
    qualityReport,
    statisticsReport,
    writerMethodsResultsDraft,
    writerIntroductionDraftForm,
    citationIssueCount,
    candidateReferenceCount,
    reminderSummary,
  } = params;
  const formalTestReport = statisticsReport?.formal_test_report ?? null;
  const introductionHasText = introductionDraftFields.some(
    (field) => writerIntroductionDraftForm[field].trim().length > 0,
  );

  return [
    {
      title: "研究方案完整性",
      severity: protocolHasContent ? "green" : "red",
      status: protocolHasContent ? "已形成方案" : "缺少方案",
      detail: protocol?.research_question
        ? `研究问题：${protocol.research_question}`
        : "当前项目还没有可审查的研究问题、终点和统计路线。",
      recommendation: protocolHasContent
        ? "正式投稿前继续核对 PICO/PECO、主要终点和伦理材料是否一致。"
        : "先由 Dr. Vera Protocol 生成并保存研究方案。",
    },
    {
      title: "数据真实性与脱敏",
      severity: qualityReport
        ? qualityReport.privacy_report?.risk_level === "red"
          ? "red"
          : qualityReport.issues.length
            ? "orange"
            : "green"
        : "red",
      status: qualityReport ? `${qualityReport.row_count} 行 / ${qualityReport.column_count} 列` : "无数据报告",
      detail: qualityReport
        ? qualityReport.privacy_report?.summary ?? "已生成 CSV 质控报告，但未生成隐私摘要。"
        : "尚未上传或加载可审查 CSV。",
      recommendation: qualityReport
        ? qualityReport.privacy_report?.risk_level === "red"
          ? "高风险脱敏问题解决前，不应继续正式统计或写作。"
          : qualityReport.issues.length
            ? "先处理缺失、字段覆盖或异常值提示，再进入正式分析。"
            : "保留审计记录，并在 Methods 中说明原始 CSV 不持久化保存。"
        : "先在 Dr. Data Lin 中加载预备 DATA 或上传脱敏 CSV。",
    },
    {
      title: "统计结果边界",
      severity: statisticsReport ? (formalTestReport ? "green" : "orange") : "red",
      status: statisticsReport
        ? formalTestReport
          ? `${formalTestReport.results.length} 项正式检验`
          : "仅有描述性统计"
        : "无统计草案",
      detail: statisticsReport
        ? formalTestReport?.audit_summary ?? statisticsReport.next_step
        : "尚无可审查的统计草案或正式检验记录。",
      recommendation: formalTestReport
        ? "核对检验前确认项、组数、结局定义、多重比较和效应量解释。"
        : "Results 中不得写 P 值或显著性结论；需要用户确认后再执行正式检验。",
    },
    {
      title: "Methods / Results 一致性",
      severity: writerMethodsResultsDraft
        ? writerMethodsResultsDraft.missingItems.length
          ? "orange"
          : "green"
        : "red",
      status: writerMethodsResultsDraft ? "已生成草稿" : "缺少结果草稿",
      detail: writerMethodsResultsDraft
        ? writerMethodsResultsDraft.missingItems.slice(0, 2).join("；") || "未发现系统级阻断项。"
        : "Alex Writer 尚未接收到 Data Lin 的统计草稿。",
      recommendation: writerMethodsResultsDraft
        ? "逐句核对 Results 草稿是否只引用已生成的数据与检验结果。"
        : "先完成 Data Lin 统计草案，再返回 Alex Writer 生成 Methods / Results。",
    },
    {
      title: "Introduction 引用追溯",
      severity: candidateReferenceCount
        ? citationIssueCount
          ? "orange"
          : introductionHasText
            ? "green"
            : "orange"
        : "red",
      status: candidateReferenceCount ? `${candidateReferenceCount} 条候选引用` : "无确认引用",
      detail: citationIssueCount
        ? `当前还有 ${citationIssueCount} 项引用质控问题。`
        : introductionHasText
          ? "Introduction 草稿已有可追溯引用或手动绑定。"
          : "候选引用已存在，但 Introduction 正文仍需撰写。",
      recommendation: citationIssueCount
        ? "先解决 DOI/PMID、全文核对、用途标记和绑定异常。"
        : "投稿前仍需人工核对全文和目标期刊引用格式。",
    },
    {
      title: "执行风险与里程碑",
      severity: reminderSummary?.risk_level ?? "orange",
      status: reminderSummary
        ? `${reminderSummary.active_count} 条提醒 / ${reminderSummary.overdue_count} 个逾期`
        : "未读取 Rhea 监控",
      detail: reminderSummary?.manager_note ?? "尚未生成项目执行提醒。",
      recommendation: reminderSummary?.overdue_count
        ? "先处理逾期任务，再进入投稿前版本冻结。"
        : "保持 Rhea 任务状态与论文草稿进展同步。",
    },
  ];
}

function buildPipelineSteps(params: {
  candidateReferenceCount: number;
  protocolHasContent: boolean;
  qualityReport: DataQualityReport | null;
  statisticsReport: DataStatisticsReport | null;
  writerMethodsResultsDraft: WriterMethodsResultsDraft | null;
  introductionHasText: boolean;
  reviewerChecks: ReviewerCheckItem[];
}): PipelineStep[] {
  const {
    candidateReferenceCount,
    protocolHasContent,
    qualityReport,
    statisticsReport,
    writerMethodsResultsDraft,
    introductionHasText,
    reviewerChecks,
  } = params;
  const reviewerRedCount = reviewerChecks.filter((item) => item.severity === "red").length;
  const reviewerOrangeCount = reviewerChecks.filter((item) => item.severity === "orange").length;

  return [
    {
      id: "literature",
      agentId: "mentor",
      title: "选题与引用",
      status: candidateReferenceCount ? "ready" : "not_started",
      detail: candidateReferenceCount ? `${candidateReferenceCount} 条确认引用` : "等待 Mentor 候选引用",
    },
    {
      id: "protocol",
      agentId: "study_planner",
      title: "研究方案",
      status: protocolHasContent ? "ready" : "not_started",
      detail: protocolHasContent ? "方案已形成" : "等待研究问题和终点",
    },
    {
      id: "data",
      agentId: "data_analyst",
      title: "数据与统计",
      status: statisticsReport
        ? statisticsReport.formal_test_report
          ? "ready"
          : "in_progress"
        : qualityReport
          ? "in_progress"
          : "not_started",
      detail: statisticsReport
        ? statisticsReport.formal_test_report
          ? "已有正式检验"
          : "已有统计草案"
        : qualityReport
          ? "已有质控报告"
          : "等待 CSV",
    },
    {
      id: "writing",
      agentId: "writer",
      title: "写作草稿",
      status: writerMethodsResultsDraft || introductionHasText ? "ready" : "not_started",
      detail: writerMethodsResultsDraft
        ? "Methods / Results 已生成"
        : introductionHasText
          ? "Introduction 已开始"
          : "等待写作素材",
    },
    {
      id: "review",
      agentId: "reviewer",
      title: "投稿前审查",
      status: reviewerRedCount ? "risk" : reviewerOrangeCount ? "in_progress" : "ready",
      detail: reviewerRedCount
        ? `${reviewerRedCount} 项高风险`
        : reviewerOrangeCount
          ? `${reviewerOrangeCount} 项需复核`
          : "清单已通过",
    },
  ];
}

function buildProtocolQualitySummary(protocol: ProjectProtocol | null): ProtocolQualitySummary {
  const valueFor = (key: keyof ProjectProtocolUpdate): string => protocol?.[key]?.trim() ?? "";
  const checkText = (
    key: keyof ProjectProtocolUpdate,
    title: string,
    minimumLength: number,
    highRiskWhenMissing: boolean,
    recommendation: string,
  ): ProtocolQualityItem => {
    const value = valueFor(key);
    if (!value) {
      return {
        key,
        title,
        status: highRiskWhenMissing ? "high_risk" : "needs_input",
        detail: "当前为空。",
        recommendation,
      };
    }
    if (value.length < minimumLength) {
      return {
        key,
        title,
        status: "needs_input",
        detail: `已有内容，但较短，约 ${value.length} 个字符。`,
        recommendation,
      };
    }
    return {
      key,
      title,
      status: "passed",
      detail: `已有可审查内容，约 ${value.length} 个字符。`,
      recommendation: "投稿前继续核对该项是否与数据字段、伦理材料和目标期刊要求一致。",
    };
  };
  const items: ProtocolQualityItem[] = [
    checkText("research_question", "研究问题是否明确", 20, true, "先写清对象、干预/暴露、比较和主要结局。"),
    checkText("hypothesis", "研究假设是否存在", 20, true, "补充方向性假设，并避免写成泛泛目标。"),
    checkText("study_type", "研究类型是否填写", 10, true, "明确回顾性/前瞻性、单中心/多中心、配对/独立样本等设计。"),
    checkText("primary_endpoint", "主要终点是否明确", 10, true, "指定一个最能回答研究问题的主要终点。"),
    checkText("inclusion_criteria", "纳入标准是否完整", 20, true, "写清病例来源、时间范围、治疗方式和最低数据要求。"),
    checkText("exclusion_criteria", "排除标准是否完整", 20, false, "列出缺失关键数据、重复病例、质控不可复核等排除条件。"),
    checkText("data_requirements", "数据需求是否可执行", 30, true, "列出必需字段、来源系统、导出格式和脱敏要求。"),
    checkText("statistical_plan", "统计路线是否存在", 30, true, "说明描述性统计、组间比较、配对/多重比较和显著性边界。"),
    checkText("experiment_workflow", "实验流程是否可复现", 30, false, "补充数据导出、清洗、质控、统计、图表和审稿复核顺序。"),
    checkText("rhea_milestones", "Rhea 里程碑是否可监控", 20, false, "拆成可执行节点，并写清每个节点的交付物。"),
  ];
  const passedCount = items.filter((item) => item.status === "passed").length;
  const needsInputCount = items.filter((item) => item.status === "needs_input").length;
  const highRiskCount = items.filter((item) => item.status === "high_risk").length;
  const completionPercent = Math.round((passedCount / items.length) * 100);
  const nextItem = items.find((item) => item.status === "high_risk") ?? items.find((item) => item.status === "needs_input");

  return {
    completionPercent,
    passedCount,
    needsInputCount,
    highRiskCount,
    nextAction: nextItem ? `${nextItem.title}：${nextItem.recommendation}` : "方案质量检查已通过，下一步可生成 Rhea 执行计划。",
    items,
  };
}

interface IntroductionFieldCitationMap {
  field: IntroductionDraftField;
  label: string;
  hasText: boolean;
  missingTrace: boolean;
  usages: IntroductionCitationUsage[];
  matchedReferences: IntroductionUsedReference[];
  unmatchedUsages: IntroductionCitationUsage[];
  manualReferences: IntroductionUsedReference[];
  unmatchedBindingKeys: string[];
}

interface IntroductionCitationQualityIssue {
  key: string;
  category: string;
  fieldLabel: string;
  referenceLabel: string;
  message: string;
  suggestion: string;
  action?:
    | {
        kind: "mark-introduction-use";
        cardTitle: string;
        evidenceIndex: number;
        evidence: MentorEvidenceItem;
      }
    | {
        kind: "remove-binding";
        field: IntroductionDraftField;
        bindingKey: string;
      };
}

interface MentorCandidateReference {
  cardTitle: string;
  evidenceIndex: number;
  evidence: MentorEvidenceItem;
}

interface MentorDedupedCandidateReference {
  cardTitles: string[];
  duplicateCount: number;
  evidence: MentorEvidenceItem;
}

interface WriterMethodsResultsDraft {
  methodsParagraphs: string[];
  resultsParagraphs: string[];
  formalTestLines: string[];
  chartLines: string[];
  missingItems: string[];
}

interface CsvProcessingDefaults {
  report: DataQualityReport;
  groupColumn: string;
  outcomeColumns: string[];
}

interface WorkflowSummary {
  source: "prepared" | "restored" | "manual";
  fileName: string;
  rowCount: number;
  columnCount: number;
  chartCount: number;
  saved: boolean;
  message: string;
}

type ReviewerCheckSeverity = "green" | "orange" | "red";
type PipelineStepStatus = "not_started" | "in_progress" | "ready" | "risk";
type ProtocolQualityStatus = "passed" | "needs_input" | "high_risk";

interface ReviewerCheckItem {
  title: string;
  severity: ReviewerCheckSeverity;
  status: string;
  detail: string;
  recommendation: string;
}

interface PipelineStep {
  id: string;
  agentId: AgentId;
  title: string;
  status: PipelineStepStatus;
  detail: string;
}

interface ProtocolQualityItem {
  key: string;
  title: string;
  status: ProtocolQualityStatus;
  detail: string;
  recommendation: string;
}

interface ProtocolQualitySummary {
  completionPercent: number;
  passedCount: number;
  needsInputCount: number;
  highRiskCount: number;
  nextAction: string;
  items: ProtocolQualityItem[];
}

function buildCitationTrace(evidence: MentorEvidenceItem): string {
  const traceItems = [
    evidence.pmid ? `PMID ${evidence.pmid}` : null,
    evidence.doi ? `DOI ${evidence.doi}` : null,
  ].filter(Boolean);
  const citation = evidence.vancouver_citation || evidence.citation_text;
  return [
    traceItems.length ? traceItems.join(" / ") : "候选来源待核对",
    citation ? `候选引用：${citation}` : null,
  ]
    .filter(Boolean)
    .join("；");
}

function buildIntroductionCitationSentence(
  field: IntroductionDraftField,
  evidence: MentorEvidenceItem,
): string {
  const title = evidence.title?.replace(/\.$/, "") || evidence.evidence_summary;
  const topicText = title ? `“${title}”` : "相关候选文献";
  const trace = buildCitationTrace(evidence);
  const sentenceByField: Record<IntroductionDraftField, string> = {
    background_paragraph: `已有${topicText}等候选文献提示，该方向在放疗物理流程、计划质量或临床实施中具有持续研究价值。[${trace}]`,
    gap_paragraph: `不过，现有${topicText}相关证据仍需要结合本中心设备、数据结构和具体流程进一步验证其适用性。[${trace}]`,
    objective_paragraph: `因此，本研究拟在上述候选文献线索基础上，围绕当前项目的具体研究问题进一步评估本中心数据中的相关物理或流程指标。[${trace}]`,
  };
  return sentenceByField[field];
}

function extractCitationMatches(text: string): IntroductionCitationMatch[] {
  return [
    ...Array.from(text.matchAll(/\bDOI\s+([^\]\s；;，,]+)/gi)).map((match) => ({
      key: `doi:${match[1].toLowerCase()}`,
      label: `DOI ${match[1]}`,
    })),
    ...Array.from(text.matchAll(/\bPMID\s+(\d+)/gi)).map((match) => ({
      key: `pmid:${match[1]}`,
      label: `PMID ${match[1]}`,
    })),
  ];
}

function buildCitationUsagesForText(
  text: string,
  sectionLabel: string,
): IntroductionCitationUsage[] {
  const usageMap = new Map<string, IntroductionCitationUsage>();
  extractCitationMatches(text).forEach((match) => {
    const current = usageMap.get(match.key) ?? {
      key: match.key,
      label: match.label,
      count: 0,
      sections: [],
    };
    current.count += 1;
    if (!current.sections.includes(sectionLabel)) {
      current.sections.push(sectionLabel);
    }
    usageMap.set(match.key, current);
  });
  return Array.from(usageMap.values()).sort((left, right) => right.count - left.count);
}

function extractIntroductionCitationUsages(
  draft: WriterIntroductionDraftUpdate,
): IntroductionCitationUsage[] {
  const usageMap = new Map<string, IntroductionCitationUsage>();

  introductionDraftFields.forEach((field) => {
    const text = draft[field];
    const sectionLabel = introductionDraftFieldLabels[field];
    buildCitationUsagesForText(text, sectionLabel).forEach((usage) => {
      const current = usageMap.get(usage.key) ?? {
        key: usage.key,
        label: usage.label,
        count: 0,
        sections: [],
      };
      current.count += usage.count;
      if (!current.sections.includes(sectionLabel)) {
        current.sections.push(sectionLabel);
      }
      usageMap.set(usage.key, current);
    });
  });

  return Array.from(usageMap.values()).sort((left, right) => right.count - left.count);
}

function referenceKeysForEvidence(evidence: MentorEvidenceItem): string[] {
  const keys = [
    evidence.doi ? `doi:${evidence.doi.toLowerCase()}` : null,
    evidence.pmid ? `pmid:${evidence.pmid}` : null,
  ].filter(Boolean) as string[];
  if (!keys.length) {
    keys.push(fallbackReferenceKeyForEvidence(evidence));
  }
  return keys;
}

function fallbackReferenceKeyForEvidence(evidence: MentorEvidenceItem): string {
  const fallback = (evidence.title || evidence.search_query || evidence.evidence_summary)
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
  return `fallback:${fallback}`;
}

function primaryReferenceKeyForEvidence(evidence: MentorEvidenceItem): string {
  if (evidence.doi?.trim()) {
    return `doi:${evidence.doi.trim().toLowerCase()}`;
  }
  if (evidence.pmid?.trim()) {
    return `pmid:${evidence.pmid.trim()}`;
  }
  return fallbackReferenceKeyForEvidence(evidence);
}

function formatCitationBindingKey(key: string): string {
  if (key.startsWith("pmid:")) {
    return `PMID ${key.slice(5)}`;
  }
  if (key.startsWith("doi:")) {
    return `DOI ${key.slice(4)}`;
  }
  return "本地候选引用";
}

function findCandidateReferenceForUsage(
  usage: IntroductionCitationUsage,
  references: MentorCandidateReference[],
): MentorCandidateReference | undefined {
  return references.find(({ evidence }) => referenceKeysForEvidence(evidence).includes(usage.key));
}

function buildIntroductionFieldCitationMaps(
  draft: WriterIntroductionDraftUpdate,
  references: MentorCandidateReference[],
): IntroductionFieldCitationMap[] {
  const citationBindings = normalizeIntroductionCitationBindings(draft.citation_bindings);
  return introductionDraftFields.map((field) => {
    const text = draft[field];
    const label = introductionDraftFieldLabels[field];
    const usages = buildCitationUsagesForText(text, label);
    const usedReferences = usages.map((usage) => {
      const matchedReference = findCandidateReferenceForUsage(usage, references);
      return {
        usage,
        cardTitle: matchedReference?.cardTitle,
        evidenceIndex: matchedReference?.evidenceIndex,
        evidence: matchedReference?.evidence,
      };
    });
    const manualReferences = citationBindings[field].map((key) => {
      const usage = {
        key,
        label: formatCitationBindingKey(key),
        count: 1,
        sections: [label],
      };
      const matchedReference = findCandidateReferenceForUsage(usage, references);
      return {
        usage,
        cardTitle: matchedReference?.cardTitle,
        evidenceIndex: matchedReference?.evidenceIndex,
        evidence: matchedReference?.evidence,
      };
    });
    return {
      field,
      label,
      hasText: Boolean(text.trim()),
      missingTrace: Boolean(text.trim()) && usages.length === 0,
      usages,
      matchedReferences: usedReferences.filter((item) => item.evidence),
      unmatchedUsages: usedReferences.filter((item) => !item.evidence).map((item) => item.usage),
      manualReferences: manualReferences.filter((item) => item.evidence),
      unmatchedBindingKeys: manualReferences.filter((item) => !item.evidence).map((item) => item.usage.key),
    };
  });
}

function buildIntroductionCitationQualityIssues(
  fieldMaps: IntroductionFieldCitationMap[],
): IntroductionCitationQualityIssue[] {
  const issueMap = new Map<string, IntroductionCitationQualityIssue>();

  function addIssue(
    fieldLabel: string,
    referenceLabel: string,
    issueKey: string,
    category: string,
    message: string,
    suggestion: string,
    action?: IntroductionCitationQualityIssue["action"],
  ) {
    const key = `${fieldLabel}:${referenceLabel}:${issueKey}`;
    if (!issueMap.has(key)) {
      issueMap.set(key, { key, category, fieldLabel, referenceLabel, message, suggestion, action });
    }
  }

  fieldMaps.forEach((fieldMap) => {
    if (fieldMap.missingTrace) {
      addIssue(
        fieldMap.label,
        "段落正文",
        "missing-trace",
        "追溯异常",
        "已有正文但缺少 PMID / DOI 追溯标记或手动绑定",
        "为该段插入 PMID / DOI 追溯标记，或手动绑定已确认可用的候选引用",
      );
    }

    fieldMap.unmatchedUsages.forEach((usage) => {
      addIssue(
        fieldMap.label,
        usage.label,
        "unmatched-trace",
        "追溯异常",
        "追溯标记未匹配到当前候选引用",
        "检查草稿中的 PMID / DOI 是否录入正确，或先把对应文献加入候选引用清单",
      );
    });

    fieldMap.unmatchedBindingKeys.forEach((key) => {
      addIssue(
        fieldMap.label,
        formatCitationBindingKey(key),
        "unmatched-binding",
        "绑定异常",
        "手动绑定未匹配到当前候选引用",
        "删除该手动绑定，或先确认对应候选文献仍在当前引用清单中",
        { kind: "remove-binding", field: fieldMap.field, bindingKey: key },
      );
    });

    [...fieldMap.matchedReferences, ...fieldMap.manualReferences].forEach((item) => {
      const evidence = item.evidence;
      if (!evidence) {
        return;
      }
      const referenceLabel = item.usage.label;
      if (!evidence.full_text_checked) {
        addIssue(
          fieldMap.label,
          referenceLabel,
          "full-text",
          "全文核对",
          "候选文献尚未核对全文",
          "阅读全文并核对研究对象、方法、结论和 DOI 页面后，再勾选全文核对",
        );
      }
      if (!evidence.pmid) {
        addIssue(
          fieldMap.label,
          referenceLabel,
          "pmid",
          "元数据缺失",
          "候选文献缺 PMID",
          "在 PubMed 或候选文献复核备注中补充 PMID；若无 PMID，请保留 DOI 并人工说明",
        );
      }
      if (!evidence.doi) {
        addIssue(
          fieldMap.label,
          referenceLabel,
          "doi",
          "元数据缺失",
          "候选文献缺 DOI",
          "在 DOI 页面、Crossref 或期刊页面核对 DOI，并补充到候选文献记录",
        );
      }
      if (!evidence.vancouver_citation) {
        addIssue(
          fieldMap.label,
          referenceLabel,
          "vancouver",
          "引用格式",
          "候选文献缺 Vancouver 候选引用",
          "先补齐作者、期刊、年份、卷期页码或 DOI，再重新生成或人工整理候选引用",
        );
      }
      if (!evidence.use_in_introduction) {
        addIssue(
          fieldMap.label,
          referenceLabel,
          "intro-use",
          "用途标记",
          "候选文献尚未标记为 Introduction 用途",
          "如果该文献确实用于 Introduction，请在候选文献卡片勾选 Introduction 用途",
          item.cardTitle && item.evidenceIndex !== undefined
            ? {
                kind: "mark-introduction-use",
                cardTitle: item.cardTitle,
                evidenceIndex: item.evidenceIndex,
                evidence,
              }
            : undefined,
        );
      }
    });
  });

  return Array.from(issueMap.values());
}

function createEmptyIntroductionCitationBindings(): IntroductionCitationBindings {
  return {
    background_paragraph: [],
    gap_paragraph: [],
    objective_paragraph: [],
  };
}

function normalizeIntroductionCitationBindings(
  citationBindings?: Record<string, string[]> | null,
): IntroductionCitationBindings {
  const normalized = createEmptyIntroductionCitationBindings();
  if (!citationBindings) {
    return normalized;
  }

  introductionDraftFields.forEach((field) => {
    const keys = citationBindings[field];
    if (!Array.isArray(keys)) {
      return;
    }
    normalized[field] = keys
      .map((key) => key.trim())
      .filter((key, index, allKeys) => key.length > 0 && allKeys.indexOf(key) === index);
  });
  return normalized;
}

function mentorReferenceDedupKey(evidence: MentorEvidenceItem): string {
  if (evidence.doi?.trim()) {
    return `doi:${evidence.doi.trim().toLowerCase()}`;
  }
  if (evidence.pmid?.trim()) {
    return `pmid:${evidence.pmid.trim()}`;
  }

  return fallbackReferenceKeyForEvidence(evidence);
}

function mentorReferenceCompletenessScore(evidence: MentorEvidenceItem): number {
  return [
    evidence.vancouver_citation,
    evidence.citation_text,
    evidence.pmid,
    evidence.doi,
    evidence.authors?.length,
    evidence.journal,
    evidence.publication_year,
    evidence.volume,
    evidence.issue,
    evidence.page,
    evidence.external_url,
    evidence.crossref_url,
    evidence.full_text_checked,
  ].filter(Boolean).length;
}

function mentorReferenceManualCheckItems(evidence: MentorEvidenceItem): string[] {
  return [
    evidence.full_text_checked ? null : "尚未核对全文",
    evidence.vancouver_citation ? null : "缺 Vancouver 候选引用",
    evidence.pmid ? null : "缺 PMID",
    evidence.doi ? null : "缺 DOI",
    evidence.authors?.length ? null : "缺作者",
    evidence.journal ? null : "缺期刊",
    evidence.publication_year ? null : "缺年份",
    evidence.volume ? null : "缺卷",
    evidence.issue ? null : "缺期",
    evidence.page ? null : "缺页码/编号",
  ].filter(Boolean) as string[];
}

function mentorEvidenceKey(
  cardTitle: string,
  evidenceIndex: number,
  evidence?: MentorEvidenceItem,
): string {
  if (evidence?.pmid?.trim()) {
    return `pmid:${evidence.pmid.trim()}`;
  }
  if (evidence?.doi?.trim()) {
    return `doi:${evidence.doi.trim().toLowerCase()}`;
  }

  const fallbackKey = `${cardTitle}::${evidenceIndex}::${evidence?.search_query ?? ""}`
    .trim()
    .replace(/\s+/g, " ");
  return fallbackKey.slice(0, 240);
}

function applyMentorEvidenceReviews(
  report: MentorRecommendationResponse,
  reviewMap: Record<string, MentorEvidenceReview>,
): MentorRecommendationResponse {
  return {
    ...report,
    recommendations: report.recommendations.map((card) => ({
      ...card,
      evidence_items: card.evidence_items.map((evidence, evidenceIndex) => {
        const savedReview = reviewMap[mentorEvidenceKey(card.title, evidenceIndex, evidence)];
        return savedReview
          ? {
              ...evidence,
              review_status: savedReview.review_status,
              review_note: savedReview.review_note,
              reviewer: savedReview.reviewer,
              full_text_checked: savedReview.full_text_checked,
              use_in_introduction: savedReview.use_in_introduction,
              use_in_discussion: savedReview.use_in_discussion,
            }
          : evidence;
      }),
    })),
  };
}

type MentorEvidenceReviewPatch = Partial<
  Pick<
    MentorEvidenceReviewUpdate,
    | "review_status"
    | "review_note"
    | "reviewer"
    | "full_text_checked"
    | "use_in_introduction"
    | "use_in_discussion"
  >
>;

function mentorEvidenceReviewPayload(
  cardTitle: string,
  evidenceIndex: number,
  evidence: MentorEvidenceItem,
  reviewPatch: MentorEvidenceReviewPatch,
): MentorEvidenceReviewUpdate {
  return {
    evidence_key: mentorEvidenceKey(cardTitle, evidenceIndex, evidence),
    card_title: cardTitle,
    evidence_index: evidenceIndex,
    pmid: evidence.pmid ?? null,
    doi: evidence.doi ?? null,
    title: evidence.title ?? null,
    search_query: evidence.search_query,
    review_status: reviewPatch.review_status ?? evidence.review_status,
    review_note: reviewPatch.review_note ?? evidence.review_note ?? "",
    reviewer: reviewPatch.reviewer ?? evidence.reviewer ?? "",
    full_text_checked: reviewPatch.full_text_checked ?? evidence.full_text_checked ?? false,
    use_in_introduction: reviewPatch.use_in_introduction ?? evidence.use_in_introduction ?? false,
    use_in_discussion: reviewPatch.use_in_discussion ?? evidence.use_in_discussion ?? false,
  };
}

function createMentorFormState() {
  return {
    equipmentSummary: "",
    planningSystems: "",
    programmingLevel: "basic" as MentorProgrammingLevel,
    dataTypesText: "DICOM RTDose, RTStruct, RTPlan",
    weeklyHours: 4,
    publicationExperience: "",
    interestTopics: [] as string[],
  };
}

function createWriterIntroductionDraftForm(): WriterIntroductionDraftUpdate {
  return {
    background_paragraph: "",
    gap_paragraph: "",
    objective_paragraph: "",
    citation_bindings: createEmptyIntroductionCitationBindings(),
  };
}

function App() {
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [agents, setAgents] = useState<AgentProfile[]>([]);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [projectAccess, setProjectAccess] = useState<ProjectAccessPolicy | null>(null);
  const [selectedAgentId, setSelectedAgentId] = useState<AgentId>("study_planner");
  const [selectedProjectId, setSelectedProjectId] = useState<string>("project-a");
  const [mentorTrendSnapshot, setMentorTrendSnapshot] = useState<MentorTrendSnapshot | null>(null);
  const [mentorRecommendationReport, setMentorRecommendationReport] =
    useState<MentorRecommendationResponse | null>(null);
  const [mentorEvidenceReviews, setMentorEvidenceReviews] = useState<
    Record<string, MentorEvidenceReview>
  >({});
  const [mentorForm, setMentorForm] = useState(createMentorFormState);
  const [writerIntroductionDraft, setWriterIntroductionDraft] =
    useState<WriterIntroductionDraft | null>(null);
  const [writerIntroductionDraftForm, setWriterIntroductionDraftForm] =
    useState<WriterIntroductionDraftUpdate>(createWriterIntroductionDraftForm);
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
  const [workflowStatus, setWorkflowStatus] = useState<string | null>(null);
  const [workflowSummary, setWorkflowSummary] = useState<WorkflowSummary | null>(null);
  const [selectedGroupColumn, setSelectedGroupColumn] = useState("");
  const [selectedOutcomeColumns, setSelectedOutcomeColumns] = useState<string[]>([]);
  const [selectedChartStyle, setSelectedChartStyle] = useState<ChartStyleId>("journalBlue");
  const [isPairedFormalTest, setIsPairedFormalTest] = useState(false);
  const [pairedDataLayout, setPairedDataLayout] = useState<PairedDataLayout>("wide");
  const [pairedAnalysis, setPairedAnalysis] = useState<PairedAnalysis>("paired_t");
  const [pairedSubjectColumn, setPairedSubjectColumn] = useState("");
  const [pairedConditionColumn, setPairedConditionColumn] = useState("");
  const [pairedConditionA, setPairedConditionA] = useState("");
  const [pairedConditionB, setPairedConditionB] = useState("");
  const [pairedConditionList, setPairedConditionList] = useState("");
  const [multiplicityCorrection, setMultiplicityCorrection] =
    useState<MultiplicityCorrection>("holm");
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
  const [isMentorLoading, setIsMentorLoading] = useState(false);
  const [isMentorSubmitting, setIsMentorSubmitting] = useState(false);
  const [applyingMentorCardTitle, setApplyingMentorCardTitle] = useState<string | null>(null);
  const [pendingMentorProtocolCard, setPendingMentorProtocolCard] =
    useState<MentorRecommendationCard | null>(null);
  const [isCsvUploading, setIsCsvUploading] = useState(false);
  const [isStatisticsLoading, setIsStatisticsLoading] = useState(false);
  const [isFormalTestLoading, setIsFormalTestLoading] = useState(false);
  const [isWriterDrafting, setIsWriterDrafting] = useState(false);
  const [isWriterDraftLoading, setIsWriterDraftLoading] = useState(false);
  const [isWriterDraftSaving, setIsWriterDraftSaving] = useState(false);
  const [citationQualityNotice, setCitationQualityNotice] = useState<string | null>(null);
  const [updatingCitationQualityActionKey, setUpdatingCitationQualityActionKey] =
    useState<string | null>(null);
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

  const shouldShowMentorWorkspace = selectedAgentId === "mentor";
  const shouldShowProtocolWorkspace = selectedAgentId === "study_planner";
  const shouldShowDataWorkspace = selectedAgentId === "data_analyst";
  const shouldShowWriterWorkspace = selectedAgentId === "writer";
  const shouldShowReviewerWorkspace = selectedAgentId === "reviewer";

  const protocolHasContent = useMemo(() => hasProtocolContent(protocol), [protocol]);
  const protocolQualitySummary = useMemo(
    () => buildProtocolQualitySummary(protocol),
    [protocol],
  );
  const pendingMentorProtocolUpdate = useMemo(
    () =>
      pendingMentorProtocolCard
        ? mentorCardToProtocolUpdate(pendingMentorProtocolCard)
        : null,
    [pendingMentorProtocolCard],
  );

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

  const mentorTrendHighlights = useMemo(() => {
    return [...(mentorTrendSnapshot?.trends ?? [])]
      .sort((left, right) => {
        const leftValue = left.recent_counts[left.recent_counts.length - 1]?.publication_count ?? 0;
        const rightValue = right.recent_counts[right.recent_counts.length - 1]?.publication_count ?? 0;
        return rightValue - leftValue;
      })
      .slice(0, 4);
  }, [mentorTrendSnapshot]);

  const mentorCandidateReferences = useMemo<MentorCandidateReference[]>(() => {
    return (
      mentorRecommendationReport?.recommendations.flatMap((card) =>
        card.evidence_items
          .map((evidence, evidenceIndex) => ({ evidence, evidenceIndex }))
          .filter(({ evidence }) => evidence.review_status === "reviewed")
          .map(({ evidence, evidenceIndex }) => ({
            cardTitle: card.title,
            evidenceIndex,
            evidence,
          })),
      ) ?? []
    );
  }, [mentorRecommendationReport]);

  const mentorDedupedCandidateReferences = useMemo<MentorDedupedCandidateReference[]>(() => {
    const referencesByKey = new Map<string, MentorDedupedCandidateReference>();

    mentorCandidateReferences.forEach(({ cardTitle, evidence }) => {
      const key = mentorReferenceDedupKey(evidence);
      const current = referencesByKey.get(key);
      if (!current) {
        referencesByKey.set(key, {
          cardTitles: [cardTitle],
          duplicateCount: 1,
          evidence,
        });
        return;
      }

      current.duplicateCount += 1;
      if (!current.cardTitles.includes(cardTitle)) {
        current.cardTitles.push(cardTitle);
      }
      if (mentorReferenceCompletenessScore(evidence) > mentorReferenceCompletenessScore(current.evidence)) {
        current.evidence = evidence;
      }
    });

    return Array.from(referencesByKey.values());
  }, [mentorCandidateReferences]);

  const writerOutlineDraft = useMemo(() => {
    if (!mentorCandidateReferences.length) {
      return null;
    }

    const referenceTitles = mentorCandidateReferences
      .map(({ evidence }) => evidence.title ?? evidence.evidence_summary)
      .slice(0, 5);
    const introductionParagraphs = [
      {
        title: "背景段",
        purpose: "交代研究方向在放疗物理流程、计划质量、质控或临床执行中的现实意义。",
        writingCue: referenceTitles.length
          ? `可从这些确认可用文献切入背景：${referenceTitles.slice(0, 3).join("；")}。`
          : "先用确认可用文献概括该方向为什么值得关注。",
      },
      {
        title: "研究空白段",
        purpose: "指出既有研究尚未充分回答的本中心、本设备、本流程或本数据问题。",
        writingCue: "只描述候选文献能支持的研究空白；不要写成系统综述结论或夸大为所有研究一致。",
      },
      {
        title: "研究目的段",
        purpose: "把背景和空白收束到本研究的具体问题、对象和主要终点。",
        writingCue: protocol?.research_question
          ? `可收束到当前研究问题：${protocol.research_question}`
          : "补充 Project Protocol 后，再把本段收束到明确研究问题和主要终点。",
      },
    ];
    return {
      introductionParagraphs,
      referenceTitles,
      discussionDeferredNote:
        "Discussion 暂不自动生成；请等待 Dr. Data Lin 完成正式结果确认后，再基于真实发现生成解释、对照和局限性段落。",
      remainingChecks: [
        "阅读全文确认候选文献是否真正支持拟写观点。",
        "补充近 5-7 年同主题研究，确认是否存在更高质量证据。",
        "在正式写作前核对 PMID、DOI、期刊名和引用格式。",
      ],
    };
  }, [mentorCandidateReferences, protocol]);

  const writerMethodsResultsDraft = useMemo(
    () => buildWriterMethodsResultsDraft(qualityReport, statisticsReport),
    [qualityReport, statisticsReport],
  );

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

  const pairedColumnOptions = useMemo(() => {
    return qualityReport?.columns.filter((column) => column.inferred_type !== "empty") ?? [];
  }, [qualityReport]);

  const privacyReport = qualityReport?.privacy_report ?? null;
  const hasBlockingPrivacyRisk = privacyReport?.risk_level === "red";
  const canEditSelectedProject = projectAccess?.can_edit ?? true;
  const introductionCitationUsages = useMemo(
    () => extractIntroductionCitationUsages(writerIntroductionDraftForm),
    [writerIntroductionDraftForm],
  );
  const introductionHasText = introductionDraftFields.some(
    (field) => writerIntroductionDraftForm[field].trim().length > 0,
  );
  const introductionSectionsWithoutCitation = useMemo(() => {
    const citationBindings = normalizeIntroductionCitationBindings(
      writerIntroductionDraftForm.citation_bindings,
    );
    return introductionDraftFields
      .filter((field) => writerIntroductionDraftForm[field].trim())
      .filter(
        (field) =>
          !/\b(?:DOI\s+[^\]\s；;，,]+|PMID\s+\d+)/i.test(writerIntroductionDraftForm[field]) &&
          citationBindings[field].length === 0,
      )
      .map((field) => introductionDraftFieldLabels[field]);
  }, [writerIntroductionDraftForm]);
  const introductionUsedReferences = useMemo<IntroductionUsedReference[]>(() => {
    return introductionCitationUsages.map((usage) => {
      const matchedReference = findCandidateReferenceForUsage(usage, mentorCandidateReferences);
      return {
        usage,
        cardTitle: matchedReference?.cardTitle,
        evidenceIndex: matchedReference?.evidenceIndex,
        evidence: matchedReference?.evidence,
      };
    });
  }, [introductionCitationUsages, mentorCandidateReferences]);
  const introductionFieldCitationMaps = useMemo(
    () => buildIntroductionFieldCitationMaps(writerIntroductionDraftForm, mentorCandidateReferences),
    [writerIntroductionDraftForm, mentorCandidateReferences],
  );
  const introductionCitationQualityIssues = useMemo(
    () => buildIntroductionCitationQualityIssues(introductionFieldCitationMaps),
    [introductionFieldCitationMaps],
  );
  const reviewerChecks = useMemo(
    () =>
      buildReviewerChecks({
        protocolHasContent,
        protocol,
        qualityReport,
        statisticsReport,
        writerMethodsResultsDraft,
        writerIntroductionDraftForm,
        citationIssueCount: introductionCitationQualityIssues.length,
        candidateReferenceCount: mentorCandidateReferences.length,
        reminderSummary,
      }),
    [
      protocolHasContent,
      protocol,
      qualityReport,
      statisticsReport,
      writerMethodsResultsDraft,
      writerIntroductionDraftForm,
      introductionCitationQualityIssues.length,
      mentorCandidateReferences.length,
      reminderSummary,
    ],
  );
  const pipelineSteps = useMemo(
    () =>
      buildPipelineSteps({
        candidateReferenceCount: mentorCandidateReferences.length,
        protocolHasContent,
        qualityReport,
        statisticsReport,
        writerMethodsResultsDraft,
        introductionHasText,
        reviewerChecks,
      }),
    [
      mentorCandidateReferences.length,
      protocolHasContent,
      qualityReport,
      statisticsReport,
      writerMethodsResultsDraft,
      introductionHasText,
      reviewerChecks,
    ],
  );
  const formalTestReport = statisticsReport?.formal_test_report ?? null;
  const isFormalTestReady = useMemo(() => {
    return (
      formalTestConfirmation.confirmed_by.trim().length > 0 &&
      formalTestConfirmationItems.every((item) => formalTestConfirmation[item.key])
    );
  }, [formalTestConfirmation]);
  const parsedPairedConditions = useMemo(
    () =>
      pairedConditionList
        .split(",")
        .map((condition) => condition.trim())
        .filter(Boolean),
    [pairedConditionList],
  );
  const hasDuplicatePairedConditions =
    parsedPairedConditions.length !== new Set(parsedPairedConditions).size;
  const isPairedFormalTestInvalid =
    isPairedFormalTest &&
    (pairedDataLayout === "wide"
      ? selectedOutcomeColumns.length !== 2 || pairedAnalysis !== "paired_t"
      : selectedOutcomeColumns.length !== 1 ||
        !pairedSubjectColumn ||
        !pairedConditionColumn ||
        (pairedAnalysis === "friedman" || pairedAnalysis === "rm_anova"
          ? parsedPairedConditions.length < 3 || hasDuplicatePairedConditions
          : !pairedConditionA.trim() ||
            !pairedConditionB.trim() ||
            pairedConditionA.trim() === pairedConditionB.trim()));

  function resetPairedFormalTestSettings() {
    setIsPairedFormalTest(false);
    setPairedDataLayout("wide");
    setPairedAnalysis("paired_t");
    setPairedSubjectColumn("");
    setPairedConditionColumn("");
    setPairedConditionA("");
    setPairedConditionB("");
    setPairedConditionList("");
    setMultiplicityCorrection("holm");
  }

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
    setWriterIntroductionDraft(null);
    setWriterIntroductionDraftForm(createWriterIntroductionDraftForm());
    setUploadedCsvFile(null);
    setSelectedGroupColumn("");
    setSelectedOutcomeColumns([]);
    resetPairedFormalTestSettings();
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

    async function loadMentorEvidenceReviews() {
      if (!selectedProjectId) {
        setMentorEvidenceReviews({});
        return;
      }

      try {
        const reviews = await getMentorEvidenceReviews(selectedProjectId);
        if (isCurrent) {
          const reviewMap = Object.fromEntries(
            reviews.map((review) => [review.evidence_key, review]),
          );
          setMentorEvidenceReviews(reviewMap);
          setMentorRecommendationReport((current) =>
            current ? applyMentorEvidenceReviews(current, reviewMap) : current,
          );
        }
      } catch (caughtError) {
        if (isCurrent) {
          setError(caughtError instanceof Error ? caughtError.message : "Mentor 文献复核记录读取失败。");
          setMentorEvidenceReviews({});
        }
      }
    }

    loadMentorEvidenceReviews();

    return () => {
      isCurrent = false;
    };
  }, [selectedProjectId]);

  useEffect(() => {
    let isCurrent = true;

    async function loadWriterIntroductionDraft() {
      if (!selectedProjectId) {
        setWriterIntroductionDraft(null);
        setWriterIntroductionDraftForm(createWriterIntroductionDraftForm());
        return;
      }

      setIsWriterDraftLoading(true);
      try {
        const draft = await getWriterIntroductionDraft(selectedProjectId);
        if (isCurrent) {
          setWriterIntroductionDraft(draft);
          setWriterIntroductionDraftForm({
            background_paragraph: draft.background_paragraph,
            gap_paragraph: draft.gap_paragraph,
            objective_paragraph: draft.objective_paragraph,
            citation_bindings: normalizeIntroductionCitationBindings(draft.citation_bindings),
          });
        }
      } catch (caughtError) {
        if (isCurrent) {
          setWriterIntroductionDraft(null);
          setWriterIntroductionDraftForm(createWriterIntroductionDraftForm());
          setError(caughtError instanceof Error ? caughtError.message : "Introduction 草稿读取失败。");
        }
      } finally {
        if (isCurrent) {
          setIsWriterDraftLoading(false);
        }
      }
    }

    loadWriterIntroductionDraft();

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
    setIsMentorLoading(true);
    setError(null);

    try {
      const [dashboardData, projectData, agentData, userData, mentorTrendData] = await Promise.all([
        getDashboard(),
        getProjects(),
        getAgents(),
        getCurrentUser(),
        getMentorTrendSnapshot(),
      ]);
      setDashboard(dashboardData);
      setProjects(projectData);
      setAgents(agentData);
      setCurrentUser(userData);
      setMentorTrendSnapshot(mentorTrendData);
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
      setIsMentorLoading(false);
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

  async function handleMentorSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isMentorSubmitting) {
      return;
    }

    setIsMentorSubmitting(true);
    setError(null);

    try {
      const report = await getMentorRecommendations({
        equipment_summary: mentorForm.equipmentSummary,
        planning_systems: mentorForm.planningSystems,
        programming_level: mentorForm.programmingLevel,
        data_types: mentorForm.dataTypesText
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        weekly_hours: mentorForm.weeklyHours,
        publication_experience: mentorForm.publicationExperience,
        interest_topics: mentorForm.interestTopics,
      });
      setMentorRecommendationReport(applyMentorEvidenceReviews(report, mentorEvidenceReviews));
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "虚拟导师推荐生成失败。");
    } finally {
      setIsMentorSubmitting(false);
    }
  }

  function handleMentorInterestToggle(topicId: string) {
    setMentorForm((current) => ({
      ...current,
      interestTopics: current.interestTopics.includes(topicId)
        ? current.interestTopics.filter((item) => item !== topicId)
        : [...current.interestTopics, topicId],
    }));
  }

  function updateMentorEvidenceReviewInReport(
    cardTitle: string,
    evidenceIndex: number,
    reviewPatch: MentorEvidenceReviewPatch,
  ) {
    setMentorRecommendationReport((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        recommendations: current.recommendations.map((card) => {
          if (card.title !== cardTitle) {
            return card;
          }
          return {
            ...card,
            evidence_items: card.evidence_items.map((evidence, index) =>
              index === evidenceIndex ? { ...evidence, ...reviewPatch } : evidence,
            ),
          };
        }),
      };
    });
  }

  async function handleMentorEvidenceReview(
    cardTitle: string,
    evidenceIndex: number,
    evidence: MentorEvidenceItem,
    reviewPatch: MentorEvidenceReviewPatch,
  ) {
    const nextPatch = { ...reviewPatch };
    const nextStatus = nextPatch.review_status ?? evidence.review_status;
    if (
      nextStatus !== "unreviewed" &&
      !nextPatch.reviewer &&
      !evidence.reviewer &&
      currentUser?.display_name
    ) {
      nextPatch.reviewer = currentUser.display_name;
    }

    const reviewPayload = mentorEvidenceReviewPayload(cardTitle, evidenceIndex, evidence, nextPatch);

    updateMentorEvidenceReviewInReport(cardTitle, evidenceIndex, nextPatch);

    if (!selectedProjectId) {
      return true;
    }

    try {
      const savedReview = await saveMentorEvidenceReview(selectedProjectId, reviewPayload);
      setMentorEvidenceReviews((current) => ({
        ...current,
        [savedReview.evidence_key]: savedReview,
      }));
      return true;
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Mentor 文献复核状态保存失败。");
      return false;
    }
  }

  function handleDownloadMentorBrief() {
    if (!mentorRecommendationReport) {
      return;
    }

    const trendLines = mentorTrendSnapshot?.trends.map(
      (trend) => `- ${trend.title}：${trend.summary} ${trend.forecast_note}`,
    ) ?? [];
    const content = [
      "# 研究方向建议书",
      "",
      `生成时间：${new Date().toLocaleString("zh-CN")}`,
      selectedProject ? `关联项目：${selectedProject.name} / ${selectedProject.title}` : "关联项目：未指定",
      "",
      "## 画像摘要",
      mentorRecommendationReport.profile_summary,
      "",
      "## 资源诊断",
      ...mentorRecommendationReport.resource_diagnosis.map((item) => `- ${item}`),
      "",
      "## 匹配优势",
      ...mentorRecommendationReport.matched_strengths.map((item) => `- ${item}`),
      "",
      "## 趋势摘要",
      ...(trendLines.length ? trendLines.slice(0, 6) : ["- 当前建议结合虚拟导师面板中的趋势卡片一并查看。"]),
      "",
      "## 课题推荐卡",
      ...mentorRecommendationReport.recommendations.flatMap((item) => [
        `### ${item.title}`,
        `- 研究问题：${item.research_question}`,
        `- 为什么适合：${item.why_fit}`,
        `- 数据路径：${item.data_pathway}`,
        `- 方法路线：${item.methods_route}`,
        `- 统计建议：${item.statistical_plan}`,
        `- 创新点：${item.innovation_point}`,
        `- 可行性：${item.feasibility_note}`,
        "- 风险提示：",
        ...item.risk_flags.map((risk) => `  - ${risk}`),
        "- 推荐依据：",
        ...item.evidence_items.flatMap((evidence) => [
          `  - 状态：${formatMentorEvidenceStatus(evidence.evidence_status)}`,
          evidence.retrieved_at ? `    - 检索时间：${evidence.retrieved_at}` : "    - 检索时间：未进行真实外部检索",
          evidence.external_url ? `    - 外部链接：${evidence.external_url}` : "    - 外部链接：待真实检索后补充",
          evidence.crossref_url ? `    - Crossref/DOI 链接：${evidence.crossref_url}` : "    - Crossref/DOI 链接：待补充",
          `    - 复核状态：${formatMentorReviewStatus(evidence.review_status)}`,
          `    - 复核人：${evidence.reviewer?.trim() || "待补充"}`,
          `    - 全文核对：${evidence.full_text_checked ? "是" : "否"}`,
          `    - 引用用途：${formatMentorReviewUsage(evidence)}`,
          `    - 复核备注：${evidence.review_note?.trim() || "无"}`,
          evidence.pmid ? `    - PMID：${evidence.pmid}` : "    - PMID：待真实检索后补充",
          evidence.title ? `    - 题名：${evidence.title}` : "    - 题名：待真实检索后补充",
          evidence.authors?.length ? `    - 作者：${evidence.authors.join(", ")}` : "    - 作者：待真实检索后补充",
          evidence.journal ? `    - 期刊：${evidence.journal}` : "    - 期刊：待真实检索后补充",
          evidence.publication_year ? `    - 年份：${evidence.publication_year}` : "    - 年份：待真实检索后补充",
          evidence.volume ? `    - 卷：${evidence.volume}` : "    - 卷：待真实检索后补充",
          evidence.issue ? `    - 期：${evidence.issue}` : "    - 期：待真实检索后补充",
          evidence.page ? `    - 页码/编号：${evidence.page}` : "    - 页码/编号：待真实检索后补充",
          evidence.doi ? `    - DOI：${evidence.doi}` : "    - DOI：待真实检索后补充",
          evidence.citation_text ? `    - 候选引用草稿：${evidence.citation_text}` : "    - 候选引用草稿：待补充",
          evidence.vancouver_citation
            ? `    - Vancouver 候选引用：${evidence.vancouver_citation}`
            : "    - Vancouver 候选引用：待补充",
          evidence.publication_types.length
            ? `    - 文献类型：${evidence.publication_types.join(" / ")}`
            : "    - 文献类型：待真实检索后补充",
          `  - 检索式：${evidence.search_query}`,
          `    - 摘要：${evidence.evidence_summary}`,
          `    - 信号：${evidence.recommendation_signal}`,
          `    - 局限：${evidence.limitation}`,
        ]),
        "- 首轮里程碑：",
        ...item.first_milestones.map((milestone) => `  - ${milestone}`),
        `- 建议期刊：${item.target_journals.join(" / ")}`,
        "",
      ]),
      "## 候选引用清单",
      ...(mentorCandidateReferences.length
        ? mentorCandidateReferences.flatMap(({ cardTitle, evidence }, index) => [
            `${index + 1}. ${evidence.title ?? evidence.evidence_summary}`,
            `   - 来源课题：${cardTitle}`,
            evidence.authors?.length ? `   - 作者：${evidence.authors.join(", ")}` : "   - 作者：待补充",
            evidence.journal ? `   - 期刊：${evidence.journal}` : "   - 期刊：待补充",
            evidence.publication_year ? `   - 年份：${evidence.publication_year}` : "   - 年份：待补充",
            evidence.volume ? `   - 卷：${evidence.volume}` : "   - 卷：待补充",
            evidence.issue ? `   - 期：${evidence.issue}` : "   - 期：待补充",
            evidence.page ? `   - 页码/编号：${evidence.page}` : "   - 页码/编号：待补充",
            evidence.pmid ? `   - PMID：${evidence.pmid}` : "   - PMID：待补充",
            evidence.doi ? `   - DOI：${evidence.doi}` : "   - DOI：待补充",
            evidence.external_url ? `   - 链接：${evidence.external_url}` : "   - 链接：待补充",
            evidence.crossref_url ? `   - Crossref/DOI 链接：${evidence.crossref_url}` : "   - Crossref/DOI 链接：待补充",
            evidence.citation_text ? `   - 候选引用草稿：${evidence.citation_text}` : "   - 候选引用草稿：待补充",
            evidence.vancouver_citation
              ? `   - Vancouver 候选引用：${evidence.vancouver_citation}`
              : "   - Vancouver 候选引用：待补充",
            `   - 复核状态：${formatMentorReviewStatus(evidence.review_status)}`,
            `   - 复核人：${evidence.reviewer?.trim() || "待补充"}`,
            `   - 全文核对：${evidence.full_text_checked ? "是" : "否"}`,
            `   - 引用用途：${formatMentorReviewUsage(evidence)}`,
            `   - 复核备注：${evidence.review_note?.trim() || "无"}`,
            "",
          ])
        : ["- 暂无确认可用的候选引用。"]),
      "",
      "## 下一步行动",
      ...mentorRecommendationReport.next_steps.map((item) => `- ${item}`),
      "",
    ].join("\n");

    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    try {
      link.href = url;
      link.download = "research-direction-brief.md";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  function handleDownloadVancouverReferences() {
    if (!mentorDedupedCandidateReferences.length) {
      return;
    }

    const manualCheckLines = mentorDedupedCandidateReferences.flatMap(({ evidence }, index) => {
      const checkItems = mentorReferenceManualCheckItems(evidence);
      return checkItems.length
        ? [`- ${index + 1}. ${evidence.title ?? evidence.evidence_summary}：${checkItems.join("；")}`]
        : [];
    });
    const content = [
      "# Vancouver 候选引用清单",
      "",
      `导出时间：${new Date().toLocaleString("zh-CN")}`,
      selectedProject ? `关联项目：${selectedProject.name} / ${selectedProject.title}` : "关联项目：未指定",
      `原始确认可用候选数：${mentorCandidateReferences.length}`,
      `去重后候选引用数：${mentorDedupedCandidateReferences.length}`,
      "",
      "## 使用边界",
      "- 本文件只汇总已在 Mentor 中标记为“确认可用”的候选文献。",
      "- Vancouver 候选引用不是最终投稿格式；正式投稿前仍需核对全文、DOI 页面、期刊缩写、卷期页码和目标期刊格式。",
      "- 当前清单不等同于系统综述、质量评价或引用真实性复核结论。",
      "",
      "## References",
      ...mentorDedupedCandidateReferences.flatMap(({ cardTitles, duplicateCount, evidence }, index) => {
        const checkItems = mentorReferenceManualCheckItems(evidence);
        return [
          `${index + 1}. ${evidence.vancouver_citation || evidence.citation_text || evidence.title || evidence.evidence_summary}`,
          `   - 来源课题：${cardTitles.join(" / ")}${duplicateCount > 1 ? `（合并 ${duplicateCount} 条候选）` : ""}`,
          evidence.title ? `   - 题名：${evidence.title}` : "   - 题名：待补充",
          evidence.authors?.length ? `   - 作者：${evidence.authors.join(", ")}` : "   - 作者：待补充",
          evidence.journal ? `   - 期刊：${evidence.journal}` : "   - 期刊：待补充",
          evidence.publication_year ? `   - 年份：${evidence.publication_year}` : "   - 年份：待补充",
          evidence.volume ? `   - 卷：${evidence.volume}` : "   - 卷：待补充",
          evidence.issue ? `   - 期：${evidence.issue}` : "   - 期：待补充",
          evidence.page ? `   - 页码/编号：${evidence.page}` : "   - 页码/编号：待补充",
          evidence.pmid ? `   - PMID：${evidence.pmid}` : "   - PMID：待补充",
          evidence.doi ? `   - DOI：${evidence.doi}` : "   - DOI：待补充",
          evidence.external_url ? `   - PubMed：${evidence.external_url}` : "   - PubMed：待补充",
          evidence.crossref_url ? `   - Crossref/DOI：${evidence.crossref_url}` : "   - Crossref/DOI：待补充",
          `   - 全文核对：${evidence.full_text_checked ? "是" : "否"}`,
          `   - 引用用途：${formatMentorReviewUsage(evidence)}`,
          `   - 复核人：${evidence.reviewer?.trim() || "待补充"}`,
          `   - 复核备注：${evidence.review_note?.trim() || "无"}`,
          `   - 待人工核对：${checkItems.length ? checkItems.join("；") : "暂无明显缺项，仍需按目标期刊复核"}`,
          "",
        ];
      }),
      "## 待人工核对总表",
      ...(manualCheckLines.length
        ? manualCheckLines
        : ["- 暂无字段缺项；仍需人工核对全文、DOI 页面和目标期刊格式。"]),
      "",
    ].join("\n");

    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    try {
      link.href = url;
      link.download = "references-vancouver.md";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  function handleDownloadWriterOutline() {
    if (!writerOutlineDraft) {
      return;
    }

    const content = [
      "# Alex Writer 写作提纲",
      "",
      `生成时间：${new Date().toLocaleString("zh-CN")}`,
      selectedProject ? `关联项目：${selectedProject.name} / ${selectedProject.title}` : "关联项目：未指定",
      protocol?.research_question ? `研究问题：${protocol.research_question}` : "研究问题：待补充",
      protocol?.primary_endpoint ? `主要终点：${protocol.primary_endpoint}` : "主要终点：待补充",
      "",
      "## Introduction 段落骨架",
      ...writerOutlineDraft.introductionParagraphs.flatMap((paragraph) => [
        `### ${paragraph.title}`,
        `- 写作目的：${paragraph.purpose}`,
        `- 写作提示：${paragraph.writingCue}`,
        "",
      ]),
      "",
      "## Introduction 可编辑草稿",
      "### 背景段",
      writerIntroductionDraftForm.background_paragraph.trim() ||
        writerOutlineDraft.introductionParagraphs[0]?.writingCue ||
        "待撰写",
      "",
      "### 研究空白段",
      writerIntroductionDraftForm.gap_paragraph.trim() ||
        writerOutlineDraft.introductionParagraphs[1]?.writingCue ||
        "待撰写",
      "",
      "### 研究目的段",
      writerIntroductionDraftForm.objective_paragraph.trim() ||
        writerOutlineDraft.introductionParagraphs[2]?.writingCue ||
        "待撰写",
      "",
      "## Discussion",
      writerOutlineDraft.discussionDeferredNote,
      "",
      "## 候选引用清单",
      ...mentorCandidateReferences.flatMap(({ cardTitle, evidence }, index) => [
        `${index + 1}. ${evidence.title ?? evidence.evidence_summary}`,
        `   - 来源课题：${cardTitle}`,
        evidence.authors?.length ? `   - 作者：${evidence.authors.join(", ")}` : "   - 作者：待补充",
        evidence.journal ? `   - 期刊：${evidence.journal}` : "   - 期刊：待补充",
        evidence.publication_year ? `   - 年份：${evidence.publication_year}` : "   - 年份：待补充",
        evidence.volume ? `   - 卷：${evidence.volume}` : "   - 卷：待补充",
        evidence.issue ? `   - 期：${evidence.issue}` : "   - 期：待补充",
        evidence.page ? `   - 页码/编号：${evidence.page}` : "   - 页码/编号：待补充",
        evidence.pmid ? `   - PMID：${evidence.pmid}` : "   - PMID：待补充",
        evidence.doi ? `   - DOI：${evidence.doi}` : "   - DOI：待补充",
        evidence.external_url ? `   - 链接：${evidence.external_url}` : "   - 链接：待补充",
        evidence.crossref_url ? `   - Crossref/DOI 链接：${evidence.crossref_url}` : "   - Crossref/DOI 链接：待补充",
        evidence.citation_text ? `   - 候选引用草稿：${evidence.citation_text}` : "   - 候选引用草稿：待补充",
        evidence.vancouver_citation
          ? `   - Vancouver 候选引用：${evidence.vancouver_citation}`
          : "   - Vancouver 候选引用：待补充",
        `   - 全文核对：${evidence.full_text_checked ? "是" : "否"}`,
        `   - 引用用途：${formatMentorReviewUsage(evidence)}`,
        `   - 复核备注：${evidence.review_note?.trim() || "无"}`,
        "",
      ]),
      "## 写作前检查清单",
      ...writerOutlineDraft.remainingChecks.map((item) => `- ${item}`),
      "",
    ].join("\n");

    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    try {
      link.href = url;
      link.download = "alex-writer-outline.md";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  function handleDownloadIntroductionDraft() {
    const duplicateUsages = introductionCitationUsages.filter((usage) => usage.count > 1);
    const matchedReferences = introductionUsedReferences.filter((item) => item.evidence);
    const unmatchedReferences = introductionUsedReferences.filter((item) => !item.evidence);
    const unmatchedManualBindingKeys = introductionFieldCitationMaps.flatMap((fieldMap) =>
      fieldMap.unmatchedBindingKeys.map((key) => ({
        fieldLabel: fieldMap.label,
        key,
      })),
    );
    const content = [
      "# Introduction 草稿",
      "",
      `导出时间：${new Date().toLocaleString("zh-CN")}`,
      selectedProject ? `关联项目：${selectedProject.name} / ${selectedProject.title}` : "关联项目：未指定",
      protocol?.research_question ? `研究问题：${protocol.research_question}` : "研究问题：待补充",
      protocol?.primary_endpoint ? `主要终点：${protocol.primary_endpoint}` : "主要终点：待补充",
      "",
      "## 正文草稿",
      "",
      "### 背景段",
      writerIntroductionDraftForm.background_paragraph.trim() || "待撰写",
      "",
      "### 研究空白段",
      writerIntroductionDraftForm.gap_paragraph.trim() || "待撰写",
      "",
      "### 研究目的段",
      writerIntroductionDraftForm.objective_paragraph.trim() || "待撰写",
      "",
      "## 已使用候选引用",
      ...(matchedReferences.length
        ? matchedReferences.flatMap((item, index) => {
            const evidence = item.evidence;
            return [
              `${index + 1}. ${
                evidence?.vancouver_citation || evidence?.citation_text || evidence?.title || item.usage.label
              }`,
              `   - 追溯标记：${item.usage.label}`,
              `   - 出现位置：${item.usage.sections.join(" / ")}`,
              `   - 出现次数：${item.usage.count}`,
              item.cardTitle ? `   - 来源课题：${item.cardTitle}` : "   - 来源课题：待补充",
              evidence?.pmid ? `   - PMID：${evidence.pmid}` : "   - PMID：待补充",
              evidence?.doi ? `   - DOI：${evidence.doi}` : "   - DOI：待补充",
              evidence?.external_url ? `   - PubMed：${evidence.external_url}` : "   - PubMed：待补充",
              evidence?.crossref_url
                ? `   - Crossref/DOI：${evidence.crossref_url}`
                : "   - Crossref/DOI：待补充",
              "",
            ];
          })
        : ["- 当前草稿中没有匹配到候选引用。"]),
      "",
      "## 字段级引用映射",
      ...introductionFieldCitationMaps.flatMap((fieldMap) => [
        `### ${fieldMap.label}`,
        fieldMap.hasText ? "- 段落状态：已有文字" : "- 段落状态：待撰写",
        fieldMap.missingTrace
          ? "- 追溯状态：已有文字但尚无 PMID / DOI 追溯标记"
          : `- 追溯标记数：${fieldMap.usages.length}`,
        ...(fieldMap.matchedReferences.length
          ? fieldMap.matchedReferences.flatMap((item, index) => {
              const evidence = item.evidence;
              return [
                `${index + 1}. ${item.usage.label} → ${
                  evidence?.vancouver_citation || evidence?.citation_text || evidence?.title || "待补充题名"
                }`,
                item.cardTitle ? `   - 来源课题：${item.cardTitle}` : "   - 来源课题：待补充",
                `   - 出现次数：${item.usage.count}`,
                `   - 全文核对：${evidence?.full_text_checked ? "是" : "否"}`,
                `   - 已标记用于 Introduction：${evidence?.use_in_introduction ? "是" : "否"}`,
                evidence?.pmid ? `   - PMID：${evidence.pmid}` : "   - PMID：待补充",
                evidence?.doi ? `   - DOI：${evidence.doi}` : "   - DOI：待补充",
              ];
            })
          : []),
        ...(fieldMap.manualReferences.length
          ? fieldMap.manualReferences.flatMap((item, index) => {
              const evidence = item.evidence;
              return [
                `手动绑定 ${index + 1}. ${item.usage.label} → ${
                  evidence?.vancouver_citation || evidence?.citation_text || evidence?.title || "待补充题名"
                }`,
                item.cardTitle ? `   - 来源课题：${item.cardTitle}` : "   - 来源课题：待补充",
                `   - 全文核对：${evidence?.full_text_checked ? "是" : "否"}`,
                `   - 已标记用于 Introduction：${evidence?.use_in_introduction ? "是" : "否"}`,
                evidence?.pmid ? `   - PMID：${evidence.pmid}` : "   - PMID：待补充",
                evidence?.doi ? `   - DOI：${evidence.doi}` : "   - DOI：待补充",
              ];
            })
          : []),
        ...(fieldMap.unmatchedUsages.length
          ? fieldMap.unmatchedUsages.map(
              (usage) => `- ${usage.label} 未匹配到当前候选引用列表，需人工核对。`,
            )
          : []),
        ...(fieldMap.unmatchedBindingKeys.length
          ? fieldMap.unmatchedBindingKeys.map(
              (key) => `- 手动绑定 ${formatCitationBindingKey(key)} 未匹配到当前候选引用列表，需人工核对。`,
            )
          : []),
        ...(!fieldMap.usages.length &&
        !fieldMap.manualReferences.length &&
        !fieldMap.unmatchedBindingKeys.length
          ? ["- 暂无可映射引用。"]
          : []),
        "",
      ]),
      "",
      "## 引用质控摘要",
      ...(introductionCitationQualityIssues.length
        ? introductionCitationQualityIssues.map(
            (issue) =>
              `- [${issue.category}] ${issue.fieldLabel} / ${issue.referenceLabel}：${issue.message}。建议：${issue.suggestion}。`,
          )
        : ["- 当前字段级引用映射未发现引用质控风险。"]),
      "",
      "## 待人工核对",
      ...(introductionSectionsWithoutCitation.length
        ? [`- ${introductionSectionsWithoutCitation.join("、")}已有文字，但尚无 PMID / DOI 追溯标记或手动绑定。`]
        : ["- 所有已有文字的段落都包含至少一个 PMID / DOI 追溯标记或手动绑定。"]),
      ...(duplicateUsages.length
        ? duplicateUsages.map(
            (usage) =>
              `- ${usage.label} 出现 ${usage.count} 次，位于 ${usage.sections.join(" / ")}，需人工确认是否重复使用。`,
          )
        : ["- 未发现重复 PMID / DOI 标记。"]),
      ...(unmatchedReferences.length
        ? unmatchedReferences.map(
            (item) =>
              `- ${item.usage.label} 在草稿中出现，但当前候选引用列表未匹配到对应文献，请人工核对。`,
          )
        : ["- 草稿中的 PMID / DOI 标记均已匹配到当前候选引用列表。"]),
      ...(unmatchedManualBindingKeys.length
        ? unmatchedManualBindingKeys.map(
            (item) =>
              `- ${item.fieldLabel} 手动绑定 ${formatCitationBindingKey(item.key)}，但当前候选引用列表未匹配到对应文献，请人工核对。`,
          )
        : ["- 手动绑定的引用均已匹配到当前候选引用列表。"]),
      "- 候选 Vancouver 引用不是最终投稿格式，正式投稿前仍需核对全文、DOI 页面和目标期刊格式。",
      "",
    ].join("\n");

    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    try {
      link.href = url;
      link.download = "introduction-draft.md";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  function handleDownloadMethodsResultsDraft() {
    if (!writerMethodsResultsDraft) {
      return;
    }

    const content = [
      "# Methods / Results 草稿",
      "",
      `导出时间：${new Date().toLocaleString("zh-CN")}`,
      selectedProject ? `关联项目：${selectedProject.name} / ${selectedProject.title}` : "关联项目：未指定",
      protocol?.research_question ? `研究问题：${protocol.research_question}` : "研究问题：待补充",
      qualityReport ? `数据文件：${qualityReport.file_name}` : "数据文件：待补充",
      "",
      "## Methods",
      ...writerMethodsResultsDraft.methodsParagraphs.flatMap((paragraph) => [paragraph, ""]),
      "## Results",
      ...writerMethodsResultsDraft.resultsParagraphs.flatMap((paragraph) => [paragraph, ""]),
      "## 正式检验摘要",
      ...writerMethodsResultsDraft.formalTestLines.map((line) => `- ${line}`),
      "",
      "## 图表与展示建议",
      ...(writerMethodsResultsDraft.chartLines.length
        ? writerMethodsResultsDraft.chartLines.map((line) => `- ${line}`)
        : ["- 暂无可展示图表摘要。"]),
      "",
      "## 待补充 / 不可编造",
      ...(writerMethodsResultsDraft.missingItems.length
        ? writerMethodsResultsDraft.missingItems.map((item) => `- ${item}`)
        : ["- 当前没有系统识别出的阻断项；正式投稿前仍需人工复核数据、统计和引用。"]),
      "",
      "## 使用边界",
      "- 本草稿来自 Data Lin 的结构化质控和统计结果，不等同于最终论文正文。",
      "- 未执行正式检验时，不得添加 P 值、置信区间或显著性表述。",
      "- 正式论文需要用真实课题数据、伦理信息和目标期刊格式重新核对。",
      "",
    ].join("\n");

    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    try {
      link.href = url;
      link.download = "methods-results-draft.md";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  function handleDownloadReviewerReport() {
    const highRiskCount = reviewerChecks.filter((item) => item.severity === "red").length;
    const reviewNeededCount = reviewerChecks.filter((item) => item.severity === "orange").length;
    const passedCount = reviewerChecks.filter((item) => item.severity === "green").length;
    const content = [
      "# 投稿前审稿清单",
      "",
      `导出时间：${new Date().toLocaleString("zh-CN")}`,
      selectedProject ? `关联项目：${selectedProject.name} / ${selectedProject.title}` : "关联项目：未指定",
      protocol?.research_question ? `研究问题：${protocol.research_question}` : "研究问题：待补充",
      "",
      "## 总览",
      `- 高风险：${highRiskCount}`,
      `- 需复核：${reviewNeededCount}`,
      `- 已通过：${passedCount}`,
      "",
      "## 检查项",
      ...reviewerChecks.flatMap((item, index) => [
        `### ${index + 1}. ${item.title}`,
        `- 状态：${item.status}`,
        `- 风险：${riskLabels[item.severity]}`,
        `- 细节：${item.detail}`,
        `- 建议：${item.recommendation}`,
        "",
      ]),
      "## 使用边界",
      "- 该清单是规则型投稿前自查，不代表真实同行评审意见。",
      "- 正式投稿前仍需人工复核伦理、统计、引用、图表和目标期刊格式。",
      "",
    ].join("\n");

    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    try {
      link.href = url;
      link.download = "pre-submission-review.md";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  function handleDownloadProtocolQualityCheck() {
    const content = [
      "# 方案质量检查",
      "",
      `导出时间：${new Date().toLocaleString("zh-CN")}`,
      selectedProject ? `关联项目：${selectedProject.name} / ${selectedProject.title}` : "关联项目：未指定",
      "",
      "## 总览",
      `- 完成度：${protocolQualitySummary.completionPercent}%`,
      `- 已通过：${protocolQualitySummary.passedCount}`,
      `- 需补充：${protocolQualitySummary.needsInputCount}`,
      `- 高风险：${protocolQualitySummary.highRiskCount}`,
      `- 下一步：${protocolQualitySummary.nextAction}`,
      "",
      "## 检查项",
      ...protocolQualitySummary.items.flatMap((item, index) => [
        `### ${index + 1}. ${item.title}`,
        `- 状态：${item.status === "passed" ? "已通过" : item.status === "high_risk" ? "高风险" : "需补充"}`,
        `- 细节：${item.detail}`,
        `- 建议：${item.recommendation}`,
        "",
      ]),
      "## 使用边界",
      "- 本检查为规则型完整性检查，不替代医学、伦理或统计专家审查。",
      "- 正式研究方案仍需根据本中心数据、伦理审批和目标期刊要求人工复核。",
      "",
    ].join("\n");

    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    try {
      link.href = url;
      link.download = "protocol-quality-check.md";
      document.body.appendChild(link);
      link.click();
      link.remove();
    } finally {
      URL.revokeObjectURL(url);
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

  async function handleConfirmMentorRecommendationToProtocol() {
    if (
      !selectedProjectId ||
      !pendingMentorProtocolCard ||
      applyingMentorCardTitle ||
      !canEditSelectedProject
    ) {
      return;
    }

    const card = pendingMentorProtocolCard;
    setApplyingMentorCardTitle(card.title);
    setError(null);

    try {
      const savedProtocol = await saveProjectProtocol(
        selectedProjectId,
        mentorCardToProtocolUpdate(card),
      );
      setProtocol(savedProtocol);
      setSelectedAgentId("study_planner");
      setOpenProtocolSections({
        core: true,
        criteria: true,
        analysis: true,
        submission: true,
      });
      setPendingMentorProtocolCard(null);
      await refreshDataRequirements(selectedProjectId);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "推荐课题写入研究方案失败。");
    } finally {
      setApplyingMentorCardTitle(null);
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

  async function processCsvFile(file: File): Promise<CsvProcessingDefaults | null> {
    if (!selectedProjectId || isCsvUploading || !canEditSelectedProject) {
      return null;
    }

    setIsCsvUploading(true);
    setError(null);

    try {
      setWorkflowStatus("正在生成质控报告...");
      const report = await uploadDataQualityReport(selectedProjectId, file);
      const numericDefaults = preferredNumericColumns(report.columns);
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
      setWorkflowSummary({
        source: file.name === preparedDataSampleFileName ? "prepared" : "manual",
        fileName: report.file_name,
        rowCount: report.row_count,
        columnCount: report.column_count,
        chartCount: 0,
        saved: false,
        message: "已生成质控报告，下一步可生成统计草案。",
      });
      setSelectedOutcomeColumns(numericDefaults);
      setSelectedGroupColumn(groupDefault);
      resetPairedFormalTestSettings();
      setFormalTestConfirmation(createFormalTestConfirmation(currentUser?.display_name ?? ""));
      setSelectedAgentId("data_analyst");
      await refreshDataAuditLogs(selectedProjectId);
      setWorkflowStatus("质控报告已生成。");
      return {
        report,
        groupColumn: groupDefault,
        outcomeColumns: numericDefaults,
      };
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "CSV 质量检查失败。");
      setWorkflowStatus(null);
      return null;
    } finally {
      setIsCsvUploading(false);
    }
  }

  async function handleCsvUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) {
      return;
    }

    await processCsvFile(file);
  }

  async function handleLoadPreparedData() {
    if (isCsvUploading || !canEditSelectedProject) {
      return;
    }

    setError(null);

    try {
      setWorkflowStatus("正在加载预备 DATA...");
      const response = await fetch(preparedDataSamplePath);
      if (!response.ok) {
        throw new Error(`预备 DATA 读取失败：${response.status}`);
      }
      const csvText = await response.text();
      const file = new File([csvText], preparedDataSampleFileName, { type: "text/csv" });
      await processCsvFile(file);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "预备 DATA 加载失败。");
    }
  }

  async function saveAnalysisRecordFromReports(
    fileName: string,
    quality: DataQualityReport,
    statistics: DataStatisticsReport | null,
  ): Promise<DataAnalysisRecord | null> {
    if (!selectedProjectId || !canEditSelectedProject) {
      return null;
    }

    const savedRecord = await saveDataAnalysisRecord(selectedProjectId, {
      file_name: fileName,
      quality_report: quality,
      statistics_report: statistics,
    });
    setAnalysisRecords((current) => [
      savedRecord,
      ...current.filter((record) => record.id !== savedRecord.id),
    ]);
    return savedRecord;
  }

  async function handleRunPreparedDataWorkflow() {
    if (!selectedProjectId || isCsvUploading || isStatisticsLoading || !canEditSelectedProject) {
      return;
    }

    setError(null);

    try {
      const response = await fetch(preparedDataSamplePath);
      if (!response.ok) {
        throw new Error(`预备 DATA 读取失败：${response.status}`);
      }
      const csvText = await response.text();
      const file = new File([csvText], preparedDataSampleFileName, { type: "text/csv" });
      const defaults = await processCsvFile(file);
      if (!defaults) {
        return;
      }
      if (!defaults.outcomeColumns.length) {
        setSelectedAgentId("data_analyst");
        setError("预备 DATA 已完成质控，但没有可用于统计草案的数值结局列。");
        return;
      }

      setWorkflowStatus("正在生成统计草案...");
      setIsStatisticsLoading(true);
      const statistics = await uploadDataStatisticsReport(
        selectedProjectId,
        file,
        defaults.groupColumn,
        defaults.outcomeColumns,
      );
      setStatisticsReport(statistics);
      setFormalTestConfirmation(createFormalTestConfirmation(currentUser?.display_name ?? ""));
      setWorkflowStatus("正在保存分析记录...");
      const savedRecord = await saveAnalysisRecordFromReports(file.name, defaults.report, statistics);
      await refreshDataAuditLogs(selectedProjectId);
      setWorkflowSummary({
        source: "prepared",
        fileName: defaults.report.file_name,
        rowCount: defaults.report.row_count,
        columnCount: defaults.report.column_count,
        chartCount: statistics.chart_specs.length,
        saved: Boolean(savedRecord),
        message: savedRecord
          ? "预备 DATA 联调已完成并保存，可在已保存报告中恢复。"
          : "预备 DATA 联调已完成，但未保存分析记录。",
      });
      setWorkflowStatus("已切换到 Alex Writer。");
      setSelectedAgentId("writer");
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "预备 DATA 联调流程失败。");
      setWorkflowStatus(null);
    } finally {
      setIsStatisticsLoading(false);
    }
  }

  function handleLoadPreparedReferences() {
    const report = buildPreparedReferenceReport();
    setMentorRecommendationReport(applyMentorEvidenceReviews(report, mentorEvidenceReviews));
    setSelectedAgentId("mentor");
  }

  function handleOutcomeColumnToggle(columnName: string) {
    setSelectedOutcomeColumns((current) => {
      if (current.includes(columnName)) {
        return current.filter((name) => name !== columnName);
      }
      if (isPairedFormalTest && pairedDataLayout === "long") {
        return [columnName];
      }
      const maxOutcomeCount = isPairedFormalTest ? 2 : 6;
      return [...current, columnName].slice(0, maxOutcomeCount);
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
      setWorkflowStatus("正在生成统计草案...");
      const report = await uploadDataStatisticsReport(
        selectedProjectId,
        uploadedCsvFile,
        selectedGroupColumn,
        selectedOutcomeColumns,
      );
      setStatisticsReport(report);
      if (qualityReport) {
        setWorkflowSummary({
          source: uploadedCsvFile.name === preparedDataSampleFileName ? "prepared" : "manual",
          fileName: qualityReport.file_name,
          rowCount: qualityReport.row_count,
          columnCount: qualityReport.column_count,
          chartCount: report.chart_specs.length,
          saved: false,
          message: "统计草案已生成，保存后可在分析记录中恢复。",
        });
      }
      setFormalTestConfirmation(createFormalTestConfirmation(currentUser?.display_name ?? ""));
      setSelectedAgentId("data_analyst");
      await refreshDataAuditLogs(selectedProjectId);
      setWorkflowStatus("统计草案已生成。");
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "统计草案生成失败。");
      setWorkflowStatus(null);
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
    if (!isPairedFormalTest && !formalGroupColumn) {
      setError("正式检验前请先选择分组列，并重新生成统计草案。");
      return;
    }

    if (isPairedFormalTest) {
      if (pairedDataLayout === "wide" && selectedOutcomeColumns.length !== 2) {
        setError("宽表配对 t 检验需要且只能选择两个数值结局列。");
        return;
      }
      if (pairedDataLayout === "long") {
        if (selectedOutcomeColumns.length !== 1) {
          setError("长表配对检验需要且只能选择一个数值结局列。");
          return;
        }
        if (!pairedSubjectColumn || !pairedConditionColumn) {
          setError("长表配对检验需要选择对象 ID 列和条件列。");
          return;
        }
        if (pairedAnalysis === "friedman" || pairedAnalysis === "rm_anova") {
          if (parsedPairedConditions.length < 3) {
            setError("Friedman 重复测量检验至少需要填写 3 个条件/时间点取值。");
            return;
          }
          if (hasDuplicatePairedConditions) {
            setError("Friedman 条件/时间点取值不能重复。");
            return;
          }
        } else {
          if (!pairedConditionA.trim() || !pairedConditionB.trim()) {
            setError("长表配对 t 检验需要填写两个条件取值。");
            return;
          }
          if (pairedConditionA.trim() === pairedConditionB.trim()) {
            setError("长表配对 t 检验的两个条件取值不能相同。");
            return;
          }
        }
      }
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
        formalGroupColumn ?? "",
        isPairedFormalTest
          ? selectedOutcomeColumns
          : statisticsReport.numeric_summaries.map((summary) => summary.column),
        formalTestConfirmation,
        {
          pairedTest: isPairedFormalTest,
          pairedDataLayout,
          pairedAnalysis,
          pairedSubjectColumn,
          pairedConditionColumn,
          pairedConditionA: pairedConditionA.trim(),
          pairedConditionB: pairedConditionB.trim(),
          pairedConditions:
            pairedAnalysis === "friedman" || pairedAnalysis === "rm_anova"
              ? parsedPairedConditions
              : undefined,
          multiplicityCorrection,
        },
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
      .map((result) => {
        const pairwiseText =
          result.pairwise_results
            ?.map((pairwise) => `  - ${pairwise.group_a} vs ${pairwise.group_b}: ${pairwise.interpretation}`)
            .join("\n") ?? "";
        return [`- ${result.outcome_column}: ${result.interpretation}`, pairwiseText]
          .filter(Boolean)
          .join("\n");
      })
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

  function buildReferenceHandoffMessage(): string {
    if (!selectedProject || !mentorCandidateReferences.length) {
      return "";
    }

    const referenceText = mentorCandidateReferences
      .map(({ cardTitle, evidence }, index) =>
        [
          `${index + 1}. ${evidence.title ?? evidence.evidence_summary}`,
          `   - 来源课题：${cardTitle}`,
          `   - 作者：${evidence.authors?.join(", ") || "待补充"}`,
          `   - 期刊：${evidence.journal ?? "待补充"}`,
          `   - 年份：${evidence.publication_year ?? "待补充"}`,
          `   - 卷：${evidence.volume ?? "待补充"}`,
          `   - 期：${evidence.issue ?? "待补充"}`,
          `   - 页码/编号：${evidence.page ?? "待补充"}`,
          `   - PMID：${evidence.pmid ?? "待补充"}`,
          `   - DOI：${evidence.doi ?? "待补充"}`,
          `   - Crossref/DOI 链接：${evidence.crossref_url ?? "待补充"}`,
          `   - 候选引用草稿：${evidence.citation_text ?? "待补充"}`,
          `   - Vancouver 候选引用：${evidence.vancouver_citation ?? "待补充"}`,
          `   - 文献类型：${evidence.publication_types.join(" / ") || "待补充"}`,
          `   - 全文核对：${evidence.full_text_checked ? "是" : "否"}`,
          `   - 引用用途：${formatMentorReviewUsage(evidence)}`,
          `   - 复核备注：${evidence.review_note?.trim() || "无"}`,
          `   - 推荐信号：${evidence.recommendation_signal}`,
          `   - 局限：${evidence.limitation}`,
        ].join("\n"),
      )
      .join("\n");

    return [
      "请基于以下已经人工标记为“确认可用”的候选引用，生成 SCI 论文 Introduction 的段落写作骨架。",
      "要求：使用简体中文；不要编造未列出的文献、PMID、DOI、作者、样本量或结论；候选引用只能作为写作线索，不能当成已完成系统综述。",
      "",
      `项目：${selectedProject.name} - ${selectedProject.title}`,
      `研究主题：${selectedProject.topic}`,
      protocol?.research_question ? `研究问题：${protocol.research_question}` : "",
      protocol?.primary_endpoint ? `主要终点：${protocol.primary_endpoint}` : "",
      "",
      "候选引用：",
      referenceText,
      "",
      "请输出：1）Introduction 背景段、研究空白段、研究目的段写作骨架；2）每个段落建议引用哪些候选文献；3）仍需补充检索或人工阅读全文确认的项目。Discussion 请等待 Dr. Data Lin 正式结果确认后再生成。",
    ]
      .filter(Boolean)
      .join("\n");
  }

  async function handleSaveWriterIntroductionDraft() {
    if (!selectedProjectId || isWriterDraftSaving || !canEditSelectedProject) {
      return;
    }

    setIsWriterDraftSaving(true);
    setError(null);
    try {
      const savedDraft = await saveWriterIntroductionDraft(
        selectedProjectId,
        writerIntroductionDraftForm,
      );
      setWriterIntroductionDraft(savedDraft);
      setWriterIntroductionDraftForm({
        background_paragraph: savedDraft.background_paragraph,
        gap_paragraph: savedDraft.gap_paragraph,
        objective_paragraph: savedDraft.objective_paragraph,
        citation_bindings: normalizeIntroductionCitationBindings(savedDraft.citation_bindings),
      });
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Introduction 草稿保存失败。");
    } finally {
      setIsWriterDraftSaving(false);
    }
  }

  function handleInsertSemanticCitation(
    field: IntroductionDraftField,
    evidence: MentorEvidenceItem,
  ) {
    if (!canEditSelectedProject) {
      return;
    }
    const sentence = buildIntroductionCitationSentence(field, evidence);
    setWriterIntroductionDraftForm((current) => {
      const currentText = current[field].trimEnd();
      return {
        ...current,
        [field]: currentText ? `${currentText}\n${sentence}` : sentence,
      };
    });
  }

  function isReferenceBoundToField(
    field: IntroductionDraftField,
    evidence: MentorEvidenceItem,
  ): boolean {
    const citationBindings = normalizeIntroductionCitationBindings(
      writerIntroductionDraftForm.citation_bindings,
    );
    return citationBindings[field].includes(primaryReferenceKeyForEvidence(evidence));
  }

  function handleToggleManualCitationBinding(
    field: IntroductionDraftField,
    evidence: MentorEvidenceItem,
    checked: boolean,
  ) {
    if (!canEditSelectedProject) {
      return;
    }

    const referenceKey = primaryReferenceKeyForEvidence(evidence);
    setWriterIntroductionDraftForm((current) => {
      const citationBindings = normalizeIntroductionCitationBindings(current.citation_bindings);
      const fieldKeys = citationBindings[field];
      const nextFieldKeys = checked
        ? fieldKeys.includes(referenceKey)
          ? fieldKeys
          : [...fieldKeys, referenceKey]
        : fieldKeys.filter((key) => key !== referenceKey);

      return {
        ...current,
        citation_bindings: {
          ...citationBindings,
          [field]: nextFieldKeys,
        },
      };
    });
  }

  function handleRemoveManualCitationBinding(field: IntroductionDraftField, bindingKey: string) {
    if (!canEditSelectedProject) {
      return;
    }

    setWriterIntroductionDraftForm((current) => {
      const citationBindings = normalizeIntroductionCitationBindings(current.citation_bindings);
      return {
        ...current,
        citation_bindings: {
          ...citationBindings,
          [field]: citationBindings[field].filter((key) => key !== bindingKey),
        },
      };
    });
  }

  async function handleCitationQualityMarkIntroductionUse(
    issueKey: string,
    action: Extract<
      NonNullable<IntroductionCitationQualityIssue["action"]>,
      { kind: "mark-introduction-use" }
    >,
  ) {
    if (!canEditSelectedProject || !selectedProjectId) {
      return;
    }

    setCitationQualityNotice("正在保存用途标记...");
    setUpdatingCitationQualityActionKey(issueKey);
    try {
      const didSave = await handleMentorEvidenceReview(action.cardTitle, action.evidenceIndex, action.evidence, {
        use_in_introduction: true,
      });
      setCitationQualityNotice(
        didSave ? "已标记为 Introduction 用途。" : "用途标记保存失败，请查看页面错误提示。",
      );
    } finally {
      setUpdatingCitationQualityActionKey(null);
    }
  }

  function handleCitationQualityRemoveBinding(
    action: Extract<
      NonNullable<IntroductionCitationQualityIssue["action"]>,
      { kind: "remove-binding" }
    >,
  ) {
    handleRemoveManualCitationBinding(action.field, action.bindingKey);
    setCitationQualityNotice("绑定已从草稿中移除，请点击“保存草稿”持久化。");
  }

  async function handleSendReferencesToWriter() {
    if (!selectedProjectId || !mentorCandidateReferences.length || isWriterDrafting) {
      return;
    }

    const handoffMessage = buildReferenceHandoffMessage();
    if (!handoffMessage) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      speaker: "user",
      agentId: "writer",
      projectId: selectedProjectId,
      content: "请根据 Mentor 已确认可用的候选引用生成 Introduction 写作骨架。",
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
      setError(caughtError instanceof Error ? caughtError.message : "引用写作提纲生成失败。");
    } finally {
      setIsWriterDrafting(false);
    }
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
      await saveAnalysisRecordFromReports(qualityReport.file_name, qualityReport, statisticsReport);
      setWorkflowSummary({
        source: uploadedCsvFile?.name === preparedDataSampleFileName ? "prepared" : "manual",
        fileName: qualityReport.file_name,
        rowCount: qualityReport.row_count,
        columnCount: qualityReport.column_count,
        chartCount: statisticsReport?.chart_specs.length ?? 0,
        saved: true,
        message: "分析记录已保存，可在已保存报告中恢复。",
      });
      setWorkflowStatus("分析记录已保存。");
      await refreshDataAuditLogs(selectedProjectId);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "分析记录保存失败。");
      setWorkflowStatus(null);
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
    resetPairedFormalTestSettings();
    setFormalTestConfirmation(
      record.statistics_report?.formal_test_report?.confirmation ??
        createFormalTestConfirmation(currentUser?.display_name ?? ""),
    );
    setWorkflowSummary({
      source: "restored",
      fileName: record.file_name,
      rowCount: record.row_count,
      columnCount: record.column_count,
      chartCount: record.chart_count,
      saved: true,
      message: record.statistics_report
        ? "已从保存记录恢复统计草案，并切换到 Alex Writer。"
        : "已从保存记录恢复质控报告。",
    });
    setWorkflowStatus(record.statistics_report ? "已恢复到 Alex Writer。" : "已恢复分析记录。");
    setSelectedAgentId(record.statistics_report ? "writer" : "data_analyst");
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

                <section className="pipeline-panel" aria-label="论文流程总览">
                  <div className="pipeline-head">
                    <div>
                      <p className="eyebrow">论文流程总览</p>
                      <h3>从选题到投稿前审查</h3>
                    </div>
                    <span>
                      {pipelineSteps.filter((step) => step.status === "ready").length} / {pipelineSteps.length} 已就绪
                    </span>
                  </div>
                  <div className="pipeline-step-list">
                    {pipelineSteps.map((step, index) => (
                      <button
                        className={`pipeline-step status-${step.status} ${
                          selectedAgentId === step.agentId ? "selected" : ""
                        }`}
                        type="button"
                        key={step.id}
                        onClick={() => setSelectedAgentId(step.agentId)}
                      >
                        <span className="pipeline-step-index">{index + 1}</span>
                        <div>
                          <strong>{step.title}</strong>
                          <small>{step.detail}</small>
                        </div>
                        <em>{pipelineStatusLabels[step.status]}</em>
                      </button>
                    ))}
                  </div>
                  <div className="pipeline-action-strip" aria-label="主流程快捷操作">
                    <div>
                      <strong>主流程快捷操作</strong>
                      <span>
                        先加载公开引用和预备 DATA，再一键联调到 Writer，最后进入 Reviewer 做投稿前检查。
                      </span>
                    </div>
                    <div className="pipeline-action-buttons">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedAgentId("mentor");
                          handleLoadPreparedReferences();
                        }}
                        disabled={!canEditSelectedProject}
                      >
                        <BookOpenCheck aria-hidden="true" size={15} />
                        <span>加载预备引用</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedAgentId("data_analyst");
                          void handleLoadPreparedData();
                        }}
                        disabled={isCsvUploading || isStatisticsLoading || !canEditSelectedProject}
                      >
                        {isCsvUploading ? (
                          <Loader2 aria-hidden="true" className="spin" size={15} />
                        ) : (
                          <FileText aria-hidden="true" size={15} />
                        )}
                        <span>加载预备 DATA</span>
                      </button>
                      <button
                        className="primary"
                        type="button"
                        onClick={() => {
                          setSelectedAgentId("data_analyst");
                          void handleRunPreparedDataWorkflow();
                        }}
                        disabled={isCsvUploading || isStatisticsLoading || !canEditSelectedProject}
                      >
                        {isCsvUploading || isStatisticsLoading ? (
                          <Loader2 aria-hidden="true" className="spin" size={15} />
                        ) : (
                          <Sparkles aria-hidden="true" size={15} />
                        )}
                        <span>{isCsvUploading || isStatisticsLoading ? "联调中" : "一键联调到 Writer"}</span>
                      </button>
                      <button type="button" onClick={() => setSelectedAgentId("writer")}>
                        <FileText aria-hidden="true" size={15} />
                        <span>查看 Writer</span>
                      </button>
                      <button type="button" onClick={() => setSelectedAgentId("reviewer")}>
                        <ShieldCheck aria-hidden="true" size={15} />
                        <span>查看 Reviewer</span>
                      </button>
                    </div>
                    {workflowStatus || workflowSummary ? (
                      <div className="pipeline-action-status">
                        {workflowStatus ? <strong>{workflowStatus}</strong> : null}
                        {workflowSummary ? (
                          <span>
                            {workflowSummary.fileName} · {workflowSummary.rowCount} 行 /{" "}
                            {workflowSummary.columnCount} 列 · {workflowSummary.saved ? "已保存" : "未保存"}
                          </span>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                </section>

                <div className="workbench-main">
                  <div className="side-workbench">
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
                          {isSending ? (
                            <Loader2 aria-hidden="true" className="spin" size={18} />
                          ) : (
                            <Send aria-hidden="true" size={18} />
                          )}
                          <span>发送</span>
                        </button>
                      </form>
                    </section>

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

                  </div>
                  <div className="expert-workbench">

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
                    <>
                    <section className="protocol-quality-panel">
                      <div className="protocol-quality-head">
                        <div>
                          <p className="eyebrow">方案质量检查</p>
                          <h4>{protocolQualitySummary.completionPercent}% 完成</h4>
                          <small>{protocolQualitySummary.nextAction}</small>
                        </div>
                        <button type="button" onClick={handleDownloadProtocolQualityCheck}>
                          <Download aria-hidden="true" size={15} />
                          <span>导出检查</span>
                        </button>
                      </div>
                      <div className="protocol-quality-metrics">
                        <span>已通过 {protocolQualitySummary.passedCount}</span>
                        <span>需补充 {protocolQualitySummary.needsInputCount}</span>
                        <span>高风险 {protocolQualitySummary.highRiskCount}</span>
                      </div>
                      <div className="protocol-quality-list">
                        {protocolQualitySummary.items.map((item) => (
                          <article className={`protocol-quality-item status-${item.status}`} key={item.key}>
                            <div>
                              <strong>{item.title}</strong>
                              <small>{item.detail}</small>
                            </div>
                            <span>
                              {item.status === "passed"
                                ? "已通过"
                                : item.status === "high_risk"
                                  ? "高风险"
                                  : "需补充"}
                            </span>
                            {item.status !== "passed" ? <p>{item.recommendation}</p> : null}
                          </article>
                        ))}
                      </div>
                    </section>
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
                    </>
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
                    <button
                      className="prepared-data-button"
                      type="button"
                      onClick={handleLoadPreparedData}
                      disabled={isCsvUploading || isStatisticsLoading || !canEditSelectedProject}
                    >
                      {isCsvUploading ? (
                        <Loader2 aria-hidden="true" className="spin" size={16} />
                      ) : (
                        <FileText aria-hidden="true" size={16} />
                      )}
                      <span>加载预备 DATA</span>
                    </button>
                    <button
                      className="prepared-workflow-button"
                      type="button"
                      onClick={handleRunPreparedDataWorkflow}
                      disabled={isCsvUploading || isStatisticsLoading || !canEditSelectedProject}
                    >
                      {isCsvUploading || isStatisticsLoading ? (
                        <Loader2 aria-hidden="true" className="spin" size={16} />
                      ) : (
                        <Sparkles aria-hidden="true" size={16} />
                      )}
                      <span>{isCsvUploading || isStatisticsLoading ? "联调中" : "一键联调到 Writer"}</span>
                    </button>
                  </div>

                  {workflowStatus || workflowSummary ? (
                    <div className="workflow-status-panel">
                      {workflowStatus ? <strong>{workflowStatus}</strong> : null}
                      {workflowSummary ? (
                        <div className="workflow-summary-row">
                          <span>{workflowSummary.fileName}</span>
                          <span>
                            {workflowSummary.rowCount} 行 / {workflowSummary.columnCount} 列
                          </span>
                          <span>{workflowSummary.chartCount} 张图</span>
                          <span>{workflowSummary.saved ? "已保存" : "未保存"}</span>
                        </div>
                      ) : null}
                      {workflowSummary ? <p>{workflowSummary.message}</p> : null}
                    </div>
                  ) : null}

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

                              <label className="formal-test-mode-toggle">
                                <input
                                  type="checkbox"
                                  checked={isPairedFormalTest}
                                  disabled={!canEditSelectedProject}
                                  onChange={(event) => {
                                    setIsPairedFormalTest(event.target.checked);
                                    setPairedDataLayout("wide");
                                    setPairedSubjectColumn("");
                                    setPairedConditionColumn("");
                                    setPairedConditionA("");
                                    setPairedConditionB("");
                                    setSelectedOutcomeColumns((current) =>
                                      event.target.checked ? current.slice(0, 2) : current,
                                    );
                                    setStatisticsReport((current) =>
                                      current ? { ...current, formal_test_report: null } : current,
                                    );
                                    setFormalTestConfirmation(
                                      createFormalTestConfirmation(currentUser?.display_name ?? ""),
                                    );
                                  }}
                                />
                                <span>
                                  <strong>配对检验模式</strong>
                                  <small>支持宽表两列配对，或长表对象 ID + 条件列配对。</small>
                                </span>
                              </label>

                              {isPairedFormalTest ? (
                                <div className="paired-test-config">
                                  <label>
                                    <span>配对数据格式</span>
                                    <select
                                      value={pairedDataLayout}
                                      disabled={!canEditSelectedProject}
                                      onChange={(event) => {
                                        const nextLayout = event.target.value as PairedDataLayout;
                                        setPairedDataLayout(nextLayout);
                                        if (nextLayout === "wide") {
                                          setPairedAnalysis("paired_t");
                                        }
                                        setSelectedOutcomeColumns((current) =>
                                          nextLayout === "long" ? current.slice(0, 1) : current.slice(0, 2),
                                        );
                                        setStatisticsReport((current) =>
                                          current ? { ...current, formal_test_report: null } : current,
                                        );
                                      }}
                                    >
                                      <option value="wide">宽表：同一行两个数值列</option>
                                      <option value="long">长表：对象 ID + 条件列 + 一个结局列</option>
                                    </select>
                                  </label>

                                  {pairedDataLayout === "long" ? (
                                    <div className="paired-long-grid">
                                      <label>
                                        <span>配对检验类型</span>
                                        <select
                                          value={pairedAnalysis}
                                          disabled={!canEditSelectedProject}
                                          onChange={(event) =>
                                            setPairedAnalysis(event.target.value as PairedAnalysis)
                                          }
                                        >
                                          <option value="paired_t">两条件配对 t</option>
                                          <option value="friedman">三条件及以上 Friedman</option>
                                          <option value="rm_anova">重复测量 ANOVA（待复核）</option>
                                        </select>
                                      </label>
                                      <label>
                                        <span>对象 ID 列</span>
                                        <select
                                          value={pairedSubjectColumn}
                                          disabled={!canEditSelectedProject}
                                          onChange={(event) => setPairedSubjectColumn(event.target.value)}
                                        >
                                          <option value="">选择对象列</option>
                                          {pairedColumnOptions.map((column) => (
                                            <option key={column.name} value={column.name}>
                                              {column.name}
                                            </option>
                                          ))}
                                        </select>
                                      </label>
                                      <label>
                                        <span>条件/时间点列</span>
                                        <select
                                          value={pairedConditionColumn}
                                          disabled={!canEditSelectedProject}
                                          onChange={(event) => setPairedConditionColumn(event.target.value)}
                                        >
                                          <option value="">选择条件列</option>
                                          {pairedColumnOptions.map((column) => (
                                            <option key={column.name} value={column.name}>
                                              {column.name}
                                            </option>
                                          ))}
                                        </select>
                                      </label>
                                      {pairedAnalysis === "friedman" || pairedAnalysis === "rm_anova" ? (
                                        <label className="paired-long-wide">
                                          <span>条件/时间点列表</span>
                                          <textarea
                                            rows={2}
                                            value={pairedConditionList}
                                            disabled={!canEditSelectedProject}
                                            onChange={(event) => setPairedConditionList(event.target.value)}
                                            placeholder="例如 before, mid, after"
                                          />
                                        </label>
                                      ) : (
                                        <>
                                          <label>
                                            <span>条件 A</span>
                                            <input
                                              type="text"
                                              value={pairedConditionA}
                                              disabled={!canEditSelectedProject}
                                              onChange={(event) => setPairedConditionA(event.target.value)}
                                              placeholder="例如 before"
                                            />
                                          </label>
                                          <label>
                                            <span>条件 B</span>
                                            <input
                                              type="text"
                                              value={pairedConditionB}
                                              disabled={!canEditSelectedProject}
                                              onChange={(event) => setPairedConditionB(event.target.value)}
                                              placeholder="例如 after"
                                            />
                                          </label>
                                        </>
                                      )}
                                    </div>
                                  ) : null}
                                </div>
                              ) : null}

                              <label className="formal-test-correction">
                                <span>多重比较校正</span>
                                <select
                                  value={multiplicityCorrection}
                                  disabled={!canEditSelectedProject}
                                  onChange={(event) => {
                                    setMultiplicityCorrection(event.target.value as MultiplicityCorrection);
                                    setStatisticsReport((current) =>
                                      current ? { ...current, formal_test_report: null } : current,
                                    );
                                  }}
                                >
                                  <option value="holm">Holm-Bonferroni</option>
                                  <option value="fdr">Benjamini-Hochberg FDR</option>
                                </select>
                              </label>

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
                                  (!isPairedFormalTest && !statisticsReport.group_column) ||
                                  isPairedFormalTestInvalid ||
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
                              {!isPairedFormalTest && !statisticsReport.group_column ? (
                                <p className="formal-test-note">
                                  正式检验需要先选择分组列，并重新生成统计草案。
                                </p>
                              ) : null}
                              {isPairedFormalTest &&
                              pairedDataLayout === "wide" &&
                              selectedOutcomeColumns.length !== 2 ? (
                                <p className="formal-test-note">
                                  宽表配对 t 检验需要在上方结局列中选择且只选择两个数值列。
                                </p>
                              ) : null}
                              {isPairedFormalTest && pairedDataLayout === "long" && isPairedFormalTestInvalid ? (
                                <p className="formal-test-note">
                                  {pairedAnalysis === "friedman" || pairedAnalysis === "rm_anova"
                                    ? "长表 Friedman 检验需要选择一个数值结局列、对象 ID 列、条件列，并填写至少 3 个唯一条件取值。"
                                    : "长表配对 t 检验需要选择一个数值结局列、对象 ID 列、条件列，并填写两个不同条件取值。"}
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
                                        <span>{formatFormalStatistic(result)}</span>
                                        <span>P={formatPValue(result.p_value)}</span>
                                        <span>{formatFormalDegreesOfFreedom(result)}</span>
                                        <span>{formatFormalEffectSize(result)}</span>
                                        <span>{result.group_labels.join(" / ")}</span>
                                      </div>
                                      {result.warnings.length ? (
                                        <small>{result.warnings.join("；")}</small>
                                      ) : null}
                                      {result.pairwise_results?.length ? (
                                        <div className="pairwise-results">
                                          <strong>事后两两比较</strong>
                                          {result.pairwise_results.map((pairwise) => (
                                            <div
                                              className={`pairwise-result status-${pairwise.status}`}
                                              key={`${pairwise.group_a}-${pairwise.group_b}-${pairwise.test_name}`}
                                            >
                                              <div>
                                                <span>
                                                  {pairwise.group_a} vs {pairwise.group_b}
                                                </span>
                                                <small>{pairwise.test_name}</small>
                                              </div>
                                              <p>{pairwise.interpretation}</p>
                                              <div className="formal-test-metrics">
                                                <span>{formatPairwiseStatistic(pairwise)}</span>
                                                <span>P={formatPValue(pairwise.p_value)}</span>
                                                <span>
                                                  {formatPairwiseCorrectionLabel(pairwise)}=
                                                  {formatPValue(pairwise.adjusted_p_value)}
                                                </span>
                                                <span>{formatPairwiseEffectSize(pairwise)}</span>
                                              </div>
                                              {pairwise.warnings.length ? (
                                                <small>{pairwise.warnings.join("；")}</small>
                                              ) : null}
                                            </div>
                                          ))}
                                        </div>
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
                              {record.statistics_report ? "恢复到 Writer" : "恢复"}
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

                {shouldShowMentorWorkspace ? (
                  <section className="mentor-panel" aria-label="虚拟导师工作区">
                    <div className="mentor-head">
                      <div>
                        <p className="eyebrow">Prof. RadOnc Mentor</p>
                        <h3>趋势判断与课题推荐</h3>
                        <small>
                          {mentorTrendSnapshot?.recommended_focus ?? "正在读取趋势快照。"}
                        </small>
                      </div>
                      <BookOpenCheck aria-hidden="true" size={20} />
                    </div>

                    {isMentorLoading ? (
                      <div className="protocol-loading compact">
                        <Loader2 aria-hidden="true" className="spin" size={18} />
                        <span>正在读取虚拟导师趋势数据...</span>
                      </div>
                    ) : null}

                    {mentorTrendSnapshot ? (
                      <div className="mentor-brief-layout">
                        <section className="mentor-brief-section">
                          <div className="mentor-section-head">
                            <strong>趋势概览</strong>
                            <span>2019-2024 快照</span>
                          </div>
                          <div className="mentor-trend-grid">
                            {mentorTrendSnapshot.trends.slice(0, 6).map((trend) => (
                              <article className="mentor-trend-card" key={trend.topic_id}>
                                <div className="mentor-trend-title">
                                  <strong>{trend.title}</strong>
                                  <span>{trend.heat_label}</span>
                                </div>
                                <p>{trend.summary}</p>
                                <small>{trend.forecast_note}</small>
                              </article>
                            ))}
                          </div>
                        </section>

                        <section className="mentor-brief-section mentor-heatmap-section">
                          <div className="mentor-section-head">
                            <strong>热点方向</strong>
                            <span>按 2024 发文量排序</span>
                          </div>
                          <div className="mentor-heatmap-list">
                            {mentorTrendHighlights.map((trend) => {
                              const latestCount =
                                trend.recent_counts[trend.recent_counts.length - 1]?.publication_count ?? 0;
                              const maxCount =
                                mentorTrendHighlights[0]?.recent_counts[
                                  mentorTrendHighlights[0].recent_counts.length - 1
                                ]?.publication_count ?? 1;
                              return (
                                <article className="mentor-heatmap-item" key={trend.topic_id}>
                                  <div className="mentor-heatmap-copy">
                                    <strong>{trend.title}</strong>
                                    <small>{trend.heat_label}</small>
                                  </div>
                                  <div className="mentor-heatmap-bar">
                                    <span
                                      className="mentor-heatmap-fill"
                                      style={{ width: `${Math.max((latestCount / maxCount) * 100, 8)}%` }}
                                    />
                                  </div>
                                  <span className="mentor-heatmap-value">{latestCount}</span>
                                </article>
                              );
                            })}
                          </div>
                        </section>
                      </div>
                    ) : null}

                    <form className="mentor-form" onSubmit={handleMentorSubmit}>
                      <div className="mentor-prepared-row">
                        <p>需要真实引用联调时，可先加载预备 DATA 的公开数据源引用。</p>
                        <button type="button" onClick={handleLoadPreparedReferences}>
                          <BookOpenCheck aria-hidden="true" size={15} />
                          <span>加载预备引用</span>
                        </button>
                      </div>
                      <div className="mentor-form-grid">
                        <label>
                          <span>设备与治疗平台</span>
                          <input
                            type="text"
                            value={mentorForm.equipmentSummary}
                            onChange={(event) =>
                              setMentorForm((current) => ({
                                ...current,
                                equipmentSummary: event.target.value,
                              }))
                            }
                            placeholder="例如 Elekta Unity / TrueBeam / Halcyon"
                          />
                        </label>
                        <label>
                          <span>计划系统</span>
                          <input
                            type="text"
                            value={mentorForm.planningSystems}
                            onChange={(event) =>
                              setMentorForm((current) => ({
                                ...current,
                                planningSystems: event.target.value,
                              }))
                            }
                            placeholder="例如 Monaco / Eclipse / RayStation"
                          />
                        </label>
                        <label>
                          <span>编程水平</span>
                          <select
                            value={mentorForm.programmingLevel}
                            onChange={(event) =>
                              setMentorForm((current) => ({
                                ...current,
                                programmingLevel: event.target.value as MentorProgrammingLevel,
                              }))
                            }
                          >
                            <option value="none">无</option>
                            <option value="basic">基础</option>
                            <option value="intermediate">中等</option>
                            <option value="advanced">熟练</option>
                          </select>
                        </label>
                        <label>
                          <span>每周科研时间（小时）</span>
                          <input
                            type="number"
                            min={0}
                            max={40}
                            value={mentorForm.weeklyHours}
                            onChange={(event) =>
                              setMentorForm((current) => ({
                                ...current,
                                weeklyHours: Number(event.target.value) || 0,
                              }))
                            }
                          />
                        </label>
                        <label className="mentor-form-wide">
                          <span>可用数据类型</span>
                          <textarea
                            rows={2}
                            value={mentorForm.dataTypesText}
                            onChange={(event) =>
                              setMentorForm((current) => ({
                                ...current,
                                dataTypesText: event.target.value,
                              }))
                            }
                            placeholder="用逗号分隔，例如 DICOM RTDose, RTStruct, log files, CBCT"
                          />
                        </label>
                        <label className="mentor-form-wide">
                          <span>既往发文经验</span>
                          <textarea
                            rows={2}
                            value={mentorForm.publicationExperience}
                            onChange={(event) =>
                              setMentorForm((current) => ({
                                ...current,
                                publicationExperience: event.target.value,
                              }))
                            }
                            placeholder="例如 已发表 1 篇 JACMP，无第一作者 SCI"
                          />
                        </label>
                      </div>

                      <div className="mentor-interest-block">
                        <strong>感兴趣的方向</strong>
                        <div className="mentor-interest-list">
                          {mentorTrendSnapshot?.trends.map((trend) => (
                            <label className="mentor-interest-item" key={trend.topic_id}>
                              <input
                                type="checkbox"
                                checked={mentorForm.interestTopics.includes(trend.topic_id)}
                                onChange={() => handleMentorInterestToggle(trend.topic_id)}
                              />
                              <span>{trend.title}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      <button className="mentor-submit-button" type="submit" disabled={isMentorSubmitting}>
                        {isMentorSubmitting ? (
                          <Loader2 aria-hidden="true" className="spin" size={16} />
                        ) : (
                          <Sparkles aria-hidden="true" size={16} />
                        )}
                        <span>生成课题推荐</span>
                      </button>
                    </form>

                    {mentorRecommendationReport ? (
                      <div className="mentor-report">
                        <div className="mentor-report-toolbar">
                          <button type="button" onClick={handleDownloadMentorBrief}>
                            <Download aria-hidden="true" size={15} />
                            <span>导出建议书</span>
                          </button>
                        </div>
                        <div className="mentor-report-summary">
                          <div className="mentor-section-head">
                            <strong>画像摘要</strong>
                            <span>个体能力与资源匹配</span>
                          </div>
                          <p>{mentorRecommendationReport.profile_summary}</p>
                        </div>
                        <section className="mentor-brief-section">
                          <div className="mentor-section-head">
                            <strong>资源诊断</strong>
                            <span>设备、数据和时间边界</span>
                          </div>
                        <div className="mentor-strength-list">
                          {mentorRecommendationReport.resource_diagnosis.map((item) => (
                            <article className="mentor-strength-item" key={item}>
                              <p>{item}</p>
                            </article>
                          ))}
                        </div>
                        </section>
                        <section className="mentor-brief-section">
                          <div className="mentor-section-head">
                            <strong>匹配优势</strong>
                            <span>为什么这些方向更现实</span>
                          </div>
                        <div className="mentor-strength-list">
                          {mentorRecommendationReport.matched_strengths.map((strength) => (
                            <article className="mentor-strength-item" key={strength}>
                              <p>{strength}</p>
                            </article>
                          ))}
                        </div>
                        </section>
                        <section className="mentor-brief-section">
                          <div className="mentor-section-head">
                            <strong>课题推荐卡</strong>
                            <span>优先考虑 2-3 个最可落地题目</span>
                          </div>
                        <div className="mentor-recommendation-list">
                          {mentorRecommendationReport.recommendations.map((item) => (
                            <article className="mentor-recommendation-card" key={item.title}>
                              <h4>{item.title}</h4>
                              <p>{item.research_question}</p>
                              <p>{item.why_fit}</p>
                              <small>{item.data_pathway}</small>
                              <small>{item.methods_route}</small>
                              <small>{item.statistical_plan}</small>
                              <small>{item.innovation_point}</small>
                              <small>{item.feasibility_note}</small>
                              <div className="mentor-card-list">
                                <strong>风险提示</strong>
                                {item.risk_flags.map((risk) => (
                                  <small key={risk}>{risk}</small>
                                ))}
                              </div>
                              <div className="mentor-evidence-list">
                                <strong>推荐依据</strong>
                                {item.evidence_items.map((evidence, evidenceIndex) => (
                                  <article key={mentorEvidenceKey(item.title, evidenceIndex, evidence)}>
                                    <div className="mentor-evidence-meta">
                                      <span>{formatMentorEvidenceStatus(evidence.evidence_status)}</span>
                                      <small>
                                        {formatMentorReviewStatus(evidence.review_status)}
                                      </small>
                                    </div>
                                    {evidence.title ? (
                                      <div className="mentor-evidence-citation">
                                        <strong>{evidence.title}</strong>
                                        <small>
                                          {[evidence.journal, evidence.publication_year, evidence.pmid ? `PMID ${evidence.pmid}` : null]
                                            .filter(Boolean)
                                            .join(" · ")}
                                        </small>
                                        <small>{formatMentorCitationDetails(evidence)}</small>
                                        {evidence.doi ? <small>DOI {evidence.doi}</small> : null}
                                        {evidence.citation_text ? (
                                          <small>候选引用：{evidence.citation_text}</small>
                                        ) : null}
                                        {evidence.vancouver_citation ? (
                                          <small>Vancouver 候选引用：{evidence.vancouver_citation}</small>
                                        ) : null}
                                        {evidence.publication_types.length ? (
                                          <small>{evidence.publication_types.join(" / ")}</small>
                                        ) : null}
                                        {evidence.external_url ? (
                                          <a href={evidence.external_url} target="_blank" rel="noreferrer">
                                            查看 PubMed
                                          </a>
                                        ) : null}
                                        {evidence.crossref_url ? (
                                          <a href={evidence.crossref_url} target="_blank" rel="noreferrer">
                                            Crossref / DOI
                                          </a>
                                        ) : null}
                                      </div>
                                    ) : null}
                                    <small>{evidence.evidence_summary}</small>
                                    <code>{evidence.search_query}</code>
                                    <small>{evidence.recommendation_signal}</small>
                                    <em>{evidence.limitation}</em>
                                    <div className="mentor-evidence-review-actions">
                                      {[
                                        { value: "unreviewed", label: "待复核" },
                                        { value: "reviewed", label: "确认可用" },
                                        { value: "rejected", label: "排除" },
                                      ].map((option) => (
                                        <button
                                          className={
                                            evidence.review_status === option.value ? "is-active" : undefined
                                          }
                                          type="button"
                                          key={option.value}
                                          onClick={() =>
                                            handleMentorEvidenceReview(
                                              item.title,
                                              evidenceIndex,
                                              evidence,
                                              { review_status: option.value },
                                            )
                                          }
                                        >
                                          {option.label}
                                        </button>
                                      ))}
                                    </div>
                                    <div className="mentor-evidence-review-details">
                                      <label>
                                        <input
                                          type="checkbox"
                                          checked={evidence.full_text_checked ?? false}
                                          onChange={(event) =>
                                            handleMentorEvidenceReview(
                                              item.title,
                                              evidenceIndex,
                                              evidence,
                                              { full_text_checked: event.currentTarget.checked },
                                            )
                                          }
                                        />
                                        <span>全文已核对</span>
                                      </label>
                                      <label>
                                        <input
                                          type="checkbox"
                                          checked={evidence.use_in_introduction ?? false}
                                          onChange={(event) =>
                                            handleMentorEvidenceReview(
                                              item.title,
                                              evidenceIndex,
                                              evidence,
                                              { use_in_introduction: event.currentTarget.checked },
                                            )
                                          }
                                        />
                                        <span>Introduction</span>
                                      </label>
                                      <label>
                                        <input
                                          type="checkbox"
                                          checked={evidence.use_in_discussion ?? false}
                                          onChange={(event) =>
                                            handleMentorEvidenceReview(
                                              item.title,
                                              evidenceIndex,
                                              evidence,
                                              { use_in_discussion: event.currentTarget.checked },
                                            )
                                          }
                                        />
                                        <span>Discussion</span>
                                      </label>
                                    </div>
                                    <label className="mentor-evidence-reviewer">
                                      <span>复核人</span>
                                      <input
                                        type="text"
                                        value={evidence.reviewer ?? ""}
                                        placeholder={currentUser?.display_name ?? "填写复核人"}
                                        onChange={(event) =>
                                          updateMentorEvidenceReviewInReport(item.title, evidenceIndex, {
                                            reviewer: event.currentTarget.value,
                                          })
                                        }
                                        onBlur={(event) =>
                                          handleMentorEvidenceReview(
                                            item.title,
                                            evidenceIndex,
                                            evidence,
                                            { reviewer: event.currentTarget.value },
                                          )
                                        }
                                      />
                                    </label>
                                    <label className="mentor-evidence-review-note">
                                      <span>复核备注</span>
                                      <textarea
                                        value={evidence.review_note ?? ""}
                                        placeholder="记录确认依据、排除原因或需要阅读全文核对的问题"
                                        rows={2}
                                        onChange={(event) =>
                                          updateMentorEvidenceReviewInReport(item.title, evidenceIndex, {
                                            review_note: event.currentTarget.value,
                                          })
                                        }
                                        onBlur={(event) =>
                                          handleMentorEvidenceReview(
                                            item.title,
                                            evidenceIndex,
                                            evidence,
                                            { review_note: event.currentTarget.value },
                                          )
                                        }
                                      />
                                    </label>
                                  </article>
                                ))}
                              </div>
                              <div className="mentor-card-list">
                                <strong>首轮里程碑</strong>
                                {item.first_milestones.map((milestone) => (
                                  <small key={milestone}>{milestone}</small>
                                ))}
                              </div>
                              <span>{item.target_journals.join(" / ")}</span>
                              <button
                                className="mentor-card-action"
                                type="button"
                                onClick={() => setPendingMentorProtocolCard(item)}
                                disabled={
                                  applyingMentorCardTitle !== null ||
                                  isProtocolSaving ||
                                  !canEditSelectedProject
                                }
                                title="写入研究方案"
                              >
                                {applyingMentorCardTitle === item.title ? (
                                  <Loader2 aria-hidden="true" className="spin" size={15} />
                                ) : (
                                  <ClipboardCheck aria-hidden="true" size={15} />
                                )}
                                <span>预览写入</span>
                              </button>
                            </article>
                          ))}
                        </div>
                        </section>
                        {pendingMentorProtocolCard && pendingMentorProtocolUpdate ? (
                          <section className="mentor-protocol-preview" aria-label="写入研究方案预览">
                            <div className="mentor-section-head">
                              <strong>写入研究方案预览</strong>
                              <span>{protocolHasContent ? "将覆盖当前方案" : "当前方案为空"}</span>
                            </div>
                            <div className="mentor-preview-warning">
                              {protocolHasContent
                                ? "确认后会用该推荐卡生成的新方案覆盖当前 Project Protocol。"
                                : "确认后会把该推荐卡写入当前项目的 Project Protocol。"}
                            </div>
                            <div className="mentor-preview-grid">
                              <article>
                                <strong>研究问题</strong>
                                <p>{pendingMentorProtocolUpdate.research_question}</p>
                              </article>
                              <article>
                                <strong>数据需求</strong>
                                <p>{pendingMentorProtocolUpdate.data_requirements}</p>
                              </article>
                              <article>
                                <strong>统计路线</strong>
                                <p>{pendingMentorProtocolUpdate.statistical_plan}</p>
                              </article>
                              <article>
                                <strong>Rhea 里程碑</strong>
                                <p>{pendingMentorProtocolUpdate.rhea_milestones}</p>
                              </article>
                            </div>
                            <div className="mentor-preview-actions">
                              <button
                                type="button"
                                onClick={() => setPendingMentorProtocolCard(null)}
                                disabled={applyingMentorCardTitle !== null}
                              >
                                取消
                              </button>
                              <button
                                type="button"
                                onClick={handleConfirmMentorRecommendationToProtocol}
                                disabled={applyingMentorCardTitle !== null || !canEditSelectedProject}
                              >
                                {applyingMentorCardTitle === pendingMentorProtocolCard.title ? (
                                  <Loader2 aria-hidden="true" className="spin" size={15} />
                                ) : (
                                  <ClipboardCheck aria-hidden="true" size={15} />
                                )}
                                <span>确认写入</span>
                              </button>
                            </div>
                          </section>
                        ) : null}
                        <section className="mentor-brief-section mentor-reference-panel">
                          <div className="mentor-section-head">
                            <strong>候选引用清单</strong>
                            <span>{mentorCandidateReferences.length} 条确认可用</span>
                          </div>
                          {mentorCandidateReferences.length ? (
                            <div className="mentor-reference-list">
                              {mentorCandidateReferences.map(({ cardTitle, evidence }, index) => (
                                <article
                                  className="mentor-reference-item"
                                  key={`${cardTitle}-${evidence.pmid ?? evidence.search_query}-${index}`}
                                >
                                  <span>{index + 1}</span>
                                  <div>
                                    <strong>{evidence.title ?? evidence.evidence_summary}</strong>
                                    <small>
                                      {[evidence.journal, evidence.publication_year, evidence.pmid ? `PMID ${evidence.pmid}` : null]
                                        .filter(Boolean)
                                        .join(" · ") || "来源信息待补充"}
                                    </small>
                                    {evidence.doi ? <small>DOI {evidence.doi}</small> : null}
                                    <small>{formatMentorCitationDetails(evidence)}</small>
                                    {evidence.citation_text ? (
                                      <small>候选引用：{evidence.citation_text}</small>
                                    ) : null}
                                    {evidence.vancouver_citation ? (
                                      <small>Vancouver 候选引用：{evidence.vancouver_citation}</small>
                                    ) : null}
                                    <small>来源课题：{cardTitle}</small>
                                    <small>
                                      全文核对：{evidence.full_text_checked ? "是" : "否"} · 引用用途：
                                      {formatMentorReviewUsage(evidence)}
                                    </small>
                                    {evidence.review_note?.trim() ? (
                                      <small>复核备注：{evidence.review_note}</small>
                                    ) : null}
                                  </div>
                                  {evidence.external_url ? (
                                    <a href={evidence.external_url} target="_blank" rel="noreferrer">
                                      PubMed
                                    </a>
                                  ) : null}
                                  {evidence.crossref_url ? (
                                    <a href={evidence.crossref_url} target="_blank" rel="noreferrer">
                                      Crossref
                                    </a>
                                  ) : null}
                                </article>
                              ))}
                            </div>
                          ) : (
                            <p className="mentor-reference-empty">
                              将推荐依据标记为“确认可用”后，会在这里汇总为候选引用。
                            </p>
                          )}
                          <div className="mentor-reference-actions">
                            <button
                              className="mentor-reference-handoff mentor-reference-export"
                              type="button"
                              onClick={handleDownloadVancouverReferences}
                              disabled={!mentorDedupedCandidateReferences.length}
                            >
                              <Download aria-hidden="true" size={16} />
                              <span>导出引用</span>
                            </button>
                            <button
                              className="mentor-reference-handoff"
                              type="button"
                              onClick={handleSendReferencesToWriter}
                              disabled={!mentorCandidateReferences.length || isWriterDrafting}
                            >
                              {isWriterDrafting ? (
                                <Loader2 aria-hidden="true" className="spin" size={16} />
                              ) : (
                                <FileText aria-hidden="true" size={16} />
                              )}
                              <span>交给 Alex Writer</span>
                            </button>
                          </div>
                        </section>
                        <section className="mentor-brief-section mentor-next-steps">
                          <div className="mentor-section-head">
                            <strong>下一步行动</strong>
                            <span>把建议转成方案和数据准备</span>
                          </div>
                        <div className="mentor-next-steps-list">
                          {mentorRecommendationReport.next_steps.map((step) => (
                            <p key={step}>{step}</p>
                          ))}
                        </div>
                        </section>
                      </div>
                    ) : null}
                  </section>
                ) : null}

                {shouldShowWriterWorkspace ? (
                  <section className="writer-panel" aria-label="Alex Writer 写作工作区">
                    <div className="writer-head">
                      <div>
                        <p className="eyebrow">Alex Writer</p>
                        <h3>写作工作区</h3>
                      </div>
                      <div className="writer-head-actions">
                        <button type="button" onClick={handleDownloadWriterOutline} disabled={!writerOutlineDraft}>
                          <Download aria-hidden="true" size={15} />
                          <span>导出提纲</span>
                        </button>
                        <button type="button" onClick={handleDownloadIntroductionDraft}>
                          <Download aria-hidden="true" size={15} />
                          <span>导出正文</span>
                        </button>
                        <button
                          type="button"
                          onClick={handleDownloadMethodsResultsDraft}
                          disabled={!writerMethodsResultsDraft}
                        >
                          <Download aria-hidden="true" size={15} />
                          <span>导出结果</span>
                        </button>
                        <FileText aria-hidden="true" size={20} />
                      </div>
                    </div>

                    <div className="writer-outline-grid">
                      <section className="writer-outline-card">
                        <div className="mentor-section-head">
                          <strong>Introduction 段落骨架</strong>
                          <span>{writerOutlineDraft ? "来自候选引用" : "等待候选引用"}</span>
                        </div>
                        {writerOutlineDraft ? (
                          <div className="writer-outline-list">
                            {writerOutlineDraft.introductionParagraphs.map((paragraph) => (
                              <article key={paragraph.title}>
                                <strong>{paragraph.title}</strong>
                                <p>{paragraph.purpose}</p>
                                <small>{paragraph.writingCue}</small>
                              </article>
                            ))}
                          </div>
                        ) : (
                          <p className="writer-empty">
                            先在 Mentor 中将候选文献标记为“确认可用”，这里会生成 Introduction 段落骨架。
                          </p>
                        )}
                      </section>

                      <section className="writer-outline-card">
                        <div className="mentor-section-head">
                          <strong>Discussion</strong>
                          <span>等待数据结果</span>
                        </div>
                        {writerOutlineDraft ? (
                          <p className="writer-empty">{writerOutlineDraft.discussionDeferredNote}</p>
                        ) : (
                          <p className="writer-empty">
                            Discussion 将在 Dr. Data Lin 完成正式结果确认后生成。
                          </p>
                        )}
                      </section>
                    </div>

                    <section className="writer-methods-results-card">
                      <div className="mentor-section-head">
                        <strong>Methods / Results 草稿</strong>
                        <span>{writerMethodsResultsDraft ? "来自 Data Lin" : "等待统计结果"}</span>
                      </div>
                      {writerMethodsResultsDraft ? (
                        <>
                        {workflowSummary ? (
                          <div className="writer-source-strip">
                            <span>{workflowSummary.fileName}</span>
                            <span>
                              {workflowSummary.rowCount} 行 / {workflowSummary.columnCount} 列
                            </span>
                            <span>{workflowSummary.saved ? "来自已保存记录" : "尚未保存"}</span>
                            <span>
                              {workflowSummary.source === "restored"
                                ? "已恢复"
                                : workflowSummary.source === "prepared"
                                  ? "预备 DATA"
                                  : "手动 CSV"}
                            </span>
                          </div>
                        ) : null}
                        <div className="writer-methods-results-layout">
                          <article>
                            <strong>Methods</strong>
                            {writerMethodsResultsDraft.methodsParagraphs.map((paragraph) => (
                              <p key={paragraph}>{paragraph}</p>
                            ))}
                          </article>
                          <article>
                            <strong>Results</strong>
                            {writerMethodsResultsDraft.resultsParagraphs.map((paragraph) => (
                              <p key={paragraph}>{paragraph}</p>
                            ))}
                          </article>
                          <article>
                            <strong>正式检验</strong>
                            <ul>
                              {writerMethodsResultsDraft.formalTestLines.map((line) => (
                                <li key={line}>{line}</li>
                              ))}
                            </ul>
                          </article>
                          <article>
                            <strong>待补充</strong>
                            <ul>
                              {(writerMethodsResultsDraft.missingItems.length
                                ? writerMethodsResultsDraft.missingItems
                                : ["当前没有系统识别出的阻断项；正式投稿前仍需人工复核。"]
                              ).map((item) => (
                                <li key={item}>{item}</li>
                              ))}
                            </ul>
                          </article>
                          {writerMethodsResultsDraft.chartLines.length ? (
                            <article className="writer-methods-results-wide">
                              <strong>图表摘要</strong>
                              <ul>
                                {writerMethodsResultsDraft.chartLines.map((line) => (
                                  <li key={line}>{line}</li>
                                ))}
                              </ul>
                            </article>
                          ) : null}
                        </div>
                        </>
                      ) : (
                        <p className="writer-empty">
                          先在 Dr. Data Lin 中加载预备 DATA 或上传脱敏 CSV，并生成统计草案；这里会整理 Methods
                          和 Results 写作草稿。
                        </p>
                      )}
                    </section>

                    <section className="writer-draft-card">
                      <div className="mentor-section-head">
                        <strong>Introduction 草稿</strong>
                        <span>
                          {isWriterDraftLoading
                            ? "读取中"
                            : writerIntroductionDraft?.updated_at
                              ? `已保存 ${new Date(writerIntroductionDraft.updated_at).toLocaleString("zh-CN")}`
                              : "本地项目草稿"}
                        </span>
                      </div>
                      <div className="writer-draft-grid">
                        <label>
                          <span>背景段</span>
                          <textarea
                            value={writerIntroductionDraftForm.background_paragraph}
                            placeholder={
                              writerOutlineDraft?.introductionParagraphs[0]?.writingCue ??
                              "概括研究方向的现实意义和候选文献背景。"
                            }
                            disabled={!canEditSelectedProject || isWriterDraftLoading}
                            onChange={(event) =>
                              setWriterIntroductionDraftForm((current) => ({
                                ...current,
                                background_paragraph: event.currentTarget.value,
                              }))
                            }
                          />
                        </label>
                        <label>
                          <span>研究空白段</span>
                          <textarea
                            value={writerIntroductionDraftForm.gap_paragraph}
                            placeholder={
                              writerOutlineDraft?.introductionParagraphs[1]?.writingCue ??
                              "指出既有研究尚未覆盖的本中心、本设备、本流程或本数据问题。"
                            }
                            disabled={!canEditSelectedProject || isWriterDraftLoading}
                            onChange={(event) =>
                              setWriterIntroductionDraftForm((current) => ({
                                ...current,
                                gap_paragraph: event.currentTarget.value,
                              }))
                            }
                          />
                        </label>
                        <label>
                          <span>研究目的段</span>
                          <textarea
                            value={writerIntroductionDraftForm.objective_paragraph}
                            placeholder={
                              writerOutlineDraft?.introductionParagraphs[2]?.writingCue ??
                              "收束到本研究的具体问题、对象和主要终点。"
                            }
                            disabled={!canEditSelectedProject || isWriterDraftLoading}
                            onChange={(event) =>
                              setWriterIntroductionDraftForm((current) => ({
                                ...current,
                                objective_paragraph: event.currentTarget.value,
                              }))
                            }
                          />
                        </label>
                      </div>
                      <div className="writer-draft-actions">
                        <small>
                          草稿会保存到当前项目；候选引用和段落内容仍需人工核对后再进入正式论文。
                        </small>
                        <button
                          type="button"
                          onClick={handleSaveWriterIntroductionDraft}
                          disabled={!canEditSelectedProject || isWriterDraftSaving || isWriterDraftLoading}
                        >
                          {isWriterDraftSaving ? (
                            <Loader2 aria-hidden="true" className="spin" size={15} />
                          ) : (
                            <Save aria-hidden="true" size={15} />
                          )}
                          <span>{isWriterDraftSaving ? "保存中" : "保存草稿"}</span>
                        </button>
                      </div>
                      <div className="writer-citation-audit">
                        <div className="mentor-section-head">
                          <strong>引用使用清单</strong>
                          <span>{introductionCitationUsages.length} 条可追溯标记</span>
                        </div>
                        {introductionCitationUsages.length ? (
                          <div className="writer-citation-audit-list">
                            {introductionCitationUsages.map((usage) => (
                              <article
                                className={usage.count > 1 ? "is-duplicate" : undefined}
                                key={usage.key}
                              >
                                <strong>{usage.label}</strong>
                                <small>
                                  出现 {usage.count} 次 · 位于 {usage.sections.join(" / ")}
                                </small>
                                {usage.count > 1 ? (
                                  <em>重复使用，需人工确认是否必要。</em>
                                ) : null}
                              </article>
                            ))}
                          </div>
                        ) : (
                          <p className="writer-empty">当前 Introduction 草稿还没有 PMID 或 DOI 追溯标记。</p>
                        )}
                        {introductionSectionsWithoutCitation.length ? (
                          <p className="writer-citation-warning">
                            {introductionSectionsWithoutCitation.join("、")}已有文字，但尚无 PMID / DOI
                            追溯标记或手动绑定。
                          </p>
                        ) : null}
                        <div className="writer-citation-quality">
                          <div className="mentor-section-head">
                            <strong>引用质控摘要</strong>
                            <span>{introductionCitationQualityIssues.length} 项待核对</span>
                          </div>
                          {citationQualityNotice ? (
                            <p className="writer-citation-quality-notice">{citationQualityNotice}</p>
                          ) : null}
                          {introductionCitationQualityIssues.length ? (
                            <div className="writer-citation-quality-list">
                              {introductionCitationQualityIssues.map((issue) => (
                                <article key={issue.key}>
                                  <span>{issue.category}</span>
                                  <strong>
                                    {issue.fieldLabel} / {issue.referenceLabel}
                                  </strong>
                                  <small>{issue.message}</small>
                                  <em>{issue.suggestion}</em>
                                  {issue.action ? (
                                    <div className="writer-citation-quality-actions">
                                      {issue.action.kind === "mark-introduction-use" ? (
                                        <button
                                          type="button"
                                          onClick={() =>
                                            issue.action?.kind === "mark-introduction-use"
                                              ? handleCitationQualityMarkIntroductionUse(issue.key, issue.action)
                                              : undefined
                                          }
                                          disabled={
                                            !canEditSelectedProject ||
                                            !selectedProjectId ||
                                            updatingCitationQualityActionKey === issue.key
                                          }
                                        >
                                          {updatingCitationQualityActionKey === issue.key
                                            ? "保存中..."
                                            : "标记为 Introduction 用途"}
                                        </button>
                                      ) : null}
                                      {issue.action.kind === "remove-binding" ? (
                                        <button
                                          type="button"
                                          onClick={() =>
                                            issue.action?.kind === "remove-binding"
                                              ? handleCitationQualityRemoveBinding(issue.action)
                                              : undefined
                                          }
                                          disabled={!canEditSelectedProject || Boolean(updatingCitationQualityActionKey)}
                                        >
                                          移除该绑定
                                        </button>
                                      ) : null}
                                    </div>
                                  ) : null}
                                </article>
                              ))}
                            </div>
                          ) : (
                            <div className="writer-empty">
                              <p>当前字段级引用映射未发现引用质控风险。</p>
                              <small>
                                快速处理按钮只会在“用途标记”或“绑定异常”风险出现时显示。
                              </small>
                            </div>
                          )}
                        </div>
                        <div className="writer-field-citation-map">
                          <div className="mentor-section-head">
                            <strong>字段级引用映射</strong>
                            <span>
                              {introductionFieldCitationMaps.reduce(
                                (total, fieldMap) =>
                                  total + fieldMap.matchedReferences.length + fieldMap.manualReferences.length,
                                0,
                              )}{" "}
                              条自动/手动匹配
                            </span>
                          </div>
                          <div className="writer-field-citation-list">
                            {introductionFieldCitationMaps.map((fieldMap) => (
                              <article
                                className={fieldMap.missingTrace ? "is-missing-trace" : undefined}
                                key={fieldMap.field}
                              >
                                <div className="writer-field-citation-head">
                                  <strong>{fieldMap.label}</strong>
                                  <small>
                                    {fieldMap.usages.length} 条标记 · {fieldMap.matchedReferences.length} 条自动匹配 ·{" "}
                                    {fieldMap.manualReferences.length} 条手动绑定
                                  </small>
                                </div>
                                {!fieldMap.hasText ? <p>该段尚未撰写。</p> : null}
                                {fieldMap.missingTrace ? (
                                  <em>该段已有文字，但还没有 PMID / DOI 追溯标记。</em>
                                ) : null}
                                {fieldMap.matchedReferences.length ? (
                                  <div className="writer-field-citation-items">
                                    {fieldMap.matchedReferences.map((item) => {
                                      const evidence = item.evidence;
                                      return (
                                        <div key={item.usage.key}>
                                          <strong>{item.usage.label}</strong>
                                          <small>
                                            {evidence?.title ??
                                              evidence?.vancouver_citation ??
                                              evidence?.citation_text ??
                                              "候选文献信息待补充"}
                                          </small>
                                          <small>
                                            全文核对：{evidence?.full_text_checked ? "是" : "否"} ·
                                            Introduction 用途：
                                            {evidence?.use_in_introduction ? "是" : "否"}
                                          </small>
                                          {item.cardTitle ? <small>来源课题：{item.cardTitle}</small> : null}
                                        </div>
                                      );
                                    })}
                                  </div>
                                ) : null}
                                {fieldMap.manualReferences.length ? (
                                  <div className="writer-field-citation-items writer-field-citation-manual">
                                    {fieldMap.manualReferences.map((item) => {
                                      const evidence = item.evidence;
                                      return (
                                        <div key={`manual-${item.usage.key}`}>
                                          <strong>手动绑定：{item.usage.label}</strong>
                                          <small>
                                            {evidence?.title ??
                                              evidence?.vancouver_citation ??
                                              evidence?.citation_text ??
                                              "候选文献信息待补充"}
                                          </small>
                                          <small>
                                            全文核对：{evidence?.full_text_checked ? "是" : "否"} ·
                                            Introduction 用途：
                                            {evidence?.use_in_introduction ? "是" : "否"}
                                          </small>
                                          {item.cardTitle ? <small>来源课题：{item.cardTitle}</small> : null}
                                        </div>
                                      );
                                    })}
                                  </div>
                                ) : null}
                                {fieldMap.unmatchedUsages.length ? (
                                  <div className="writer-field-citation-unmatched">
                                    {fieldMap.unmatchedUsages.map((usage) => (
                                      <em key={usage.key}>{usage.label} 未匹配到当前候选引用。</em>
                                    ))}
                                  </div>
                                ) : null}
                                {fieldMap.unmatchedBindingKeys.length ? (
                                  <div className="writer-field-citation-unmatched">
                                    {fieldMap.unmatchedBindingKeys.map((key) => (
                                      <em key={`manual-${key}`}>
                                        手动绑定 {formatCitationBindingKey(key)} 未匹配到当前候选引用。
                                      </em>
                                    ))}
                                  </div>
                                ) : null}
                              </article>
                            ))}
                          </div>
                        </div>
                      </div>
                    </section>

                    <section className="writer-reference-card">
                      <div className="mentor-section-head">
                        <strong>候选引用</strong>
                        <span>{mentorCandidateReferences.length} 条确认可用</span>
                      </div>
                      {mentorCandidateReferences.length ? (
                        <div className="writer-reference-list">
                          {mentorCandidateReferences.map(({ cardTitle, evidence }, index) => (
                            <article key={`${cardTitle}-${evidence.pmid ?? evidence.search_query}-${index}`}>
                              <strong>{evidence.title ?? evidence.evidence_summary}</strong>
                              <small>
                                {[evidence.journal, evidence.publication_year, evidence.pmid ? `PMID ${evidence.pmid}` : null]
                                  .filter(Boolean)
                                  .join(" · ") || "来源信息待补充"}
                              </small>
                              {evidence.citation_text ? (
                                <small>候选引用：{evidence.citation_text}</small>
                              ) : null}
                              <small>{formatMentorCitationDetails(evidence)}</small>
                              {evidence.vancouver_citation ? (
                                <small>Vancouver 候选引用：{evidence.vancouver_citation}</small>
                              ) : null}
                              <small>用于：{cardTitle}</small>
                              <div className="writer-reference-insert-actions">
                                {[
                                  { field: "background_paragraph" as const, label: "插入背景" },
                                  { field: "gap_paragraph" as const, label: "插入空白" },
                                  { field: "objective_paragraph" as const, label: "插入目的" },
                                ].map((option) => (
                                  <button
                                    type="button"
                                    key={option.field}
                                    onClick={() => handleInsertSemanticCitation(option.field, evidence)}
                                    disabled={!canEditSelectedProject || isWriterDraftLoading}
                                  >
                                    {option.label}
                                  </button>
                                ))}
                              </div>
                              <div className="writer-reference-binding-actions" aria-label="手动绑定引用字段">
                                {[
                                  { field: "background_paragraph" as const, label: "绑定背景" },
                                  { field: "gap_paragraph" as const, label: "绑定空白" },
                                  { field: "objective_paragraph" as const, label: "绑定目的" },
                                ].map((option) => (
                                  <label key={option.field}>
                                    <input
                                      type="checkbox"
                                      checked={isReferenceBoundToField(option.field, evidence)}
                                      disabled={!canEditSelectedProject || isWriterDraftLoading}
                                      onChange={(event) =>
                                        handleToggleManualCitationBinding(
                                          option.field,
                                          evidence,
                                          event.currentTarget.checked,
                                        )
                                      }
                                    />
                                    <span>{option.label}</span>
                                  </label>
                                ))}
                              </div>
                            </article>
                          ))}
                        </div>
                      ) : (
                        <p className="writer-empty">暂无确认可用的候选引用。</p>
                      )}
                    </section>

                    <section className="writer-reference-card">
                      <div className="mentor-section-head">
                        <strong>仍需补充</strong>
                        <span>写作前检查</span>
                      </div>
                      {writerOutlineDraft ? (
                        <div className="writer-outline-list">
                          {writerOutlineDraft.remainingChecks.map((item) => (
                            <p key={item}>{item}</p>
                          ))}
                        </div>
                      ) : (
                        <p className="writer-empty">确认候选引用后会生成检查清单。</p>
                      )}
                    </section>

                    <button
                      className="writer-handoff-button"
                      type="button"
                      onClick={handleSendReferencesToWriter}
                      disabled={!mentorCandidateReferences.length || isWriterDrafting}
                    >
                      {isWriterDrafting ? (
                        <Loader2 aria-hidden="true" className="spin" size={16} />
                      ) : (
                        <FileText aria-hidden="true" size={16} />
                      )}
                      <span>生成聊天草稿</span>
                    </button>
                  </section>
                ) : null}

                {shouldShowReviewerWorkspace ? (
                  <section className="reviewer-panel" aria-label="Rev. Dr. Helena Skov 审稿工作区">
                    <div className="reviewer-head">
                      <div>
                        <p className="eyebrow">Rev. Dr. Helena Skov</p>
                        <h3>投稿前审稿清单</h3>
                        <small>规则型自查：科学性、数据、统计、写作和引用边界。</small>
                      </div>
                      <button type="button" onClick={handleDownloadReviewerReport}>
                        <Download aria-hidden="true" size={15} />
                        <span>导出清单</span>
                      </button>
                    </div>

                    <div className="reviewer-summary-grid">
                      <article className="risk-red">
                        <span>高风险</span>
                        <strong>{reviewerChecks.filter((item) => item.severity === "red").length}</strong>
                      </article>
                      <article className="risk-orange">
                        <span>需复核</span>
                        <strong>{reviewerChecks.filter((item) => item.severity === "orange").length}</strong>
                      </article>
                      <article className="risk-green">
                        <span>已通过</span>
                        <strong>{reviewerChecks.filter((item) => item.severity === "green").length}</strong>
                      </article>
                    </div>

                    <div className="reviewer-check-list">
                      {reviewerChecks.map((item) => (
                        <article className={`reviewer-check-item risk-${item.severity}`} key={item.title}>
                          <div className="reviewer-check-head">
                            <div>
                              <span className={`status-badge risk-${item.severity}`}>
                                {riskLabels[item.severity]}
                              </span>
                              <strong>{item.title}</strong>
                            </div>
                            <small>{item.status}</small>
                          </div>
                          <p>{item.detail}</p>
                          <em>{item.recommendation}</em>
                        </article>
                      ))}
                    </div>

                    <section className="reviewer-boundary-note">
                      <strong>审稿边界</strong>
                      <p>
                        这是投稿前规则自查，不替代真实同行评审。红色项目应先处理；橙色项目进入正式投稿前需人工复核。
                      </p>
                    </section>
                  </section>
                ) : null}

                {!shouldShowMentorWorkspace &&
                !shouldShowProtocolWorkspace &&
                !shouldShowDataWorkspace &&
                !shouldShowWriterWorkspace &&
                !shouldShowReviewerWorkspace ? (
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

                  </div>
                </div>
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

        </div>
      )}
    </main>
  );
}

export default App;
