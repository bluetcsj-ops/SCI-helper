from sqlalchemy import select

from app.data.models import (
    DataAnalysisRecord,
    DataAnalysisRecordCreate,
    DataQualityReport,
    DataStatisticsReport,
)
from app.db.models import DataAnalysisRecordRecord
from app.db.session import SessionLocal


class DataAnalysisRecordRepository:
    def list_records(self, project_id: str) -> list[DataAnalysisRecord]:
        with SessionLocal() as session:
            records = session.scalars(
                select(DataAnalysisRecordRecord)
                .where(DataAnalysisRecordRecord.project_id == project_id)
                .order_by(DataAnalysisRecordRecord.created_at.desc())
            ).all()
            return [self._to_record(record) for record in records]

    def save_record(
        self,
        project_id: str,
        payload: DataAnalysisRecordCreate,
    ) -> DataAnalysisRecord:
        quality_report = payload.quality_report
        statistics_report = payload.statistics_report

        with SessionLocal() as session:
            record = DataAnalysisRecordRecord(
                project_id=project_id,
                file_name=payload.file_name,
                row_count=quality_report.row_count,
                column_count=quality_report.column_count,
                issue_count=len(quality_report.issues),
                chart_count=len(statistics_report.chart_specs) if statistics_report else 0,
                quality_report_json=quality_report.model_dump_json(),
                statistics_report_json=(
                    statistics_report.model_dump_json() if statistics_report is not None else None
                ),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return self._to_record(record)

    def _to_record(self, record: DataAnalysisRecordRecord) -> DataAnalysisRecord:
        statistics_report = (
            DataStatisticsReport.model_validate_json(record.statistics_report_json)
            if record.statistics_report_json
            else None
        )
        return DataAnalysisRecord(
            id=record.id,
            project_id=record.project_id,
            file_name=record.file_name,
            row_count=record.row_count,
            column_count=record.column_count,
            issue_count=record.issue_count,
            chart_count=record.chart_count,
            quality_report=DataQualityReport.model_validate_json(record.quality_report_json),
            statistics_report=statistics_report,
            created_at=record.created_at,
        )


data_analysis_record_repository = DataAnalysisRecordRepository()
