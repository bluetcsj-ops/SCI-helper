from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from app.agents.mentor_models import MentorEvidenceItem
from app.core.config import settings


LOCAL_EVIDENCE_LIBRARY: dict[str, list[MentorEvidenceItem]] = {
    "mr_linac": [
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("MR-guided radiotherapy" OR "MR-Linac") AND ("adaptive radiotherapy" OR "online adaptive") AND 2019:2024',
            evidence_summary="近年主题集中在在线自适应流程、累积剂量评估、治疗效率和特定病种真实世界队列。",
            recommendation_signal="如果中心具备 MR-Linac 或在线自适应流程，容易形成明确临床问题和配对剂量学终点。",
            limitation="当前为本地证据模板，尚未自动拉取 PubMed 结果和真实发文计量。",
        ),
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("adaptive radiotherapy" AND "accumulated dose" AND radiotherapy)',
            evidence_summary="累积剂量和分次间解剖变化是该方向常见切入点，适合与剂量学指标和流程耗时联合分析。",
            recommendation_signal="推荐优先选择病例量稳定、结构和剂量可追溯的部位。",
            limitation="不同平台的剂量累积方法差异较大，正式论文需说明配准和剂量合成方法。",
        ),
    ],
    "flash": [
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("FLASH radiotherapy" OR "ultra-high dose rate") AND radiotherapy AND 2019:2024',
            evidence_summary="FLASH 方向热度高，主题多集中于剂量率、实验验证、正常组织保护和设备实现。",
            recommendation_signal="适合有专门设备、实验平台或物理验证条件的团队。",
            limitation="普通临床中心若缺少 FLASH 平台，直接形成可投稿数据的难度较高。",
        ),
    ],
    "ai_planning_qa": [
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("artificial intelligence" OR "machine learning") AND ("treatment planning" OR "patient-specific QA") AND radiotherapy',
            evidence_summary="AI 计划与 QA 方向持续活跃，常见主题包括自动计划质量预测、QA 通过率预测、计划复杂度和可解释特征。",
            recommendation_signal="如果已有计划、QA、log files 或批量导出能力，可快速形成结构化数据表。",
            limitation="预测模型类研究需要交叉验证、校准和过拟合控制，不能只报告训练集效果。",
        ),
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("plan complexity" AND "patient-specific QA" AND radiotherapy)',
            evidence_summary="计划复杂度指标与 QA 结果的关系适合做轻量、可解释、单中心回顾性研究。",
            recommendation_signal="适合编程能力一般但能稳定获取计划和 QA 指标的团队。",
            limitation="不同设备、能量和部位会引入异质性，需要预先设定分层或敏感性分析。",
        ),
    ],
    "particle": [
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("proton therapy" OR "carbon ion therapy") AND ("robustness" OR dosimetry) AND radiotherapy',
            evidence_summary="粒子治疗研究常围绕鲁棒性、适应证、LET/RBE、剂量不确定性和计划质量展开。",
            recommendation_signal="适合有质子或重离子中心资源、病例队列和计划复核能力的团队。",
            limitation="如果缺少粒子治疗平台，建议不作为首篇本地可落地课题。",
        ),
    ],
    "radiomics": [
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("radiomics" OR "radiogenomics") AND radiotherapy AND outcome',
            evidence_summary="影像组学方向文献多，但重复性、特征稳定性、外部验证和多重比较是常见审稿关注点。",
            recommendation_signal="适合有影像、剂量和结局数据，并能控制建模流程的团队。",
            limitation="不建议在缺少统计/建模复核时直接做高维预测模型。",
        ),
    ],
    "automation": [
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("automated treatment planning" OR "knowledge-based planning") AND radiotherapy AND workflow',
            evidence_summary="自动化计划与知识库优化常见终点包括计划质量、一致性、人工计划时间和流程可复制性。",
            recommendation_signal="适合已有 Eclipse、RayStation、Ethos 或批量计划经验的中心，容易落地为真实世界效率评估。",
            limitation="需要区分人工计划、自动化计划和人工复核之间的责任边界。",
        ),
    ],
    "sbrt": [
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("SRS" OR "SBRT") AND ("dose gradient" OR "organ at risk" OR "plan quality")',
            evidence_summary="SRS/SBRT 计划质量研究常围绕靶区覆盖、剂量梯度、适形指数和 OAR 保护平衡展开。",
            recommendation_signal="适合病例量稳定、计划质量要求高、可导出剂量学指标的团队。",
            limitation="不同部位和处方分割差异明显，需要预先限定研究对象。",
        ),
    ],
    "motion": [
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("motion management" OR gating OR tracking OR "4DCT") AND radiotherapy AND SBRT',
            evidence_summary="运动管理方向常见主题包括 4DCT、CBCT、门控、tracking、边界设置和实施效率。",
            recommendation_signal="适合围绕肺部或腹部 SBRT 做流程评估和剂量学影响分析。",
            limitation="同一患者多次测量和呼吸运动不确定性会提高统计设计复杂度。",
        ),
    ],
}


class MentorEvidenceProvider(Protocol):
    def get_topic_evidence(self, topic_id: str) -> list[MentorEvidenceItem]:
        ...


class LocalMentorEvidenceProvider:
    def get_topic_evidence(self, topic_id: str) -> list[MentorEvidenceItem]:
        evidence_items = LOCAL_EVIDENCE_LIBRARY.get(topic_id, self._fallback_evidence())
        retrieved_at = datetime.now(UTC).isoformat()
        return [
            item.model_copy(
                update={
                    "evidence_status": "local_template",
                    "retrieved_at": retrieved_at,
                    "external_url": None,
                }
            )
            for item in evidence_items
        ]

    def _fallback_evidence(self) -> list[MentorEvidenceItem]:
        return [
            MentorEvidenceItem(
                source_type="local_search_template",
                search_query="radiotherapy physics AND plan quality AND clinical workflow",
                evidence_summary="该方向属于放疗物理流程优化范畴，通常需要围绕明确终点、可复现数据和可解释方法组织证据。",
                recommendation_signal="适合先从本中心可稳定导出的数据和单一主要终点切入。",
                limitation="当前证据为本地模板，正式选题前仍需人工完成真实文献检索。",
            )
        ]


class PubMedEvidenceProvider:
    def get_topic_evidence(self, topic_id: str) -> list[MentorEvidenceItem]:
        query = self._query_for_topic(topic_id)
        retrieved_at = datetime.now(UTC).isoformat()
        try:
            pmids = self._search_pmids(query)
            if not pmids:
                return [self._pending_item(query, retrieved_at, "PubMed 未返回匹配 PMID。")]
            summaries = self._fetch_summaries(pmids)
            filtered_summaries = self._filter_summaries(summaries)
            if not filtered_summaries:
                return [self._pending_item(query, retrieved_at, "PubMed 返回结果，但没有通过基础质量筛选的候选文献。")]
            return [self._summary_to_evidence(query, retrieved_at, summary) for summary in filtered_summaries]
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            return [self._pending_item(query, retrieved_at, f"PubMed 请求未完成：{exc}")]

    def _search_pmids(self, query: str) -> list[str]:
        payload = self._request_json(
            "esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": str(max(settings.mentor_pubmed_retmax, 1)),
                "sort": "relevance",
            },
        )
        id_list = payload.get("esearchresult", {}).get("idlist", [])
        return [str(item) for item in id_list if item]

    def _fetch_summaries(self, pmids: list[str]) -> list[dict[str, object]]:
        payload = self._request_json(
            "esummary.fcgi",
            {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json",
            },
        )
        result = payload.get("result", {})
        uids = result.get("uids", [])
        return [result[uid] for uid in uids if uid in result]

    def _filter_summaries(self, summaries: list[dict[str, object]]) -> list[dict[str, object]]:
        filtered: list[dict[str, object]] = []
        for summary in summaries:
            uid = str(summary.get("uid") or "").strip()
            title = str(summary.get("title") or "").strip()
            if not uid or not title:
                continue
            filtered.append(summary)
        return sorted(filtered, key=self._summary_sort_key, reverse=True)[
            : max(settings.mentor_pubmed_retmax, 1)
        ]

    def _summary_sort_key(self, summary: dict[str, object]) -> tuple[int, int]:
        year = self._publication_year(str(summary.get("pubdate") or ""))
        publication_year = int(year) if year and year.isdigit() else 0
        is_recent = 1 if publication_year >= datetime.now(UTC).year - 7 else 0
        return (is_recent, publication_year)

    def _request_json(self, endpoint: str, params: dict[str, str]) -> dict[str, object]:
        query_params = {
            **params,
            "tool": "sci-helper",
        }
        if settings.pubmed_email:
            query_params["email"] = settings.pubmed_email
        if settings.pubmed_api_key:
            query_params["api_key"] = settings.pubmed_api_key
        url = f"{settings.pubmed_base_url.rstrip('/')}/{endpoint}?{urlencode(query_params)}"
        with urlopen(url, timeout=settings.mentor_evidence_timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def _summary_to_evidence(
        self,
        query: str,
        retrieved_at: str,
        summary: dict[str, object],
    ) -> MentorEvidenceItem:
        pmid = str(summary.get("uid") or "")
        title = str(summary.get("title") or "题名未返回")
        journal = str(summary.get("fulljournalname") or summary.get("source") or "期刊未返回")
        publication_year = self._publication_year(str(summary.get("pubdate") or ""))
        doi = self._extract_doi(summary)
        publication_types = self._publication_types(summary)
        return MentorEvidenceItem(
            source_type="pubmed",
            evidence_status="pubmed",
            retrieved_at=retrieved_at,
            external_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else self._pubmed_search_url(query),
            pmid=pmid or None,
            title=title,
            journal=journal,
            publication_year=publication_year,
            doi=doi,
            publication_types=publication_types,
            review_status="unreviewed",
            search_query=query,
            evidence_summary=f"{title}。来源：{journal}{f'，{publication_year}' if publication_year else ''}。",
            recommendation_signal=(
                "该 PubMed 结果可作为方向相关文献线索；"
                f"文献类型：{', '.join(publication_types) if publication_types else '未返回'}。"
            ),
            limitation="自动检索只返回候选文献，不代表系统已完成系统综述、质量评价或引用真实性复核。",
        )

    def _pending_item(
        self,
        query: str,
        retrieved_at: str,
        limitation: str,
    ) -> MentorEvidenceItem:
        return [
            MentorEvidenceItem(
                source_type="pubmed",
                evidence_status="external_pending",
                retrieved_at=retrieved_at,
                external_url=self._pubmed_search_url(query),
                search_query=query,
                evidence_summary="PubMed 检索请求未返回可用结构化文献，当前保留检索式和搜索链接供人工复核。",
                recommendation_signal="获得 PMID、题名、年份和期刊后，可作为推荐依据候选文献继续筛选。",
                review_status="unreviewed",
                limitation=limitation,
            )
        ][0]

    def _publication_year(self, pubdate: str) -> str | None:
        for token in pubdate.split():
            if token.isdigit() and len(token) == 4:
                return token
        return None

    def _extract_doi(self, summary: dict[str, object]) -> str | None:
        article_ids = summary.get("articleids")
        if not isinstance(article_ids, list):
            return None
        for article_id in article_ids:
            if not isinstance(article_id, dict):
                continue
            if article_id.get("idtype") == "doi" and article_id.get("value"):
                return str(article_id["value"])
        return None

    def _publication_types(self, summary: dict[str, object]) -> list[str]:
        pub_types = summary.get("pubtype")
        if not isinstance(pub_types, list):
            return []
        return [str(item) for item in pub_types if item]

    def _query_for_topic(self, topic_id: str) -> str:
        local_items = LOCAL_EVIDENCE_LIBRARY.get(topic_id)
        if local_items:
            return local_items[0].search_query
        return "radiotherapy physics AND plan quality AND clinical workflow"

    def _pubmed_search_url(self, query: str) -> str:
        return f"https://pubmed.ncbi.nlm.nih.gov/?term={query.replace(' ', '+')}"


class MentorEvidenceService:
    def __init__(self) -> None:
        self._local_provider = LocalMentorEvidenceProvider()
        self._pubmed_provider = PubMedEvidenceProvider()

    def get_topic_evidence(self, topic_id: str) -> list[MentorEvidenceItem]:
        if settings.mentor_evidence_provider == "pubmed":
            return self._pubmed_provider.get_topic_evidence(topic_id)
        return self._local_provider.get_topic_evidence(topic_id)


mentor_evidence_service = MentorEvidenceService()
