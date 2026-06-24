from __future__ import annotations

from datetime import UTC, datetime

from app.agents.mentor_evidence_service import mentor_evidence_service
from app.agents.mentor_models import (
    MentorQuestionnaireRequest,
    MentorRecommendationCard,
    MentorRecommendationResponse,
    MentorTrendItem,
    MentorTrendPoint,
    MentorTrendSnapshot,
)


TREND_LIBRARY: list[MentorTrendItem] = [
    MentorTrendItem(
        topic_id="mr_linac",
        title="MR 引导自适应放疗",
        heat_label="🔥🔥🔥",
        summary="适合有 Unity、MR-linac 或在线自适应流程的中心，临床问题具体，容易形成病例队列。",
        recent_counts=[
            MentorTrendPoint(year=2019, publication_count=82),
            MentorTrendPoint(year=2020, publication_count=104),
            MentorTrendPoint(year=2021, publication_count=131),
            MentorTrendPoint(year=2022, publication_count=167),
            MentorTrendPoint(year=2023, publication_count=196),
            MentorTrendPoint(year=2024, publication_count=228),
        ],
        forecast_note="未来几年仍会持续升温，重点会转向累积剂量、在线适配效率与真实世界流程评估。",
    ),
    MentorTrendItem(
        topic_id="flash",
        title="FLASH 超高剂量率放疗",
        heat_label="🔥🔥",
        summary="热度高，但更依赖特定设备与实验平台，普通临床中心直接落地门槛偏高。",
        recent_counts=[
            MentorTrendPoint(year=2019, publication_count=33),
            MentorTrendPoint(year=2020, publication_count=47),
            MentorTrendPoint(year=2021, publication_count=72),
            MentorTrendPoint(year=2022, publication_count=98),
            MentorTrendPoint(year=2023, publication_count=123),
            MentorTrendPoint(year=2024, publication_count=149),
        ],
        forecast_note="未来仍会增长，但更偏设备与机制研究，不一定适合缺少专门平台的团队。",
    ),
    MentorTrendItem(
        topic_id="ai_planning_qa",
        title="AI for Planning & QA",
        heat_label="🔥🔥🔥",
        summary="适合有计划系统、QA 数据、log files 或轻量编程能力的团队，题目空间很大。",
        recent_counts=[
            MentorTrendPoint(year=2019, publication_count=125),
            MentorTrendPoint(year=2020, publication_count=164),
            MentorTrendPoint(year=2021, publication_count=214),
            MentorTrendPoint(year=2022, publication_count=268),
            MentorTrendPoint(year=2023, publication_count=319),
            MentorTrendPoint(year=2024, publication_count=372),
        ],
        forecast_note="预计仍是最活跃方向之一，重点会在自动化、质量预测与流程集成。",
    ),
    MentorTrendItem(
        topic_id="particle",
        title="粒子治疗",
        heat_label="🔥🔥",
        summary="适合有质子或重离子中心背景的团队，若缺少设备通常不作为第一优先。",
        recent_counts=[
            MentorTrendPoint(year=2019, publication_count=94),
            MentorTrendPoint(year=2020, publication_count=106),
            MentorTrendPoint(year=2021, publication_count=118),
            MentorTrendPoint(year=2022, publication_count=133),
            MentorTrendPoint(year=2023, publication_count=146),
            MentorTrendPoint(year=2024, publication_count=159),
        ],
        forecast_note="整体保持稳步增长，更多聚焦适应证细化与高精度剂量学问题。",
    ),
    MentorTrendItem(
        topic_id="radiomics",
        title="影像组学与放射基因组学",
        heat_label="🔥🔥",
        summary="适合能获得影像与结局数据、并具备一定编程或建模能力的团队。",
        recent_counts=[
            MentorTrendPoint(year=2019, publication_count=108),
            MentorTrendPoint(year=2020, publication_count=138),
            MentorTrendPoint(year=2021, publication_count=176),
            MentorTrendPoint(year=2022, publication_count=211),
            MentorTrendPoint(year=2023, publication_count=237),
            MentorTrendPoint(year=2024, publication_count=255),
        ],
        forecast_note="未来会继续热门，但方法学重复较多，选题必须更贴近真实临床问题。",
    ),
    MentorTrendItem(
        topic_id="automation",
        title="自动化计划与知识库优化",
        heat_label="🔥🔥",
        summary="适合有 Eclipse、RayStation、Ethos 或批量计划经验的中心，实施路径务实。",
        recent_counts=[
            MentorTrendPoint(year=2019, publication_count=76),
            MentorTrendPoint(year=2020, publication_count=93),
            MentorTrendPoint(year=2021, publication_count=117),
            MentorTrendPoint(year=2022, publication_count=142),
            MentorTrendPoint(year=2023, publication_count=168),
            MentorTrendPoint(year=2024, publication_count=192),
        ],
        forecast_note="会继续增长，尤其是自动化质控、效率评估与可复制工作流文章。",
    ),
    MentorTrendItem(
        topic_id="sbrt",
        title="SRS / SBRT 剂量雕刻",
        heat_label="🔥🔥",
        summary="适合病例量稳定、计划质量要求高的团队，容易形成剂量学对比和流程优化选题。",
        recent_counts=[
            MentorTrendPoint(year=2019, publication_count=87),
            MentorTrendPoint(year=2020, publication_count=101),
            MentorTrendPoint(year=2021, publication_count=118),
            MentorTrendPoint(year=2022, publication_count=136),
            MentorTrendPoint(year=2023, publication_count=149),
            MentorTrendPoint(year=2024, publication_count=163),
        ],
        forecast_note="增长平稳，重点会落在复杂靶区剂量雕刻与 OAR 保护平衡。",
    ),
    MentorTrendItem(
        topic_id="motion",
        title="实时运动管理",
        heat_label="🔥🔥",
        summary="适合有 4DCT、CBCT、门控或 tracking 流程的中心，临床问题明确。",
        recent_counts=[
            MentorTrendPoint(year=2019, publication_count=68),
            MentorTrendPoint(year=2020, publication_count=79),
            MentorTrendPoint(year=2021, publication_count=94),
            MentorTrendPoint(year=2022, publication_count=113),
            MentorTrendPoint(year=2023, publication_count=127),
            MentorTrendPoint(year=2024, publication_count=141),
        ],
        forecast_note="未来仍稳定增长，尤其适合围绕 SBRT、肺部或腹部靶区做真实世界研究。",
    ),
]

TOPIC_JOURNALS: dict[str, list[str]] = {
    "mr_linac": ["Radiotherapy & Oncology", "Physics in Medicine & Biology", "JACMP"],
    "flash": ["Medical Physics", "Frontiers in Oncology", "PMB"],
    "ai_planning_qa": ["Medical Physics", "JACMP", "Frontiers in Oncology"],
    "particle": ["Radiotherapy & Oncology", "Medical Physics", "PMB"],
    "radiomics": ["Frontiers in Oncology", "Radiotherapy & Oncology", "JACMP"],
    "automation": ["JACMP", "Medical Physics", "Frontiers in Oncology"],
    "sbrt": ["JACMP", "Radiotherapy & Oncology", "Medical Physics"],
    "motion": ["Radiotherapy & Oncology", "JACMP", "PMB"],
}


class MentorService:
    def get_trend_snapshot(self) -> MentorTrendSnapshot:
        return MentorTrendSnapshot(
            generated_at=datetime.now(UTC).isoformat(),
            trends=TREND_LIBRARY,
            recommended_focus="优先选择既有设备和数据能直接支撑、并能在 3-6 个月内形成首轮结果的方向。",
        )

    def generate_recommendations(
        self,
        payload: MentorQuestionnaireRequest,
    ) -> MentorRecommendationResponse:
        interests = payload.interest_topics or [trend.topic_id for trend in TREND_LIBRARY[:3]]
        selected_topics = [trend for trend in TREND_LIBRARY if trend.topic_id in interests] or TREND_LIBRARY[:3]
        selected_topics = selected_topics[:3]
        strengths = self._build_strengths(payload)
        recommendations = [self._build_card(topic, payload) for topic in selected_topics]
        return MentorRecommendationResponse(
            profile_summary=self._build_profile_summary(payload, strengths),
            resource_diagnosis=self._build_resource_diagnosis(payload),
            matched_strengths=strengths,
            recommendations=recommendations,
            next_steps=[
                "确认 1 个最有把握拿到数据的方向，并先定义主要终点。",
                "列出该方向可直接导出的病例、计划、QA 或影像数据类型。",
                "把首轮样例数据交给 Dr. Data Lin 做字段和质控预检查。",
            ],
        )

    def _build_strengths(self, payload: MentorQuestionnaireRequest) -> list[str]:
        strengths: list[str] = []
        if payload.weekly_hours >= 6:
            strengths.append("每周可投入科研时间较稳定，适合推进连续型课题。")
        else:
            strengths.append("科研时间偏紧，建议优先选取数据现成、流程清晰的题目。")
        if payload.programming_level in {"intermediate", "advanced"}:
            strengths.append("具备一定编程能力，可以考虑 AI、自动化或影像建模路线。")
        else:
            strengths.append("编程投入应控制在轻量范围，优先选择剂量学或流程评估型课题。")
        if payload.data_types:
            strengths.append(f"当前已明确可用数据：{', '.join(payload.data_types[:4])}。")
        else:
            strengths.append("当前可用数据类型还不够明确，先做数据摸底会更稳。")
        if payload.publication_experience.strip():
            strengths.append("已有发文或投稿经验可作为写作节奏基础，建议从可快速形成 Methods/Results 的题目切入。")
        else:
            strengths.append("发文经验尚未明确，建议优先选择结构清楚、统计边界简单的首篇 SCI 题目。")
        return strengths

    def _build_resource_diagnosis(self, payload: MentorQuestionnaireRequest) -> list[str]:
        diagnosis: list[str] = []
        equipment = payload.equipment_summary.strip()
        systems = payload.planning_systems.strip()
        if equipment:
            diagnosis.append(f"设备资源：已提供“{equipment}”，推荐题目会优先贴合现有治疗平台。")
        else:
            diagnosis.append("设备资源：尚未填写具体设备，推荐题目会先按通用放疗物理流程保守匹配。")
        if systems:
            diagnosis.append(f"计划系统：已提供“{systems}”，可围绕计划导出、剂量学指标和流程效率设计研究。")
        else:
            diagnosis.append("计划系统：尚未填写，后续需要补充 TPS、QA 和影像系统名称以缩小选题。")
        if payload.weekly_hours >= 8:
            diagnosis.append("时间投入：每周时间较充足，可承担数据清洗、统计复核和多轮改稿。")
        elif payload.weekly_hours >= 3:
            diagnosis.append("时间投入：适合 3-6 个月内完成单中心回顾性或流程评估型课题。")
        else:
            diagnosis.append("时间投入：偏紧，应优先选择数据已导出、终点单一、图表数量少的题目。")
        return diagnosis

    def _build_profile_summary(
        self,
        payload: MentorQuestionnaireRequest,
        strengths: list[str],
    ) -> str:
        equipment = payload.equipment_summary.strip() or "设备信息待补充"
        systems = payload.planning_systems.strip() or "计划系统待补充"
        interests = ", ".join(payload.interest_topics) if payload.interest_topics else "尚未勾选兴趣方向"
        return (
            f"当前画像：设备/平台为“{equipment}”，计划系统为“{systems}”，"
            f"编程水平为“{payload.programming_level or '未说明'}”，每周科研时间约 {payload.weekly_hours} 小时，"
            f"兴趣方向为“{interests}”。综合来看，最应优先选择与现成设备、现成数据和稳定时间投入相匹配的题目。"
            f"{strengths[0]}"
        )

    def _build_card(
        self,
        topic: MentorTrendItem,
        payload: MentorQuestionnaireRequest,
    ) -> MentorRecommendationCard:
        data_text = ", ".join(payload.data_types[:3]) if payload.data_types else "现有临床数据"
        programming_note = (
            "可加入轻量自动化或建模部分增强创新度。"
            if payload.programming_level in {"intermediate", "advanced"}
            else "建议把方法学控制在剂量学对比或流程评估范围内。"
        )
        topic_plan = self._topic_plan(topic.topic_id, payload)
        evidence_items = mentor_evidence_service.get_topic_evidence(topic.topic_id)
        minimum_data_fields = self._minimum_data_fields(topic.topic_id)
        return MentorRecommendationCard(
            title=self._build_title(topic.topic_id),
            research_question=topic_plan["research_question"],
            why_fit=(
                f"该方向与“{payload.equipment_summary.strip() or '当前设备条件'}”和"
                f"“{payload.planning_systems.strip() or '当前计划系统'}”更容易对接，同时可以直接利用 {data_text}。"
            ),
            data_pathway=topic_plan["data_pathway"],
            methods_route=topic_plan["methods_route"],
            statistical_plan=topic_plan["statistical_plan"],
            innovation_point=f"{topic.summary} {programming_note}",
            feasibility_note=f"按每周 {payload.weekly_hours} 小时估计，先做单中心回顾性首轮分析通常更可控。",
            risk_flags=self._risk_flags(topic.topic_id, payload),
            minimum_data_fields=minimum_data_fields,
            readiness_checklist=self._readiness_checklist(
                topic_id=topic.topic_id,
                payload=payload,
                minimum_data_fields=minimum_data_fields,
            ),
            protocol_trace=self._protocol_trace_points(
                topic=topic,
                evidence_count=len(evidence_items),
                payload=payload,
            ),
            first_milestones=[
                "第 1 周：锁定病例范围、主要终点和最小字段清单。",
                "第 2-3 周：导出 10-20 例脱敏样例数据并完成字段质控。",
                "第 4-6 周：完成首轮描述统计、图表草案和 Methods/Results 骨架。",
            ],
            evidence_items=evidence_items,
            target_journals=TOPIC_JOURNALS.get(topic.topic_id, ["JACMP", "Medical Physics"]),
        )

    def _minimum_data_fields(self, topic_id: str) -> list[str]:
        shared_fields = [
            "匿名病例或计划 ID",
            "治疗部位",
            "计划系统和版本",
            "处方剂量与分割次数",
            "主要终点字段",
        ]
        topic_fields: dict[str, list[str]] = {
            "mr_linac": [
                "原计划与在线自适应计划标识",
                "分次序号或治疗日期",
                "PTV/CTV 覆盖指标",
                "OAR 剂量指标",
                "在线适配耗时或审核结果",
            ],
            "flash": [
                "超高剂量率设备或实验平台标识",
                "剂量率或束流参数",
                "剂量学验证指标",
                "实验或临床适用边界说明",
            ],
            "ai_planning_qa": [
                "计划 ID",
                "QA 结果标签",
                "gamma pass rate 或质控通过率",
                "计划复杂度或 MU",
                "设备/部位分层变量",
            ],
            "particle": [
                "粒子类型和能量/射程相关参数",
                "鲁棒性设置",
                "靶区和 OAR 剂量指标",
                "不确定性或 range margin 字段",
            ],
            "radiomics": [
                "影像派生特征版本",
                "影像序列或扫描参数",
                "剂量学协变量",
                "结局或毒性标签",
                "特征筛选记录",
            ],
            "automation": [
                "人工计划和自动化计划配对 ID",
                "计划质量评分或剂量学指标",
                "人工计划时间或自动化运行时间",
                "返工或人工调整记录",
            ],
            "sbrt": [
                "靶区体积",
                "PTV D95% / V95%",
                "剂量梯度或适形指数",
                "关键 OAR Dmax/Dmean",
                "计划技术和处方分割",
            ],
            "motion": [
                "4DCT/CBCT 或 tracking 指标",
                "运动管理策略",
                "边界或 ITV/PTV margin",
                "治疗执行时间",
                "剂量偏差或配准质量指标",
            ],
        }
        return shared_fields + topic_fields.get(topic_id, ["计划质量指标", "流程效率指标"])

    def _readiness_checklist(
        self,
        *,
        topic_id: str,
        payload: MentorQuestionnaireRequest,
        minimum_data_fields: list[str],
    ) -> list[str]:
        checklist = [
            f"最小字段：先确认 {', '.join(minimum_data_fields[:5])} 是否可从现有系统导出。",
            "伦理/数据许可：正式使用真实病例前确认 IRB、数据使用授权和脱敏规则。",
            "首轮样例数据：先导出 10-20 例脱敏 CSV，交给 Dr. Data Lin 做字段覆盖、缺失率和隐私检查。",
            "统计复核边界：当前 Mentor 只给选题和方法路线，正式 P 值、CI、模型诊断需由 Data Lin 和人工统计复核确认。",
        ]
        if not payload.data_types:
            checklist.append("当前未填写可用数据类型，测试前应先补充 RTDose、RTStruct、QA、CBCT 或 log files 等来源。")
        if topic_id in {"radiomics", "ai_planning_qa"}:
            checklist.append("建模类题目需预先定义训练/验证边界，避免把探索性模型写成已验证预测工具。")
        if topic_id in {"flash", "particle"}:
            checklist.append("设备依赖较强，测试前应确认本中心是否真的拥有对应平台或可访问合作数据。")
        return checklist

    def _protocol_trace_points(
        self,
        *,
        topic: MentorTrendItem,
        evidence_count: int,
        payload: MentorQuestionnaireRequest,
    ) -> list[str]:
        data_types = ", ".join(payload.data_types[:4]) if payload.data_types else "数据类型待补充"
        return [
            f"来源趋势主题：{topic.title}（{topic.topic_id}）。",
            f"推荐生成时设备/计划系统：{payload.equipment_summary.strip() or '设备待补充'} / {payload.planning_systems.strip() or '计划系统待补充'}。",
            f"推荐生成时数据来源：{data_types}。",
            f"候选证据数量：{evidence_count} 条；写入 Protocol 前建议至少标记 1-2 条为确认可用。",
            "写入 Protocol 后仍需在 Vera Protocol 中人工确认研究问题、主要终点、数据需求和统计路线。",
        ]

    def _topic_plan(self, topic_id: str, payload: MentorQuestionnaireRequest) -> dict[str, str]:
        systems = payload.planning_systems.strip() or "现有计划系统"
        data_text = ", ".join(payload.data_types[:4]) if payload.data_types else "计划、剂量和病例结局数据"
        default_plan = {
            "research_question": "现有放疗流程中的关键物理指标是否可以解释计划质量、效率或临床执行差异？",
            "data_pathway": f"从 {systems} 导出 {data_text}，先建立病例级脱敏 CSV 与剂量学指标表。",
            "methods_route": "采用单中心回顾性队列，定义主要终点、纳入排除标准和可复现的数据处理脚本。",
            "statistical_plan": "先做描述统计和分组比较；正式检验前由 Dr. Data Lin 完成隐私、缺失值和统计假设确认。",
        }
        plans = {
            "mr_linac": {
                "research_question": "在线自适应放疗是否能在特定病种中改善靶区覆盖、OAR 保护或计划通过效率？",
                "data_pathway": f"从 {systems} 汇总原计划、自适应计划、累积剂量、分次数量、治疗部位和 OAR 指标。",
                "methods_route": "按病种建立自适应前后配对队列，比较计划质量、在线调整幅度和流程耗时。",
                "statistical_plan": "优先考虑配对设计；连续剂量学指标可用配对 t 或 Wilcoxon，三次及以上时间点需外部复核重复测量模型。",
            },
            "ai_planning_qa": {
                "research_question": "计划参数、QA 指标或 log files 能否提前识别高风险计划或异常质控结果？",
                "data_pathway": f"整合 {data_text}，形成计划级特征表、QA 结果标签和设备/部位分层变量。",
                "methods_route": "先做规则型风险分层和可解释特征筛选，再评估轻量模型或阈值策略。",
                "statistical_plan": "先报告描述统计、组间差异和效应量；预测类结果需补充交叉验证、校准和外部复核。",
            },
            "radiomics": {
                "research_question": "放疗前影像或剂量分布特征是否与毒性、局控或计划复杂度存在可解释关联？",
                "data_pathway": f"准备脱敏影像派生特征、剂量指标、治疗部位和结局字段，原始影像暂不进入当前原型。",
                "methods_route": "从少量临床问题出发，限制特征数量，优先做可解释特征和临床变量联合分析。",
                "statistical_plan": "需要控制多重比较和过拟合；当前原型只给候选检验，正式建模应在外部统计环境复核。",
            },
            "automation": {
                "research_question": "自动化计划或知识库优化是否能稳定提升计划一致性、减少人工计划时间或降低返工率？",
                "data_pathway": f"从 {systems} 导出人工计划和自动化计划的剂量学指标、计划时间、返工记录和部位信息。",
                "methods_route": "采用前后对照或配对计划对比，定义计划质量评分、效率指标和人工复核标准。",
                "statistical_plan": "配对计划可用配对检验；多个部位或多个计划策略需预先定义分层并控制多重比较。",
            },
            "sbrt": {
                "research_question": "SRS/SBRT 计划中靶区覆盖、剂量梯度和 OAR 保护之间是否存在可优化的剂量学平衡？",
                "data_pathway": f"汇总靶区体积、处方剂量、剂量梯度、适形指数、OAR Dmax/Dmean 和治疗部位。",
                "methods_route": "按部位或计划策略分层，比较关键剂量学指标并寻找异常计划模式。",
                "statistical_plan": "多组剂量指标可先做 ANOVA/Welch ANOVA/Kruskal-Wallis 候选判断，正式结果需人工确认假设。",
            },
            "motion": {
                "research_question": "运动管理策略是否降低靶区边界不确定性、剂量偏差或治疗执行时间？",
                "data_pathway": f"整理 4DCT/CBCT、门控或 tracking 相关指标、计划剂量参数和治疗执行记录。",
                "methods_route": "围绕肺部或腹部 SBRT 建立流程评估队列，比较不同运动管理策略下的剂量学与效率指标。",
                "statistical_plan": "按策略分组做描述统计和组间比较；若同一患者多次测量，应优先标记为重复测量设计。",
            },
        }
        return plans.get(topic_id, default_plan)

    def _risk_flags(self, topic_id: str, payload: MentorQuestionnaireRequest) -> list[str]:
        risks: list[str] = []
        if not payload.data_types:
            risks.append("数据类型未明确，可能导致题目范围过大。")
        if payload.weekly_hours < 3:
            risks.append("每周可投入时间较少，建议压缩为单终点、单图表主线。")
        if topic_id in {"flash", "particle"}:
            risks.append("该方向对专门设备或中心资源依赖较强，需先确认真实可用数据。")
        if topic_id == "radiomics" and payload.programming_level in {"none", "basic"}:
            risks.append("影像组学对编程和建模要求较高，建议先找合作统计或改为剂量学问题。")
        if not payload.publication_experience.strip():
            risks.append("缺少既往发文经验信息，首轮目标期刊应保持务实。")
        return risks or ["主要风险可控，关键是尽快用脱敏样例数据验证字段是否齐全。"]

    def _build_title(self, topic_id: str) -> str:
        titles = {
            "mr_linac": "基于在线自适应流程的累积剂量与计划质量评估",
            "flash": "围绕超高剂量率流程可行性的物理验证研究",
            "ai_planning_qa": "基于计划与 QA 数据的自动化质量预测研究",
            "particle": "粒子治疗计划质量或剂量鲁棒性回顾性分析",
            "radiomics": "结合放疗流程的影像特征与结局探索研究",
            "automation": "自动化计划或知识库优化的真实世界效率评估",
            "sbrt": "SRS / SBRT 剂量雕刻与 OAR 保护平衡研究",
            "motion": "实时运动管理流程对剂量学与实施效率的影响分析",
        }
        return titles.get(topic_id, "放疗物理流程优化研究")


mentor_service = MentorService()
