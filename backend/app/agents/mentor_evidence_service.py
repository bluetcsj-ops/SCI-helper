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


def _curated_reference(
    *,
    search_query: str,
    evidence_summary: str,
    recommendation_signal: str,
    limitation: str,
    pmid: str,
    title: str,
    journal: str,
    publication_year: str,
    doi: str,
    authors: list[str],
    volume: str | None,
    issue: str | None,
    page: str | None,
    publication_types: list[str],
    citation_text: str,
    vancouver_citation: str,
) -> MentorEvidenceItem:
    return MentorEvidenceItem(
        source_type="curated_radiotherapy_reference",
        evidence_status="curated_reference",
        external_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        crossref_url=f"https://doi.org/{doi}",
        pmid=pmid,
        title=title,
        journal=journal,
        publication_year=publication_year,
        doi=doi,
        citation_text=citation_text,
        vancouver_citation=vancouver_citation,
        authors=authors,
        volume=volume,
        issue=issue,
        page=page,
        publication_types=publication_types,
        review_status="unreviewed",
        search_query=search_query,
        evidence_summary=evidence_summary,
        recommendation_signal=recommendation_signal,
        limitation=limitation,
    )


LOCAL_EVIDENCE_LIBRARY: dict[str, list[MentorEvidenceItem]] = {
    "mr_linac": [
        _curated_reference(
            search_query='"Practical guidelines of online MR-guided adaptive radiotherapy"',
            evidence_summary="在线 MR 引导自适应放疗实践指南，覆盖 MRgART 工作流、团队协作、在线适配和临床实施边界。",
            recommendation_signal="适合支撑 MR-Linac / MR-guided adaptive radiotherapy 选题中的流程可行性、在线适配步骤和人工核验要求。",
            limitation="指南类候选文献可支持方法学背景，但具体病种、剂量累积和终点仍需补充本课题相关原始研究。",
            pmid="35946325",
            title="Practical guidelines of online MR-guided adaptive radiotherapy",
            journal="Journal of Radiation Research",
            publication_year="2022",
            doi="10.1093/jrr/rrac048",
            authors=["Okamoto H", "Igaki H", "Chiba T", "Shibuya K", "Sakasai T", "Jingu K"],
            volume="63",
            issue="5",
            page="730-740",
            publication_types=["Journal Article"],
            citation_text=(
                "Okamoto H, Igaki H, Chiba T, Shibuya K, Sakasai T, Jingu K, et al. "
                "Practical guidelines of online MR-guided adaptive radiotherapy. "
                "Journal of Radiation Research. 2022;63(5):730-740. doi:10.1093/jrr/rrac048."
            ),
            vancouver_citation=(
                "Okamoto H, Igaki H, Chiba T, Shibuya K, Sakasai T, Jingu K, et al. "
                "Practical guidelines of online MR-guided adaptive radiotherapy. "
                "J Radiat Res. 2022;63(5):730-740. doi:10.1093/jrr/rrac048."
            ),
        ),
        _curated_reference(
            search_query='"Technical Challenges of Real-Time Adaptive MR-Guided Radiotherapy"',
            evidence_summary="综述实时自适应 MR 引导放疗的技术挑战，包括影像、运动、在线优化、剂量计算和实时决策边界。",
            recommendation_signal="适合提醒研究方案提前定义 MR workflow、实时适配、QA 和剂量计算复核点。",
            limitation="技术综述不能替代本中心平台验证；正式论文仍需说明设备版本、TPS、在线计划策略和 QA 流程。",
            pmid="33763369",
            title="Technical Challenges of Real-Time Adaptive MR-Guided Radiotherapy",
            journal="Frontiers in Oncology",
            publication_year="2021",
            doi="10.3389/fonc.2021.634507",
            authors=["Thorwarth D", "Low DA"],
            volume="11",
            issue=None,
            page="634507",
            publication_types=["Journal Article", "Review"],
            citation_text=(
                "Thorwarth D, Low DA. Technical Challenges of Real-Time Adaptive MR-Guided Radiotherapy. "
                "Frontiers in Oncology. 2021;11:634507. doi:10.3389/fonc.2021.634507."
            ),
            vancouver_citation=(
                "Thorwarth D, Low DA. Technical Challenges of Real-Time Adaptive MR-Guided Radiotherapy. "
                "Front Oncol. 2021;11:634507. doi:10.3389/fonc.2021.634507."
            ),
        ),
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
        _curated_reference(
            search_query='"Ultrahigh dose-rate FLASH irradiation increases the differential response between normal and tumor tissue in mice"',
            evidence_summary="FLASH 超高剂量率放疗的经典转化研究，提示正常组织保护与肿瘤控制差异反应的基础证据线索。",
            recommendation_signal="适合作为 FLASH 方向的背景引用，同时提醒该方向更偏设备、剂量率验证和转化研究。",
            limitation="该研究为动物/转化研究线索，不能直接支持普通临床中心的人体疗效结论；临床选题需另补设备和剂量率实测证据。",
            pmid="25031268",
            title="Ultrahigh dose-rate FLASH irradiation increases the differential response between normal and tumor tissue in mice",
            journal="Science Translational Medicine",
            publication_year="2014",
            doi="10.1126/scitranslmed.3008973",
            authors=["Favaudon V", "Caplier L", "Monceau V", "Pouzoulet F", "Sayarath M", "Fouillade C"],
            volume="6",
            issue="245",
            page="245ra93",
            publication_types=["Journal Article"],
            citation_text=(
                "Favaudon V, Caplier L, Monceau V, Pouzoulet F, Sayarath M, Fouillade C, et al. "
                "Ultrahigh dose-rate FLASH irradiation increases the differential response between normal and tumor tissue in mice. "
                "Science Translational Medicine. 2014;6(245):245ra93. doi:10.1126/scitranslmed.3008973."
            ),
            vancouver_citation=(
                "Favaudon V, Caplier L, Monceau V, Pouzoulet F, Sayarath M, Fouillade C, et al. "
                "Ultrahigh dose-rate FLASH irradiation increases the differential response between normal and tumor tissue in mice. "
                "Sci Transl Med. 2014;6(245):245ra93. doi:10.1126/scitranslmed.3008973."
            ),
        ),
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("FLASH radiotherapy" OR "ultra-high dose rate") AND radiotherapy AND 2019:2024',
            evidence_summary="FLASH 方向热度高，主题多集中于剂量率、实验验证、正常组织保护和设备实现。",
            recommendation_signal="适合有专门设备、实验平台或物理验证条件的团队。",
            limitation="普通临床中心若缺少 FLASH 平台，直接形成可投稿数据的难度较高。",
        ),
    ],
    "ai_planning_qa": [
        _curated_reference(
            search_query='"Tolerance limits and methodologies for IMRT measurement-based verification QA" "AAPM Task Group No. 218"',
            evidence_summary="AAPM TG-218 给出 IMRT measurement-based verification QA 的容差、方法学和报告建议，是患者特异性 QA 研究的重要规范依据。",
            recommendation_signal="适合支撑 QA 通过率、gamma criteria、测量型验证和计划复杂度研究中的方法学边界。",
            limitation="TG-218 是 QA 方法学建议，不等同于某个 AI 预测模型的验证证据；预测类研究仍需校准、交叉验证和外部复核。",
            pmid="29443390",
            title="Tolerance limits and methodologies for IMRT measurement-based verification QA: Recommendations of AAPM Task Group No. 218",
            journal="Medical Physics",
            publication_year="2018",
            doi="10.1002/mp.12810",
            authors=["Miften M", "Olch A", "Mihailidis D", "Moran J", "Pawlicki T", "Molineu A"],
            volume="45",
            issue="4",
            page="e53-e83",
            publication_types=["Journal Article", "Review"],
            citation_text=(
                "Miften M, Olch A, Mihailidis D, Moran J, Pawlicki T, Molineu A, et al. "
                "Tolerance limits and methodologies for IMRT measurement-based verification QA: Recommendations of AAPM Task Group No. 218. "
                "Medical Physics. 2018;45(4):e53-e83. doi:10.1002/mp.12810."
            ),
            vancouver_citation=(
                "Miften M, Olch A, Mihailidis D, Moran J, Pawlicki T, Molineu A, et al. "
                "Tolerance limits and methodologies for IMRT measurement-based verification QA: Recommendations of AAPM Task Group No. 218. "
                "Med Phys. 2018;45(4):e53-e83. doi:10.1002/mp.12810."
            ),
        ),
        _curated_reference(
            search_query='"Quantified VMAT plan complexity in relation to measurement-based quality assurance results"',
            evidence_summary="该研究将 VMAT 计划复杂度指标与测量型 QA 结果关联，适合作为计划复杂度和 QA 数据建模的具体文献线索。",
            recommendation_signal="适合把 plan complexity、MU、MLC aperture、gamma pass rate 等字段纳入数据字典和统计路线。",
            limitation="计划复杂度与 QA 的关系受设备、部位、能量和测量流程影响，正式研究需预设分层或敏感性分析。",
            pmid="33112467",
            title="Quantified VMAT plan complexity in relation to measurement-based quality assurance results",
            journal="Journal of Applied Clinical Medical Physics",
            publication_year="2020",
            doi="10.1002/acm2.13048",
            authors=["Nguyen M", "Chan GH"],
            volume="21",
            issue="11",
            page="132-140",
            publication_types=["Journal Article"],
            citation_text=(
                "Nguyen M, Chan GH. Quantified VMAT plan complexity in relation to measurement-based quality assurance results. "
                "Journal of Applied Clinical Medical Physics. 2020;21(11):132-140. doi:10.1002/acm2.13048."
            ),
            vancouver_citation=(
                "Nguyen M, Chan GH. Quantified VMAT plan complexity in relation to measurement-based quality assurance results. "
                "J Appl Clin Med Phys. 2020;21(11):132-140. doi:10.1002/acm2.13048."
            ),
        ),
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
        _curated_reference(
            search_query='"Range uncertainties in proton therapy and the role of Monte Carlo simulations"',
            evidence_summary="质子治疗射程不确定性和 Monte Carlo 剂量计算角色的综述，是粒子治疗鲁棒性和剂量不确定性选题的重要基础。",
            recommendation_signal="适合支撑粒子治疗计划质量、鲁棒性、CT 值转换和射程不确定性相关研究问题。",
            limitation="综述提供物理背景，不代表本中心质子/重离子数据已具备；需先确认设备、计划系统和剂量复核条件。",
            pmid="22571913",
            title="Range uncertainties in proton therapy and the role of Monte Carlo simulations",
            journal="Physics in Medicine and Biology",
            publication_year="2012",
            doi="10.1088/0031-9155/57/11/R99",
            authors=["Paganetti H"],
            volume="57",
            issue="11",
            page="R99-117",
            publication_types=["Journal Article", "Review"],
            citation_text=(
                "Paganetti H. Range uncertainties in proton therapy and the role of Monte Carlo simulations. "
                "Physics in Medicine and Biology. 2012;57(11):R99-117. doi:10.1088/0031-9155/57/11/R99."
            ),
            vancouver_citation=(
                "Paganetti H. Range uncertainties in proton therapy and the role of Monte Carlo simulations. "
                "Phys Med Biol. 2012;57(11):R99-117. doi:10.1088/0031-9155/57/11/R99."
            ),
        ),
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("proton therapy" OR "carbon ion therapy") AND ("robustness" OR dosimetry) AND radiotherapy',
            evidence_summary="粒子治疗研究常围绕鲁棒性、适应证、LET/RBE、剂量不确定性和计划质量展开。",
            recommendation_signal="适合有质子或重离子中心资源、病例队列和计划复核能力的团队。",
            limitation="如果缺少粒子治疗平台，建议不作为首篇本地可落地课题。",
        ),
    ],
    "radiomics": [
        _curated_reference(
            search_query='"Radiomics: extracting more information from medical images using advanced feature analysis"',
            evidence_summary="Radiomics 经典方法学论文，说明从医学影像中提取定量特征并用于临床研究的基本思路。",
            recommendation_signal="适合支撑影像组学选题的背景，但必须与放疗剂量、结局字段和过拟合控制一起设计。",
            limitation="该文献是方法学基础，不直接证明某个放疗结局模型有效；正式研究需补充特征稳定性、多重比较和外部验证。",
            pmid="22257792",
            title="Radiomics: extracting more information from medical images using advanced feature analysis",
            journal="European Journal of Cancer",
            publication_year="2012",
            doi="10.1016/j.ejca.2011.11.036",
            authors=["Lambin P", "Rios-Velazquez E", "Leijenaar R", "Carvalho S", "van Stiphout RG", "Granton P"],
            volume="48",
            issue="4",
            page="441-446",
            publication_types=["Journal Article", "Review"],
            citation_text=(
                "Lambin P, Rios-Velazquez E, Leijenaar R, Carvalho S, van Stiphout RG, Granton P, et al. "
                "Radiomics: extracting more information from medical images using advanced feature analysis. "
                "European Journal of Cancer. 2012;48(4):441-446. doi:10.1016/j.ejca.2011.11.036."
            ),
            vancouver_citation=(
                "Lambin P, Rios-Velazquez E, Leijenaar R, Carvalho S, van Stiphout RG, Granton P, et al. "
                "Radiomics: extracting more information from medical images using advanced feature analysis. "
                "Eur J Cancer. 2012;48(4):441-446. doi:10.1016/j.ejca.2011.11.036."
            ),
        ),
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("radiomics" OR "radiogenomics") AND radiotherapy AND outcome',
            evidence_summary="影像组学方向文献多，但重复性、特征稳定性、外部验证和多重比较是常见审稿关注点。",
            recommendation_signal="适合有影像、剂量和结局数据，并能控制建模流程的团队。",
            limitation="不建议在缺少统计/建模复核时直接做高维预测模型。",
        ),
    ],
    "automation": [
        _curated_reference(
            search_query='"Automated 4π radiotherapy treatment planning with evolving knowledge-base"',
            evidence_summary="自动化 4π 放疗计划研究，使用 evolving knowledge-base 支持计划优化，是自动化计划/知识库优化的具体实现线索。",
            recommendation_signal="适合支撑自动化计划质量、一致性、优化效率和可复制 workflow 的研究问题。",
            limitation="4π 自动计划不一定适用于所有 TPS 或临床流程；本中心研究需明确人工计划、自动计划和人工复核责任边界。",
            pmid="31233619",
            title="Automated 4π radiotherapy treatment planning with evolving knowledge-base",
            journal="Medical Physics",
            publication_year="2019",
            doi="10.1002/mp.13682",
            authors=["Landers A", "O'Connor D", "Ruan D", "Sheng K"],
            volume="46",
            issue="9",
            page="3833-3843",
            publication_types=["Journal Article"],
            citation_text=(
                "Landers A, O'Connor D, Ruan D, Sheng K. Automated 4π radiotherapy treatment planning with evolving knowledge-base. "
                "Medical Physics. 2019;46(9):3833-3843. doi:10.1002/mp.13682."
            ),
            vancouver_citation=(
                "Landers A, O'Connor D, Ruan D, Sheng K. Automated 4π radiotherapy treatment planning with evolving knowledge-base. "
                "Med Phys. 2019;46(9):3833-3843. doi:10.1002/mp.13682."
            ),
        ),
        _curated_reference(
            search_query='"Automated evaluation for rapid implementation of knowledge-based radiotherapy planning models"',
            evidence_summary="该研究关注知识库放疗计划模型的自动化评估与快速实施，适合连接模型上线、计划质量和人工验收流程。",
            recommendation_signal="适合把模型评估、计划质量指标、实施效率和人工验收清单纳入 Mentor 研究路线。",
            limitation="知识库计划模型的表现依赖训练计划质量、部位、TPS 和本地约束；正式研究需保留外部或独立复核。",
            pmid="37703545",
            title="Automated evaluation for rapid implementation of knowledge-based radiotherapy planning models",
            journal="Journal of Applied Clinical Medical Physics",
            publication_year="2023",
            doi="10.1002/acm2.14152",
            authors=["Harms J", "Pogue JA", "Cardenas CE", "Stanley DN", "Cardan R", "Popple R"],
            volume="24",
            issue="10",
            page="e14152",
            publication_types=["Journal Article"],
            citation_text=(
                "Harms J, Pogue JA, Cardenas CE, Stanley DN, Cardan R, Popple R. "
                "Automated evaluation for rapid implementation of knowledge-based radiotherapy planning models. "
                "Journal of Applied Clinical Medical Physics. 2023;24(10):e14152. doi:10.1002/acm2.14152."
            ),
            vancouver_citation=(
                "Harms J, Pogue JA, Cardenas CE, Stanley DN, Cardan R, Popple R. "
                "Automated evaluation for rapid implementation of knowledge-based radiotherapy planning models. "
                "J Appl Clin Med Phys. 2023;24(10):e14152. doi:10.1002/acm2.14152."
            ),
        ),
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("automated treatment planning" OR "knowledge-based planning") AND radiotherapy AND workflow',
            evidence_summary="自动化计划与知识库优化常见终点包括计划质量、一致性、人工计划时间和流程可复制性。",
            recommendation_signal="适合已有 Eclipse、RayStation、Ethos 或批量计划经验的中心，容易落地为真实世界效率评估。",
            limitation="需要区分人工计划、自动化计划和人工复核之间的责任边界。",
        ),
    ],
    "sbrt": [
        _curated_reference(
            search_query='"Stereotactic body radiation therapy: the report of AAPM Task Group 101"',
            evidence_summary="AAPM TG-101 是 SBRT 物理、剂量、运动管理和实施质量的重要报告，可支撑 SRS/SBRT 计划质量研究的规范背景。",
            recommendation_signal="适合提醒方案定义 dose gradient、OAR 约束、处方分割、运动管理和计划 QA 边界。",
            limitation="TG 报告可作为技术规范背景，具体病种和计划策略仍需补充近年原始研究与本中心数据。",
            pmid="20879569",
            title="Stereotactic body radiation therapy: the report of AAPM Task Group 101",
            journal="Medical Physics",
            publication_year="2010",
            doi="10.1118/1.3438081",
            authors=["Benedict SH", "Yenice KM", "Followill D", "Galvin JM", "Hinson W", "Kavanagh B"],
            volume="37",
            issue="8",
            page="4078-4101",
            publication_types=["Journal Article"],
            citation_text=(
                "Benedict SH, Yenice KM, Followill D, Galvin JM, Hinson W, Kavanagh B, et al. "
                "Stereotactic body radiation therapy: the report of AAPM Task Group 101. "
                "Medical Physics. 2010;37(8):4078-4101. doi:10.1118/1.3438081."
            ),
            vancouver_citation=(
                "Benedict SH, Yenice KM, Followill D, Galvin JM, Hinson W, Kavanagh B, et al. "
                "Stereotactic body radiation therapy: the report of AAPM Task Group 101. "
                "Med Phys. 2010;37(8):4078-4101. doi:10.1118/1.3438081."
            ),
        ),
        MentorEvidenceItem(
            source_type="local_search_template",
            search_query='("SRS" OR "SBRT") AND ("dose gradient" OR "organ at risk" OR "plan quality")',
            evidence_summary="SRS/SBRT 计划质量研究常围绕靶区覆盖、剂量梯度、适形指数和 OAR 保护平衡展开。",
            recommendation_signal="适合病例量稳定、计划质量要求高、可导出剂量学指标的团队。",
            limitation="不同部位和处方分割差异明显，需要预先限定研究对象。",
        ),
    ],
    "motion": [
        _curated_reference(
            search_query='"The management of respiratory motion in radiation oncology report of AAPM Task Group 76"',
            evidence_summary="AAPM TG-76 总结呼吸运动管理在放疗中的模拟、成像、计划和治疗实施要求，是运动管理选题的重要规范背景。",
            recommendation_signal="适合支撑 4DCT、门控、tracking、边界设置、SBRT 运动管理和流程效率相关研究路线。",
            limitation="TG-76 是基础规范文献，当前设备、影像频率、门控阈值和计划流程仍需按本中心实际复核。",
            pmid="17089851",
            title="The management of respiratory motion in radiation oncology report of AAPM Task Group 76",
            journal="Medical Physics",
            publication_year="2006",
            doi="10.1118/1.2349696",
            authors=["Keall PJ", "Mageras GS", "Balter JM", "Emery RS", "Forster KM", "Jiang SB"],
            volume="33",
            issue="10",
            page="3874-3900",
            publication_types=["Journal Article"],
            citation_text=(
                "Keall PJ, Mageras GS, Balter JM, Emery RS, Forster KM, Jiang SB, et al. "
                "The management of respiratory motion in radiation oncology report of AAPM Task Group 76. "
                "Medical Physics. 2006;33(10):3874-3900. doi:10.1118/1.2349696."
            ),
            vancouver_citation=(
                "Keall PJ, Mageras GS, Balter JM, Emery RS, Forster KM, Jiang SB, et al. "
                "The management of respiratory motion in radiation oncology report of AAPM Task Group 76. "
                "Med Phys. 2006;33(10):3874-3900. doi:10.1118/1.2349696."
            ),
        ),
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
                    "evidence_status": item.evidence_status or "local_template",
                    "retrieved_at": retrieved_at,
                    "external_url": item.external_url,
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
