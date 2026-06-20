from sqlalchemy import select

from app.data.models import DataAuditLog
from app.db.models import DataAuditLogRecord
from app.db.session import SessionLocal
from app.projects.models import RiskLevel


class DataAuditLogRepository:
    def list_logs(self, project_id: str, limit: int = 20) -> list[DataAuditLog]:
        with SessionLocal() as session:
            records = session.scalars(
                select(DataAuditLogRecord)
                .where(DataAuditLogRecord.project_id == project_id)
                .order_by(DataAuditLogRecord.created_at.desc())
                .limit(limit)
            ).all()
            return [self._to_log(record) for record in records]

    def record_event(
        self,
        project_id: str,
        action: str,
        summary: str,
        file_name: str | None = None,
        row_count: int = 0,
        column_count: int = 0,
        risk_level: RiskLevel = RiskLevel.green,
        raw_data_saved: bool = False,
    ) -> DataAuditLog:
        with SessionLocal() as session:
            record = DataAuditLogRecord(
                project_id=project_id,
                action=action,
                file_name=file_name,
                row_count=row_count,
                column_count=column_count,
                risk_level=risk_level.value,
                summary=summary,
                raw_data_saved="1" if raw_data_saved else "0",
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_log(record)

    def _to_log(self, record: DataAuditLogRecord) -> DataAuditLog:
        return DataAuditLog(
            id=record.id,
            project_id=record.project_id,
            action=record.action,
            file_name=record.file_name,
            row_count=record.row_count,
            column_count=record.column_count,
            risk_level=RiskLevel(record.risk_level),
            summary=record.summary,
            raw_data_saved=self._coerce_bool(record.raw_data_saved),
            created_at=record.created_at,
        )

    def _coerce_bool(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y"}
        return bool(value)


data_audit_log_repository = DataAuditLogRepository()
