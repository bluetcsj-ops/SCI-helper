import type {
  AgentProfile,
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
  Project,
  ProjectAccessPolicy,
  ProjectPlanDraft,
  ProjectProtocol,
  ProjectProtocolUpdate,
  ProjectReminderSummary,
  UserProfile,
} from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "http://localhost:8000";

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

export async function uploadFormalTestReport(
  projectId: string,
  file: File,
  groupColumn: string,
  outcomeColumns: string[],
  confirmation: FormalTestConfirmation,
): Promise<FormalTestReport> {
  const params = new URLSearchParams({
    file_name: file.name,
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
