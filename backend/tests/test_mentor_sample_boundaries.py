import unittest

from app.agents.mentor_models import MentorQuestionnaireRequest
from app.agents.mentor_service import mentor_service


class MentorSampleBoundaryTests(unittest.TestCase):
    def test_historical_project_a_discussion_does_not_override_current_qa_resources(self) -> None:
        payload = MentorQuestionnaireRequest(
            equipment_summary="TOMO / TrueBeam",
            planning_systems="Eclipse / Accuray",
            programming_level="basic",
            data_types=["DICOM RTDose", "RTStruct", "RTPlan", "QA summary"],
            weekly_hours=4,
            interest_topics=["ai_planning_qa"],
            discussion_summary=[
                "Project A - MR 引导自适应放疗剂量学评估",
                "MR-linac 装机量增长，在线自适应和累积剂量是历史样例讨论。",
            ],
        )

        report = mentor_service.generate_recommendations(payload)

        self.assertGreaterEqual(len(report.recommendations), 1)
        self.assertEqual(
            report.recommendations[0].title,
            "基于计划参数与 QA 结果的患者特异性质控风险分层研究",
        )
        self.assertNotIn("在线自适应", report.recommendations[0].title)
        self.assertIn("Project A/B 预设样例不参与出题", " ".join(report.selection_rationale))
        self.assertNotIn("对话摘要生成", report.recommendations[0].why_fit)
        self.assertIn("历史对话只作追踪记录", " ".join(report.recommendations[0].protocol_trace))


if __name__ == "__main__":
    unittest.main()