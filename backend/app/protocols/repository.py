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
                inclusion_criteria="拟纳入与研究问题匹配、关键计划/剂量/结构或流程字段可获得、并可在真实数据阶段完成脱敏和来源追踪的数据记录。",
                exclusion_criteria="后续真实数据接入时，排除关键字段缺失、计划或影像质量不可复核、治疗流程中断、数据来源不一致、以及存在直接身份标识或脱敏不充分风险的记录。",
                data_requirements=(
                    "候选数据字段包括匿名病例或计划 ID、治疗部位、技术、RTDose/RTStruct/RTPlan "
                    "或结构化计划指标、PTV/OAR 剂量指标、QA 结果、复杂度或流程时间；"
                    "实际字段取决于 Mentor 讨论后的研究方向和可用导出。"
                ),
                institutional_field_mapping=(
                    "正式研究前人工确认：该草案来自当前研究方向讨论，不代表已有真实机构 protocol。"
                    "真实数据接入或投稿前，再由研究者确认伦理审批/豁免、数据使用许可、脱敏规则、"
                    "字段字典、CSV 导出路径、TPS/DICOM/QA 追踪和统计复核责任人。"
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
