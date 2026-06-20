import type {
  AgentProfile,
  AdvancedModelFitReport,
  AdvancedModelPlan,
  ChatRequest,
  ChatResponse,
  DataAuditLog,
  DataAnalysisRecord,
  DataAnalysisRecordCreate,
  DataQualityReport,
  DataRequirementSpec,
  DataStatisticsReport,
  FormalTestConfirmation,
  FormalTestReport,
  DashboardSummary,
  ItemStatus,
  MentorEvidenceReview,
  MentorEvidenceReviewUpdate,
  MentorRecommendationResponse,
  MentorTrendSnapshot,
  Project,
  ProjectAccessPolicy,
  ProjectPlanDraft,
  ProjectProtocol,
  ProjectProtocolUpdate,
  ProjectReminderSummary,
  ReviewerCommentThread,
  ReviewerCommentThreadUpdate,
  UserProfile,
  WriterDraftVersion,
  WriterDraftVersionCreate,
  WriterIntroductionDraft,
  WriterIntroductionDraftUpdate,
} from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

export interface FormalTestOptions {
  pairedTest?: boolean;
  pairedDataLayout?: "wide" | "long";
  pairedAnalysis?: "paired_t" | "friedman" | "rm_anova";
  pairedSubjectColumn?: string;
  pairedConditionColumn?: string;
  pairedConditionA?: string;
  pairedConditionB?: string;
  pairedConditions?: string[];
  multiplicityCorrection?: "holm" | "fdr";
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getDashboard(): Promise<DashboardSummary> {
  return request<DashboardSummary>("/api/dashboard/");
}

export function getMentorTrendSnapshot(): Promise<MentorTrendSnapshot> {
  return request<MentorTrendSnapshot>("/api/mentor/trends");
}

export function getMentorRecommendations(payload: {
  equipment_summary: string;
  planning_systems: string;
  programming_level: string;
  data_types: string[];
  weekly_hours: number;
  publication_experience: string;
  interest_topics: string[];
}): Promise<MentorRecommendationResponse> {
  return request<MentorRecommendationResponse>("/api/mentor/recommendations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getMentorEvidenceReviews(projectId: string): Promise<MentorEvidenceReview[]> {
  return request<MentorEvidenceReview[]>(`/api/projects/${projectId}/mentor/evidence-reviews`);
}

export function saveMentorEvidenceReview(
  projectId: string,
  payload: MentorEvidenceReviewUpdate,
): Promise<MentorEvidenceReview> {
  return request<MentorEvidenceReview>(`/api/projects/${projectId}/mentor/evidence-reviews`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function getWriterIntroductionDraft(projectId: string): Promise<WriterIntroductionDraft> {
  return request<WriterIntroductionDraft>(`/api/projects/${projectId}/writer/introduction-draft`);
}

export function saveWriterIntroductionDraft(
  projectId: string,
  payload: WriterIntroductionDraftUpdate,
): Promise<WriterIntroductionDraft> {
  return request<WriterIntroductionDraft>(`/api/projects/${projectId}/writer/introduction-draft`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function getWriterDraftVersions(projectId: string): Promise<WriterDraftVersion[]> {
  return request<WriterDraftVersion[]>(`/api/projects/${projectId}/writer/versions`);
}

export function createWriterDraftVersion(
  projectId: string,
  payload: WriterDraftVersionCreate,
): Promise<WriterDraftVersion> {
  return request<WriterDraftVersion>(`/api/projects/${projectId}/writer/versions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function restoreWriterDraftVersion(
  projectId: string,
  versionId: number,
): Promise<WriterIntroductionDraft> {
  return request<WriterIntroductionDraft>(
    `/api/projects/${projectId}/writer/versions/${versionId}/restore`,
    {
      method: "POST",
    },
  );
}

export function getReviewerCommentThreads(projectId: string): Promise<ReviewerCommentThread[]> {
  return request<ReviewerCommentThread[]>(`/api/projects/${projectId}/reviewer/comment-threads`);
}

export function importReviewerCommentThreads(
  projectId: string,
  rawText: string,
): Promise<ReviewerCommentThread[]> {
  return request<ReviewerCommentThread[]>(
    `/api/projects/${projectId}/reviewer/comment-threads/import`,
    {
      method: "POST",
      body: JSON.stringify({ raw_text: rawText }),
    },
  );
}

export function updateReviewerCommentThread(
  projectId: string,
  threadId: number,
  payload: ReviewerCommentThreadUpdate,
): Promise<ReviewerCommentThread> {
  return request<ReviewerCommentThread>(
    `/api/projects/${projectId}/reviewer/comment-threads/${threadId}`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
  );
}

export function getCurrentUser(): Promise<UserProfile> {
  return request<UserProfile>("/api/users/me");
}

export function getProjects(): Promise<Project[]> {
  return request<Project[]>("/api/projects/");
}

export function getProjectAccess(projectId: string): Promise<ProjectAccessPolicy> {
  return request<ProjectAccessPolicy>(`/api/projects/${projectId}/access`);
}

export function getProjectProtocol(projectId: string): Promise<ProjectProtocol> {
  return request<ProjectProtocol>(`/api/projects/${projectId}/protocol`);
}

export function saveProjectProtocol(
  projectId: string,
  requestBody: ProjectProtocolUpdate,
): Promise<ProjectProtocol> {
  return request<ProjectProtocol>(`/api/projects/${projectId}/protocol`, {
    method: "PUT",
    body: JSON.stringify(requestBody),
  });
}

export function draftProjectProtocol(projectId: string): Promise<ProjectProtocol> {
  return request<ProjectProtocol>(`/api/projects/${projectId}/protocol/draft`, {
    method: "POST",
  });
}

export function extractProjectProtocol(
  projectId: string,
  sourceText: string,
): Promise<ProjectProtocol> {
  return request<ProjectProtocol>(`/api/projects/${projectId}/protocol/extract`, {
    method: "POST",
    body: JSON.stringify({ source_text: sourceText }),
  });
}

export function getProjectPlanDrafts(projectId: string): Promise<ProjectPlanDraft[]> {
  return request<ProjectPlanDraft[]>(`/api/projects/${projectId}/plan/drafts`);
}

export function generateProjectPlanDraftFromProtocol(projectId: string): Promise<ProjectPlanDraft> {
  return request<ProjectPlanDraft>(`/api/projects/${projectId}/plan/drafts/from-protocol`, {
    method: "POST",
  });
}

export function applyProjectPlanDraft(projectId: string, draftId: number): Promise<Project> {
  return request<Project>(`/api/projects/${projectId}/plan/drafts/${draftId}/apply`, {
    method: "POST",
  });
}

export function getProjectReminders(projectId: string): Promise<ProjectReminderSummary> {
  return request<ProjectReminderSummary>(`/api/projects/${projectId}/reminders`);
}

export function getDataRequirements(projectId: string): Promise<DataRequirementSpec> {
  return request<DataRequirementSpec>(`/api/projects/${projectId}/data/requirements`);
}

export function getDataAnalysisRecords(projectId: string): Promise<DataAnalysisRecord[]> {
  return request<DataAnalysisRecord[]>(`/api/projects/${projectId}/data/analysis-records`);
}

export function getDataAuditLogs(projectId: string): Promise<DataAuditLog[]> {
  return request<DataAuditLog[]>(`/api/projects/${projectId}/data/audit-logs`);
}

export function saveDataAnalysisRecord(
  projectId: string,
  requestBody: DataAnalysisRecordCreate,
): Promise<DataAnalysisRecord> {
  return request<DataAnalysisRecord>(`/api/projects/${projectId}/data/analysis-records`, {
    method: "POST",
    body: JSON.stringify(requestBody),
  });
}

export async function uploadDataQualityReport(
  projectId: string,
  file: File,
): Promise<DataQualityReport> {
  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/data/quality-report?file_name=${encodeURIComponent(
      file.name,
    )}`,
    {
      method: "POST",
      headers: {
        "Content-Type": file.type || "text/csv",
      },
      body: file,
    },
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<DataQualityReport>;
}

export async function uploadDataStatisticsReport(
  projectId: string,
  file: File,
  groupColumn: string,
  outcomeColumns: string[],
): Promise<DataStatisticsReport> {
  const params = new URLSearchParams({ file_name: file.name });
  if (groupColumn) {
    params.set("group_column", groupColumn);
  }
  if (outcomeColumns.length) {
    params.set("outcome_columns", outcomeColumns.join(","));
  }

  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/data/statistics-report?${params.toString()}`,
    {
      method: "POST",
      headers: {
        "Content-Type": file.type || "text/csv",
      },
      body: file,
    },
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<DataStatisticsReport>;
}

export async function uploadAdvancedModelPlan(
  projectId: string,
  file: File,
  groupColumn: string,
  outcomeColumns: string[],
): Promise<AdvancedModelPlan> {
  const params = new URLSearchParams({ file_name: file.name });
  if (groupColumn) {
    params.set("group_column", groupColumn);
  }
  if (outcomeColumns.length) {
    params.set("outcome_columns", outcomeColumns.join(","));
  }

  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/data/model-plan?${params.toString()}`,
    {
      method: "POST",
      headers: {
        "Content-Type": file.type || "text/csv",
      },
      body: file,
    },
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<AdvancedModelPlan>;
}

export async function uploadAdvancedModelFitReport(
  projectId: string,
  file: File,
  groupColumn: string,
  outcomeColumns: string[],
  confirmation: FormalTestConfirmation,
  modelId = "linear_regression",
): Promise<AdvancedModelFitReport> {
  const params = new URLSearchParams({
    file_name: file.name,
    model_id: modelId,
    outcome_columns: outcomeColumns.join(","),
    confirmed_by: confirmation.confirmed_by,
    design_confirmed: String(confirmation.design_confirmed),
    endpoints_confirmed: String(confirmation.endpoints_confirmed),
    deidentified_confirmed: String(confirmation.deidentified_confirmed),
    missing_data_reviewed: String(confirmation.missing_data_reviewed),
    assumptions_reviewed: String(confirmation.assumptions_reviewed),
    multiplicity_reviewed: String(confirmation.multiplicity_reviewed),
    notes: confirmation.notes,
  });
  if (groupColumn) {
    params.set("group_column", groupColumn);
  }

  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/data/model-fit?${params.toString()}`,
    {
      method: "POST",
      headers: {
        "Content-Type": file.type || "text/csv",
      },
      body: file,
    },
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<AdvancedModelFitReport>;
}

export async function uploadFormalTestReport(
  projectId: string,
  file: File,
  groupColumn: string,
  outcomeColumns: string[],
  confirmation: FormalTestConfirmation,
  options: FormalTestOptions = {},
): Promise<FormalTestReport> {
  const params = new URLSearchParams({
    file_name: file.name,
    outcome_columns: outcomeColumns.join(","),
    paired_test: String(options.pairedTest ?? false),
    paired_data_layout: options.pairedDataLayout ?? "wide",
    paired_analysis: options.pairedAnalysis ?? "paired_t",
    multiplicity_correction: options.multiplicityCorrection ?? "holm",
    confirmed_by: confirmation.confirmed_by,
    design_confirmed: String(confirmation.design_confirmed),
    endpoints_confirmed: String(confirmation.endpoints_confirmed),
    deidentified_confirmed: String(confirmation.deidentified_confirmed),
    missing_data_reviewed: String(confirmation.missing_data_reviewed),
    assumptions_reviewed: String(confirmation.assumptions_reviewed),
    multiplicity_reviewed: String(confirmation.multiplicity_reviewed),
    notes: confirmation.notes,
  });
  if (groupColumn) {
    params.set("group_column", groupColumn);
  }
  if (options.pairedSubjectColumn) {
    params.set("paired_subject_column", options.pairedSubjectColumn);
  }
  if (options.pairedConditionColumn) {
    params.set("paired_condition_column", options.pairedConditionColumn);
  }
  if (options.pairedConditionA) {
    params.set("paired_condition_a", options.pairedConditionA);
  }
  if (options.pairedConditionB) {
    params.set("paired_condition_b", options.pairedConditionB);
  }
  if (options.pairedConditions?.length) {
    params.set("paired_conditions", options.pairedConditions.join(","));
  }

  const response = await fetch(
    `${API_BASE_URL}/api/projects/${projectId}/data/formal-test-report?${params.toString()}`,
    {
      method: "POST",
      headers: {
        "Content-Type": file.type || "text/csv",
      },
      body: file,
    },
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<FormalTestReport>;
}

export function refreshProjectReminders(projectId: string): Promise<ProjectReminderSummary> {
  return request<ProjectReminderSummary>(`/api/projects/${projectId}/reminders/refresh`, {
    method: "POST",
  });
}

export function dismissProjectReminder(
  projectId: string,
  reminderId: number,
): Promise<ProjectReminderSummary> {
  return request<ProjectReminderSummary>(
    `/api/projects/${projectId}/reminders/${reminderId}/dismiss`,
    {
      method: "PATCH",
    },
  );
}

export function getAgents(): Promise<AgentProfile[]> {
  return request<AgentProfile[]>("/api/agents/");
}

export function sendChat(requestBody: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat/", {
    method: "POST",
    body: JSON.stringify(requestBody),
  });
}

export function updateTaskStatus(
  projectId: string,
  taskId: string,
  status: ItemStatus,
): Promise<Project> {
  return request<Project>(`/api/projects/${projectId}/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
