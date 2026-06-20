from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.data.models import (
    AdvancedModelFitReport,
    AdvancedModelPlan,
    DataAuditLog,
    DataAnalysisRecord,
    DataAnalysisRecordCreate,
    FormalTestConfirmation,
    FormalTestReport,
    DataQualityReport,
    DataRequirementSpec,
    DataStatisticsReport,
)
from app.data.audit import data_audit_log_repository
from app.data.records import data_analysis_record_repository
from app.data.service import data_workspace_service
from app.projects.models import RiskLevel
from app.projects.repository import project_repository
from app.protocols.repository import protocol_repository
from app.users.dependencies import ensure_project_access, get_current_user
from app.users.models import ProjectAccessLevel, UserProfile


router = APIRouter()


@router.get("/{project_id}/data/requirements", response_model=DataRequirementSpec)
def get_data_requirements(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> DataRequirementSpec:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)

    protocol = protocol_repository.get_protocol(project_id)
    return data_workspace_service.build_requirement_spec(project=project, protocol=protocol)


@router.get("/{project_id}/data/analysis-records", response_model=list[DataAnalysisRecord])
def list_data_analysis_records(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[DataAnalysisRecord]:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)

    return data_analysis_record_repository.list_records(project_id)


@router.get("/{project_id}/data/audit-logs", response_model=list[DataAuditLog])
def list_data_audit_logs(
    project_id: str,
    current_user: UserProfile = Depends(get_current_user),
) -> list[DataAuditLog]:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.viewer)

    return data_audit_log_repository.list_logs(project_id)


@router.post("/{project_id}/data/analysis-records", response_model=DataAnalysisRecord)
def save_data_analysis_record(
    project_id: str,
    request: DataAnalysisRecordCreate,
    current_user: UserProfile = Depends(get_current_user),
) -> DataAnalysisRecord:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    saved_record = data_analysis_record_repository.save_record(project_id=project_id, payload=request)
    data_audit_log_repository.record_event(
        project_id=project_id,
        action="analysis_record_saved",
        file_name=request.file_name,
        row_count=saved_record.row_count,
        column_count=saved_record.column_count,
        risk_level=request.quality_report.privacy_report.risk_level
        if request.quality_report.privacy_report
        else project.risk_level,
        summary="已保存质控和统计报告 JSON；未保存原始 CSV。",
        raw_data_saved=False,
    )
    return saved_record


@router.post("/{project_id}/data/quality-report", response_model=DataQualityReport)
async def create_data_quality_report(
    project_id: str,
    request: Request,
    file_name: str = Query(default="uploaded.csv"),
    current_user: UserProfile = Depends(get_current_user),
) -> DataQualityReport:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="CSV file is required")

    protocol = protocol_repository.get_protocol(project_id)
    try:
        report = data_workspace_service.build_quality_report(
            project=project,
            protocol=protocol,
            file_name=file_name,
            content=content,
        )
        data_audit_log_repository.record_event(
            project_id=project_id,
            action="quality_report_generated",
            file_name=file_name,
            row_count=report.row_count,
            column_count=report.column_count,
            risk_level=report.privacy_report.risk_level if report.privacy_report else project.risk_level,
            summary=report.privacy_report.summary
            if report.privacy_report
            else "已生成 CSV 质量报告；未保存原始 CSV。",
            raw_data_saved=False,
        )
        return report
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{project_id}/data/formal-test-report", response_model=FormalTestReport)
async def create_data_formal_test_report(
    project_id: str,
    request: Request,
    file_name: str = Query(default="uploaded.csv"),
    group_column: str | None = Query(default=None),
    outcome_columns: str = Query(default=""),
    paired_test: bool = Query(default=False),
    paired_data_layout: str = Query(default="wide"),
    paired_analysis: str = Query(default="paired_t"),
    paired_subject_column: str | None = Query(default=None),
    paired_condition_column: str | None = Query(default=None),
    paired_conditions: str = Query(default=""),
    paired_condition_a: str = Query(default=""),
    paired_condition_b: str = Query(default=""),
    multiplicity_correction: str = Query(default="holm"),
    confirmed_by: str = Query(default=""),
    design_confirmed: bool = Query(default=False),
    endpoints_confirmed: bool = Query(default=False),
    deidentified_confirmed: bool = Query(default=False),
    missing_data_reviewed: bool = Query(default=False),
    assumptions_reviewed: bool = Query(default=False),
    multiplicity_reviewed: bool = Query(default=False),
    notes: str = Query(default=""),
    current_user: UserProfile = Depends(get_current_user),
) -> FormalTestReport:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="CSV file is required")

    protocol = protocol_repository.get_protocol(project_id)
    selected_outcomes = [
        column.strip()
        for column in outcome_columns.split(",")
        if column.strip()
    ]
    confirmation = FormalTestConfirmation(
        confirmed_by=confirmed_by,
        design_confirmed=design_confirmed,
        endpoints_confirmed=endpoints_confirmed,
        deidentified_confirmed=deidentified_confirmed,
        missing_data_reviewed=missing_data_reviewed,
        assumptions_reviewed=assumptions_reviewed,
        multiplicity_reviewed=multiplicity_reviewed,
        notes=notes,
    )

    try:
        report = data_workspace_service.build_formal_test_report(
            project=project,
            protocol=protocol,
            file_name=file_name,
            content=content,
            confirmation=confirmation,
            group_column=group_column,
            outcome_columns=selected_outcomes,
            paired_test=paired_test,
            paired_data_layout=paired_data_layout,
            paired_analysis=paired_analysis,
            paired_subject_column=paired_subject_column,
            paired_condition_column=paired_condition_column,
            paired_conditions=[
                value.strip()
                for value in paired_conditions.split(",")
                if value.strip()
            ],
            paired_condition_a=paired_condition_a,
            paired_condition_b=paired_condition_b,
            multiplicity_correction=multiplicity_correction,
        )
        risk_level = (
            RiskLevel.orange
            if any(result.status != "completed" for result in report.results)
            else RiskLevel.green
        )
        data_audit_log_repository.record_event(
            project_id=project_id,
            action="formal_test_executed",
            file_name=file_name,
            row_count=report.row_count,
            column_count=0,
            risk_level=risk_level,
            summary=report.audit_summary,
            raw_data_saved=False,
        )
        return report
    except ValueError as exc:
        data_audit_log_repository.record_event(
            project_id=project_id,
            action="formal_test_blocked",
            file_name=file_name,
            risk_level=RiskLevel.orange,
            summary=f"正式检验未执行：{exc} 未保存原始 CSV。",
            raw_data_saved=False,
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{project_id}/data/statistics-report", response_model=DataStatisticsReport)
async def create_data_statistics_report(
    project_id: str,
    request: Request,
    file_name: str = Query(default="uploaded.csv"),
    group_column: str | None = Query(default=None),
    outcome_columns: str = Query(default=""),
    current_user: UserProfile = Depends(get_current_user),
) -> DataStatisticsReport:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="CSV file is required")

    protocol = protocol_repository.get_protocol(project_id)
    selected_outcomes = [
        column.strip()
        for column in outcome_columns.split(",")
        if column.strip()
    ]
    try:
        privacy_report = data_workspace_service.build_privacy_report_for_csv(content)
        if privacy_report.risk_level.value == "red":
            data_audit_log_repository.record_event(
                project_id=project_id,
                action="statistics_blocked_privacy_risk",
                file_name=file_name,
                row_count=privacy_report.scanned_row_count,
                column_count=privacy_report.scanned_column_count,
                risk_level=privacy_report.risk_level,
                summary="检测到疑似直接身份标识，已阻止统计草案生成；未保存原始 CSV。",
                raw_data_saved=False,
            )
            raise HTTPException(
                status_code=400,
                detail="CSV 含疑似直接身份标识。请先完成脱敏，再生成统计草案。",
            )

        report = data_workspace_service.build_statistics_report(
            project=project,
            protocol=protocol,
            file_name=file_name,
            content=content,
            group_column=group_column,
            outcome_columns=selected_outcomes,
        )
        data_audit_log_repository.record_event(
            project_id=project_id,
            action="statistics_report_generated",
            file_name=file_name,
            row_count=report.row_count,
            column_count=privacy_report.scanned_column_count,
            risk_level=privacy_report.risk_level,
            summary="已生成描述性统计、检验建议和图表规格；未保存原始 CSV。",
            raw_data_saved=False,
        )
        return report
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{project_id}/data/model-plan", response_model=AdvancedModelPlan)
async def create_data_model_plan(
    project_id: str,
    request: Request,
    file_name: str = Query(default="uploaded.csv"),
    group_column: str | None = Query(default=None),
    outcome_columns: str = Query(default=""),
    current_user: UserProfile = Depends(get_current_user),
) -> AdvancedModelPlan:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="CSV file is required")

    protocol = protocol_repository.get_protocol(project_id)
    selected_outcomes = [
        column.strip()
        for column in outcome_columns.split(",")
        if column.strip()
    ]
    try:
        privacy_report = data_workspace_service.build_privacy_report_for_csv(content)
        if privacy_report.risk_level.value == "red":
            raise HTTPException(
                status_code=400,
                detail="CSV 含疑似直接身份标识。请先完成脱敏，再生成高级模型计划。",
            )
        return data_workspace_service.build_advanced_model_plan(
            project=project,
            protocol=protocol,
            file_name=file_name,
            content=content,
            group_column=group_column,
            outcome_columns=selected_outcomes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{project_id}/data/model-fit", response_model=AdvancedModelFitReport)
async def create_data_model_fit_report(
    project_id: str,
    request: Request,
    file_name: str = Query(default="uploaded.csv"),
    model_id: str = Query(default="linear_regression"),
    group_column: str | None = Query(default=None),
    outcome_columns: str = Query(default=""),
    confirmed_by: str = Query(default=""),
    design_confirmed: bool = Query(default=False),
    endpoints_confirmed: bool = Query(default=False),
    deidentified_confirmed: bool = Query(default=False),
    missing_data_reviewed: bool = Query(default=False),
    assumptions_reviewed: bool = Query(default=False),
    multiplicity_reviewed: bool = Query(default=False),
    notes: str = Query(default=""),
    current_user: UserProfile = Depends(get_current_user),
) -> AdvancedModelFitReport:
    project = project_repository.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_access(project_id, current_user, ProjectAccessLevel.editor)

    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="CSV file is required")

    protocol = protocol_repository.get_protocol(project_id)
    selected_outcomes = [
        column.strip()
        for column in outcome_columns.split(",")
        if column.strip()
    ]
    confirmation = FormalTestConfirmation(
        confirmed_by=confirmed_by,
        design_confirmed=design_confirmed,
        endpoints_confirmed=endpoints_confirmed,
        deidentified_confirmed=deidentified_confirmed,
        missing_data_reviewed=missing_data_reviewed,
        assumptions_reviewed=assumptions_reviewed,
        multiplicity_reviewed=multiplicity_reviewed,
        notes=notes,
    )
    try:
        report = data_workspace_service.build_advanced_model_fit_report(
            project=project,
            protocol=protocol,
            file_name=file_name,
            content=content,
            confirmation=confirmation,
            model_id=model_id,
            group_column=group_column,
            outcome_columns=selected_outcomes,
        )
        data_audit_log_repository.record_event(
            project_id=project_id,
            action="advanced_model_fit_executed",
            file_name=file_name,
            row_count=report.complete_case_count,
            column_count=len(report.predictor_columns),
            risk_level=RiskLevel.green,
            summary=report.audit_summary,
            raw_data_saved=False,
        )
        return report
    except ValueError as exc:
        data_audit_log_repository.record_event(
            project_id=project_id,
            action="advanced_model_fit_blocked",
            file_name=file_name,
            risk_level=RiskLevel.orange,
            summary=f"高级模型未执行：{exc} 未保存原始 CSV。",
            raw_data_saved=False,
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
