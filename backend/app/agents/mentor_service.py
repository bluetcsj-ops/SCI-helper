from __future__ import annotations

from datetime import UTC, datetime

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
        return strengths

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
        return MentorRecommendationCard(
            title=self._build_title(topic.topic_id),
            why_fit=(
                f"该方向与“{payload.equipment_summary.strip() or '当前设备条件'}”和"
                f"“{payload.planning_systems.strip() or '当前计划系统'}”更容易对接，同时可以直接利用 {data_text}。"
            ),
            innovation_point=f"{topic.summary} {programming_note}",
            feasibility_note=f"按每周 {payload.weekly_hours} 小时估计，先做单中心回顾性首轮分析通常更可控。",
            target_journals=TOPIC_JOURNALS.get(topic.topic_id, ["JACMP", "Medical Physics"]),
        )

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
