from __future__ import annotations

import json
import re
import time
from datetime import UTC, datetime
from threading import Lock
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, quote_plus, urlencode
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
            search_query='("artificial intelligence" OR "machine learning" OR "deep learning") AND ("treatment planning" OR "quality assurance" OR "patient-specific quality assurance" OR "plan quality") AND radiotherapy',
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


PUBMED_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "mr_linac": [
        "mr-guided",
        "mr guided",
        "mr-linac",
        "adaptive radiotherapy",
        "online adaptive",
        "magnetic resonance",
    ],
    "flash": [
        "flash",
        "ultra-high dose rate",
        "ultrahigh dose rate",
        "dose rate",
    ],
    "ai_planning_qa": [
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "treatment planning",
        "quality assurance",
        "patient-specific qa",
        "plan quality",
    ],
    "particle": [
        "proton",
        "carbon ion",
        "particle therapy",
        "robustness",
        "dosimetry",
    ],
    "radiomics": [
        "radiomics",
        "radiogenomics",
        "outcome",
        "prediction",
        "artificial intelligence",
    ],
    "automation": [
        "automated treatment planning",
        "automatic planning",
        "knowledge-based planning",
        "workflow",
        "plan quality",
    ],
    "sbrt": [
        "srs",
        "sbrt",
        "stereotactic",
        "dose gradient",
        "organ at risk",
        "plan quality",
    ],
    "motion": [
        "motion",
        "gating",
        "tracking",
        "4dct",
        "motion management",
        "sbrt",
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
    def __init__(self, crossref_provider: CrossrefEvidenceProvider | None = None) -> None:
        self._request_lock = Lock()
        self._last_request_at = 0.0
        self._crossref_provider = crossref_provider

    def get_topic_evidence(self, topic_id: str) -> list[MentorEvidenceItem]:
        query = self._query_for_topic(topic_id)
        retrieved_at = datetime.now(UTC).isoformat()
        try:
            pmids = self._search_pmids(query)
            if not pmids:
                return [self._pending_item(query, retrieved_at, "PubMed 未返回匹配 PMID。")]
            summaries = self._fetch_summaries(pmids)
            filtered_summaries = self._filter_summaries(summaries, topic_id)
            if not filtered_summaries:
                return [self._pending_item(query, retrieved_at, "PubMed 返回结果，但没有通过基础质量筛选的候选文献。")]
            return [self._summary_to_evidence(query, retrieved_at, summary) for summary in filtered_summaries]
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
            return [self._pending_item(query, retrieved_at, self._request_failure_message(exc))]

    def _search_pmids(self, query: str) -> list[str]:
        search_params = self._pubmed_search_params(query)
        payload = self._request_json(
            "esearch.fcgi",
            {
                **search_params,
                "db": "pubmed",
                "retmode": "json",
                "retmax": str(
                    max(
                        settings.mentor_pubmed_candidate_retmax,
                        settings.mentor_pubmed_retmax,
                        1,
                    )
                ),
                "sort": "relevance",
            },
        )
        esearch_result = payload.get("esearchresult", {})
        if not isinstance(esearch_result, dict):
            return []
        id_list = esearch_result.get("idlist", [])
        if not isinstance(id_list, list):
            return []
        pmids: list[str] = []
        for item in id_list:
            if item is None:
                continue
            pmid = str(item).strip()
            if pmid.isdigit():
                pmids.append(pmid)
        return pmids

    def _pubmed_search_params(self, query: str) -> dict[str, str]:
        cleaned_query = self._clean_text(query)
        date_match = re.search(
            r"(?:\s+AND)?\s+((?:19|20)\d{2})\s*:\s*((?:19|20)\d{2})\s*$",
            cleaned_query,
        )
        if not date_match:
            return {"term": cleaned_query}
        start_year, end_year = date_match.groups()
        term = self._clean_text(cleaned_query[: date_match.start()])
        if not term:
            term = cleaned_query
        return {
            "term": term,
            "mindate": start_year,
            "maxdate": end_year,
            "datetype": "pdat",
        }

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
        if not isinstance(result, dict):
            return []
        uids = result.get("uids", [])
        if not isinstance(uids, list):
            return []
        summaries: list[dict[str, object]] = []
        for uid in uids:
            summary = result.get(str(uid))
            if isinstance(summary, dict):
                summaries.append(summary)
        return summaries

    def _filter_summaries(
        self,
        summaries: list[dict[str, object]],
        topic_id: str,
    ) -> list[dict[str, object]]:
        filtered: list[dict[str, object]] = []
        for summary in summaries:
            uid = str(summary.get("uid") or "").strip()
            title = str(summary.get("title") or "").strip()
            if not uid or not title:
                continue
            filtered.append(summary)
        return sorted(filtered, key=lambda summary: self._summary_sort_key(summary, topic_id), reverse=True)[
            : max(settings.mentor_pubmed_retmax, 1)
        ]

    def _summary_sort_key(self, summary: dict[str, object], topic_id: str) -> tuple[int, int, int]:
        year = self._publication_year(str(summary.get("pubdate") or ""))
        publication_year = int(year) if year and year.isdigit() else 0
        is_recent = 1 if publication_year >= datetime.now(UTC).year - 7 else 0
        return (is_recent, self._topic_relevance_score(summary, topic_id), publication_year)

    def _topic_relevance_score(self, summary: dict[str, object], topic_id: str) -> int:
        keywords = PUBMED_TOPIC_KEYWORDS.get(topic_id, [])
        if not keywords:
            return 0
        title = self._clean_text(str(summary.get("title") or ""))
        journal = self._clean_text(str(summary.get("fulljournalname") or summary.get("source") or ""))
        publication_types = " ".join(self._publication_types(summary))
        searchable_text = f"{title} {journal} {publication_types}".lower()
        return sum(1 for keyword in keywords if keyword.lower() in searchable_text)

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
        self._wait_for_request_slot()
        with urlopen(url, timeout=settings.mentor_evidence_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("PubMed 返回内容不是 JSON object。")
        return payload

    def _wait_for_request_slot(self) -> None:
        request_interval = self._request_interval_seconds()
        if request_interval <= 0:
            return
        with self._request_lock:
            elapsed = time.monotonic() - self._last_request_at
            wait_seconds = request_interval - elapsed
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            self._last_request_at = time.monotonic()

    def _request_interval_seconds(self) -> float:
        if settings.mentor_pubmed_request_interval_seconds >= 0:
            return settings.mentor_pubmed_request_interval_seconds
        return 0.11 if settings.pubmed_api_key else 0.34

    def _request_failure_message(
        self,
        exc: HTTPError | URLError | TimeoutError | OSError | json.JSONDecodeError | ValueError,
    ) -> str:
        if isinstance(exc, HTTPError):
            reason = exc.reason or exc.msg or "未返回原因"
            return f"PubMed HTTP {exc.code}：{reason}"
        if isinstance(exc, URLError):
            return f"PubMed 网络不可达：{exc.reason}"
        if isinstance(exc, TimeoutError):
            return "PubMed 请求超时。"
        if isinstance(exc, json.JSONDecodeError):
            return f"PubMed 返回内容无法解析为 JSON：{exc.msg}"
        if isinstance(exc, OSError):
            return f"PubMed 系统网络错误：{exc}"
        return f"PubMed 返回内容不符合预期：{exc}"

    def _summary_to_evidence(
        self,
        query: str,
        retrieved_at: str,
        summary: dict[str, object],
    ) -> MentorEvidenceItem:
        pmid = str(summary.get("uid") or "").strip()
        title = self._clean_text(str(summary.get("title") or "")) or "题名未返回"
        journal = self._clean_text(str(summary.get("fulljournalname") or summary.get("source") or "")) or "期刊未返回"
        publication_year = self._publication_year(str(summary.get("pubdate") or ""))
        doi = self._extract_doi(summary)
        publication_types = self._publication_types(summary)
        evidence = MentorEvidenceItem(
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
        if self._crossref_provider:
            return self._crossref_provider.enrich_evidence(evidence)
        return evidence

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
        match = re.search(r"\b(19|20)\d{2}\b", pubdate)
        if match:
            return match.group(0)
        return None

    def _extract_doi(self, summary: dict[str, object]) -> str | None:
        article_ids = summary.get("articleids")
        if not isinstance(article_ids, list):
            return None
        for article_id in article_ids:
            if not isinstance(article_id, dict):
                continue
            if article_id.get("idtype") == "doi" and article_id.get("value"):
                doi = str(article_id["value"]).strip()
                if doi.lower().startswith("doi:"):
                    doi = doi[4:].strip()
                return doi.rstrip(" .")
        return None

    def _publication_types(self, summary: dict[str, object]) -> list[str]:
        pub_types = summary.get("pubtype")
        if not isinstance(pub_types, list):
            return []
        return [self._clean_text(str(item)) for item in pub_types if self._clean_text(str(item))]

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _query_for_topic(self, topic_id: str) -> str:
        local_items = LOCAL_EVIDENCE_LIBRARY.get(topic_id)
        if local_items:
            return local_items[0].search_query
        return "radiotherapy physics AND plan quality AND clinical workflow"

    def _pubmed_search_url(self, query: str) -> str:
        return f"https://pubmed.ncbi.nlm.nih.gov/?term={quote_plus(query)}"


class CrossrefEvidenceProvider:
    def enrich_evidence(self, evidence: MentorEvidenceItem) -> MentorEvidenceItem:
        query = evidence.doi or evidence.title or evidence.search_query
        if not query:
            return evidence
        retrieved_at = evidence.retrieved_at or datetime.now(UTC).isoformat()
        try:
            works = self._search_works(query)
            matched_work, match_warning = self._best_match(works, evidence)
            if not matched_work:
                return evidence.model_copy(
                    update={
                        "limitation": (
                            f"{evidence.limitation} {match_warning or 'Crossref 未返回可用于补充引用格式的匹配记录，'}"
                            "需人工核对 DOI 和期刊官网。"
                        )
                    }
                )
            return self._merge_crossref_work(evidence, matched_work, retrieved_at)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
            return evidence.model_copy(
                update={
                    "limitation": (
                        f"{evidence.limitation} Crossref 补充检索失败："
                        f"{self._request_failure_message(exc)}"
                    )
                }
            )

    def _search_works(self, query: str) -> list[dict[str, object]]:
        params = {
            "rows": str(max(settings.mentor_crossref_retmax, 1)),
            "select": (
                "DOI,title,container-title,published-print,published-online,issued,type,URL,"
                "author,volume,issue,page,article-number"
            ),
        }
        if self._looks_like_doi(query):
            endpoint = f"works/{quote(query.strip(), safe='')}"
            payload = self._request_json(endpoint, {})
            message = payload.get("message", {})
            return [message] if isinstance(message, dict) else []
        params["query.bibliographic"] = query
        payload = self._request_json("works", params)
        message = payload.get("message", {})
        if not isinstance(message, dict):
            return []
        items = message.get("items", [])
        if not isinstance(items, list):
            return []
        return [item for item in items if isinstance(item, dict)]

    def _request_json(self, endpoint: str, params: dict[str, str]) -> dict[str, object]:
        query_params = dict(params)
        if settings.crossref_mailto:
            query_params["mailto"] = settings.crossref_mailto
        query_string = f"?{urlencode(query_params)}" if query_params else ""
        url = f"{settings.crossref_base_url.rstrip('/')}/{endpoint}{query_string}"
        with urlopen(url, timeout=settings.mentor_evidence_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Crossref 返回内容不是 JSON object。")
        return payload

    def _best_match(
        self,
        works: list[dict[str, object]],
        evidence: MentorEvidenceItem,
    ) -> tuple[dict[str, object] | None, str | None]:
        if not works:
            return None, None
        evidence_doi = (evidence.doi or "").strip().lower()
        if evidence_doi:
            for work in works:
                work_doi = str(work.get("DOI") or "").strip().lower()
                if work_doi == evidence_doi:
                    return work, None
            return (
                None,
                "Crossref 返回结果未精确匹配当前 DOI，未自动写入候选引用草稿。",
            )
        evidence_title = self._normalize_title(evidence.title or "")
        if not evidence_title:
            return (
                None,
                "当前候选文献缺少题名或 DOI，Crossref 结果未自动写入候选引用草稿。",
            )
        best_work = max(works, key=lambda work: self._title_overlap_score(evidence_title, work))
        best_score = self._title_overlap_score(evidence_title, best_work)
        if best_score < settings.mentor_crossref_title_match_min_score:
            return (
                None,
                (
                    "Crossref 返回结果与当前题名相似度不足，"
                    f"命中词数 {best_score}/{settings.mentor_crossref_title_match_min_score}，"
                    "未自动写入候选引用草稿。"
                ),
            )
        return best_work, None

    def _merge_crossref_work(
        self,
        evidence: MentorEvidenceItem,
        work: dict[str, object],
        retrieved_at: str,
    ) -> MentorEvidenceItem:
        doi = evidence.doi or self._clean_text(str(work.get("DOI") or "")) or None
        title = evidence.title or self._first_text(work.get("title"))
        journal = evidence.journal or self._first_text(work.get("container-title"))
        publication_year = evidence.publication_year or self._issued_year(work)
        crossref_url = self._clean_text(str(work.get("URL") or "")) or (
            f"https://doi.org/{doi}" if doi else None
        )
        authors = self._authors(work)
        volume = self._clean_text(str(work.get("volume") or "")) or None
        issue = self._clean_text(str(work.get("issue") or "")) or None
        page = self._clean_text(str(work.get("page") or work.get("article-number") or "")) or None
        publication_types = evidence.publication_types or [self._clean_text(str(work.get("type") or ""))]
        publication_types = [item for item in publication_types if item]
        return evidence.model_copy(
            update={
                "evidence_status": "pubmed_crossref" if evidence.evidence_status == "pubmed" else "crossref",
                "retrieved_at": retrieved_at,
                "crossref_url": crossref_url,
                "doi": doi,
                "title": title,
                "journal": journal,
                "publication_year": publication_year,
                "publication_types": publication_types,
                "authors": authors,
                "volume": volume,
                "issue": issue,
                "page": page,
                "citation_text": self._citation_text(title, journal, publication_year, doi),
                "vancouver_citation": self._vancouver_citation(
                    authors,
                    title,
                    journal,
                    publication_year,
                    volume,
                    issue,
                    page,
                    doi,
                ),
                "recommendation_signal": (
                    f"{evidence.recommendation_signal} Crossref 已补充 DOI/期刊元数据候选。"
                ),
                "limitation": (
                    f"{evidence.limitation} Crossref 元数据仅用于生成候选引用草稿，"
                    "正式投稿前仍需人工核对全文、期刊页面和引用格式。"
                ),
            }
        )

    def _issued_year(self, work: dict[str, object]) -> str | None:
        for key in ("published-print", "published-online", "issued"):
            date_parts = work.get(key)
            if not isinstance(date_parts, dict):
                continue
            parts = date_parts.get("date-parts")
            if not isinstance(parts, list) or not parts:
                continue
            first_date = parts[0]
            if not isinstance(first_date, list) or not first_date:
                continue
            year = str(first_date[0]).strip()
            if re.fullmatch(r"(19|20)\d{2}", year):
                return year
        return None

    def _title_overlap_score(self, evidence_title: str, work: dict[str, object]) -> int:
        candidate_title = self._normalize_title(self._first_text(work.get("title")) or "")
        if not candidate_title:
            return 0
        evidence_words = set(evidence_title.split())
        candidate_words = set(candidate_title.split())
        return len(evidence_words & candidate_words)

    def _authors(self, work: dict[str, object]) -> list[str]:
        authors = work.get("author")
        if not isinstance(authors, list):
            return []
        formatted_authors: list[str] = []
        for author in authors:
            if not isinstance(author, dict):
                continue
            formatted_author = self._format_author(author)
            if formatted_author:
                formatted_authors.append(formatted_author)
        return formatted_authors

    def _format_author(self, author: dict[str, object]) -> str | None:
        family = self._clean_text(str(author.get("family") or ""))
        given = self._clean_text(str(author.get("given") or ""))
        name = self._clean_text(str(author.get("name") or ""))
        if family:
            initials = self._initials(given)
            return f"{family} {initials}".strip()
        return name or None

    def _initials(self, given: str) -> str:
        initials: list[str] = []
        for part in re.split(r"[\s.-]+", given):
            cleaned_part = re.sub(r"[^A-Za-z]", "", part)
            if cleaned_part:
                initials.append(cleaned_part[0].upper())
        return "".join(initials)

    def _citation_text(
        self,
        title: str | None,
        journal: str | None,
        publication_year: str | None,
        doi: str | None,
    ) -> str | None:
        if not title:
            return None
        parts = [title.rstrip(".")]
        journal_part = ". ".join(item for item in [journal, publication_year] if item)
        if journal_part:
            parts.append(journal_part)
        if doi:
            parts.append(f"doi:{doi}")
        return ". ".join(parts) + "."

    def _vancouver_citation(
        self,
        authors: list[str],
        title: str | None,
        journal: str | None,
        publication_year: str | None,
        volume: str | None,
        issue: str | None,
        page: str | None,
        doi: str | None,
    ) -> str | None:
        if not title:
            return None
        citation_parts: list[str] = []
        author_text = self._vancouver_author_text(authors)
        if author_text:
            citation_parts.append(author_text)
        citation_parts.append(title.rstrip("."))
        journal_text = self._vancouver_journal_text(journal, publication_year, volume, issue, page)
        if journal_text:
            citation_parts.append(journal_text)
        if doi:
            citation_parts.append(f"doi:{doi}")
        return ". ".join(citation_parts) + "."

    def _vancouver_author_text(self, authors: list[str]) -> str | None:
        if not authors:
            return None
        if len(authors) > 6:
            return f"{', '.join(authors[:6])}, et al"
        return ", ".join(authors)

    def _vancouver_journal_text(
        self,
        journal: str | None,
        publication_year: str | None,
        volume: str | None,
        issue: str | None,
        page: str | None,
    ) -> str | None:
        journal_parts = [item for item in [journal, publication_year] if item]
        if not journal_parts:
            return None
        journal_text = ". ".join(journal_parts)
        volume_issue = ""
        if volume:
            volume_issue = volume
            if issue:
                volume_issue += f"({issue})"
        elif issue:
            volume_issue = f"({issue})"
        if volume_issue and page:
            journal_text += f";{volume_issue}:{page}"
        elif volume_issue:
            journal_text += f";{volume_issue}"
        elif page:
            journal_text += f":{page}"
        return journal_text

    def _request_failure_message(
        self,
        exc: HTTPError | URLError | TimeoutError | OSError | json.JSONDecodeError | ValueError,
    ) -> str:
        if isinstance(exc, HTTPError):
            reason = exc.reason or exc.msg or "未返回原因"
            return f"HTTP {exc.code}：{reason}"
        if isinstance(exc, URLError):
            return f"网络不可达：{exc.reason}"
        if isinstance(exc, TimeoutError):
            return "请求超时。"
        if isinstance(exc, json.JSONDecodeError):
            return f"返回内容无法解析为 JSON：{exc.msg}"
        if isinstance(exc, OSError):
            return f"系统网络错误：{exc}"
        return f"返回内容不符合预期：{exc}"

    def _first_text(self, value: object) -> str | None:
        if isinstance(value, list) and value:
            return self._clean_text(str(value[0])) or None
        if isinstance(value, str):
            return self._clean_text(value) or None
        return None

    def _looks_like_doi(self, value: str) -> bool:
        return bool(re.match(r"^10\.\S+/.+", value.strip(), flags=re.IGNORECASE))

    def _normalize_title(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()


class MentorEvidenceService:
    def __init__(self) -> None:
        self._local_provider = LocalMentorEvidenceProvider()
        self._crossref_provider = CrossrefEvidenceProvider()
        self._pubmed_provider = PubMedEvidenceProvider(self._crossref_provider)

    def get_topic_evidence(self, topic_id: str) -> list[MentorEvidenceItem]:
        if settings.mentor_evidence_provider == "crossref":
            local_items = self._local_provider.get_topic_evidence(topic_id)
            return [self._crossref_provider.enrich_evidence(item) for item in local_items]
        if settings.mentor_evidence_provider == "pubmed":
            return self._pubmed_provider.get_topic_evidence(topic_id)
        return self._local_provider.get_topic_evidence(topic_id)


mentor_evidence_service = MentorEvidenceService()
