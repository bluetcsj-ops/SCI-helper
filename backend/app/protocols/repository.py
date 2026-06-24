from sqlalchemy import inspect, select, text

from app.db.models import ProjectProtocolRecord
from app.db.session import Base, SessionLocal, engine
from app.projects.models import Project, ProjectProtocol, ProjectProtocolUpdate


class ProtocolRepository:
    def __init__(self) -> None:
        self._schema_checked = False

    def get_protocol(self, project_id: str) -> ProjectProtocol:
        self._ensure_schema()
        with SessionLocal() as session:
            record = session.scalar(
                select(ProjectProtocolRecord).where(ProjectProtocolRecord.project_id == project_id)
            )
            if record is None:
                return ProjectProtocol(project_id=project_id)
            return self._to_protocol(record)

    def save_protocol(
        self,
        project_id: str,
        payload: ProjectProtocolUpdate,
    ) -> ProjectProtocol:
        self._ensure_schema()
        with SessionLocal() as session:
            record = session.scalar(
                select(ProjectProtocolRecord).where(ProjectProtocolRecord.project_id == project_id)
            )
            if record is None:
                record = ProjectProtocolRecord(project_id=project_id)
                session.add(record)

            self._apply_update(record, payload)
            session.commit()
            return self._to_protocol(record)

    def create_draft(self, project: Project) -> ProjectProtocol:
        existing = self.get_protocol(project.id)
        if self._has_content(existing):
            return existing

        return self.save_protocol(
            project_id=project.id,
            payload=ProjectProtocolUpdate(
                research_question=(
                    f"围绕“{project.topic}”，明确在线流程、剂量学指标或模型预测结果是否能回答"
                    "一个可投稿的放疗物理研究问题。"
                ),
                hypothesis=(
                    "与常规流程或参考计划相比，拟研究方法能够在保持靶区覆盖的同时改善计划质量、"
                    "降低 OAR 剂量或提高工作流可解释性。"
                ),
                study_type="回顾性放疗物理剂量学研究；如涉及模型预测，可扩展为回顾性建模与验证研究。",
                primary_endpoint="主要终点建议设为与课题最直接相关的剂量学或模型性能指标，例如 PTV/CTV D95%、OAR Dmax、Gamma 通过率或预测剂量误差。",
                secondary_endpoints="次要终点包括 HI、CI、D2%、D98%、OAR Vx/Dx、计划失败率、处理时间、不同亚组的稳定性分析。",
                inclusion_criteria="纳入已完成标准治疗流程、数据完整、计划与结构可追溯、具有可导出 DICOM-RT 或结构化计划数据的病例。",
                exclusion_criteria="排除关键 DICOM/剂量/结构数据缺失、治疗流程中断、计划系统版本不可追溯或图像配准质量不可接受的病例。",
                data_requirements="至少需要患者匿名 ID、治疗部位、计划系统版本、RTPLAN、RTDOSE、RTSTRUCT、处方剂量、分割次数、靶区和 OAR 剂量指标。",
                institutional_field_mapping=(
                    "机构适配字段：IRB 编号/豁免依据、数据使用授权、脱敏规则、原始数据保存边界、"
                    "字段字典路径、CSV 导出路径、TPS/计划软件版本、剂量计算算法、机器或 MLC 型号、"
                    "结构命名规则、QA/gamma criteria。"
                ),
                experiment_workflow=(
                    "1. 明确病例筛选标准；2. 导出并脱敏数据；3. 完成数据完整性检查；"
                    "4. 提取剂量学或模型输入变量；5. 执行统计分析；6. 生成图表和方法学记录。"
                ),
                statistical_plan=(
                    "连续变量先做分布检查。配对设计优先考虑配对 t 检验或 Wilcoxon 符号秩检验；"
                    "多组比较考虑 ANOVA 或 Kruskal-Wallis；报告效应量、置信区间和多重比较校正。"
                ),
                target_journals="JACMP、Medical Physics、Physics in Medicine & Biology、Radiotherapy and Oncology、Frontiers in Oncology。",
                rhea_milestones=(
                    "第 1 周完成研究问题和文献矩阵；第 2 周完成数据字段表；"
                    "第 3-6 周完成数据导出和质控；第 7-8 周完成统计分析；第 9-12 周完成初稿。"
                ),
            ),
        )

    def _apply_update(self, record: ProjectProtocolRecord, payload: ProjectProtocolUpdate) -> None:
        for field_name, value in payload.model_dump().items():
            setattr(record, field_name, value)

    def _to_protocol(self, record: ProjectProtocolRecord) -> ProjectProtocol:
        return ProjectProtocol(
            project_id=record.project_id,
            research_question=record.research_question,
            hypothesis=record.hypothesis,
            study_type=record.study_type,
            primary_endpoint=record.primary_endpoint,
            secondary_endpoints=record.secondary_endpoints,
            inclusion_criteria=record.inclusion_criteria,
            exclusion_criteria=record.exclusion_criteria,
            data_requirements=record.data_requirements,
            institutional_field_mapping=record.institutional_field_mapping,
            experiment_workflow=record.experiment_workflow,
            statistical_plan=record.statistical_plan,
            target_journals=record.target_journals,
            rhea_milestones=record.rhea_milestones,
        )

    def _has_content(self, protocol: ProjectProtocol) -> bool:
        return any(
            value.strip()
            for field_name, value in protocol.model_dump().items()
            if field_name != "project_id"
        )

    def _ensure_schema(self) -> None:
        if self._schema_checked:
            return
        table = Base.metadata.tables[ProjectProtocolRecord.__tablename__]
        if engine.dialect.name == "sqlite":
            inspector = inspect(engine)
            if not inspector.has_table(ProjectProtocolRecord.__tablename__):
                table.create(bind=engine, checkfirst=True)
            else:
                existing_columns = {
                    column["name"]
                    for column in inspector.get_columns(ProjectProtocolRecord.__tablename__)
                }
                if "institutional_field_mapping" not in existing_columns:
                    with engine.begin() as connection:
                        connection.execute(
                            text(
                                f"ALTER TABLE {ProjectProtocolRecord.__tablename__} "
                                "ADD COLUMN institutional_field_mapping TEXT NOT NULL DEFAULT ''"
                            )
                        )
        else:
            table.create(bind=engine, checkfirst=True)
        self._schema_checked = True


protocol_repository = ProtocolRepository()
