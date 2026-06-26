import unittest

from app.projects.reviewer_comments import ReviewerCommentRepository


class ReviewerCommentResponseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = ReviewerCommentRepository()

    def assertDraftContains(self, comment_type: str, comment: str, expected: list[str]) -> None:
        draft = self.repository._build_response_draft(comment, comment_type)
        for phrase in expected:
            self.assertIn(phrase, draft)
        self.assertIn("Page: [to be completed manually].", draft)
        self.assertIn("Lines: [to be completed manually].", draft)
        self.assertIn("Manuscript location: [to be completed manually].", draft)

    def test_statistics_boundary_comment_gets_exploratory_response(self) -> None:
        comment = (
            "The Results section should avoid causal wording because the current analysis "
            "is exploratory and the binary endpoint coding is unclear."
        )

        self.assertEqual(self.repository._infer_response_theme(comment), "statistics_model")
        self.assertDraftContains(
            "minor",
            comment,
            [
                "statistical interpretation",
                "event coding",
                "exploratory unless it has been externally validated",
            ],
        )

    def test_reference_comment_gets_literature_response(self) -> None:
        comment = (
            "Please add a recent reference supporting automated radiotherapy plan-quality "
            "workflows in the Introduction."
        )

        self.assertEqual(self.repository._infer_response_theme(comment), "literature_reference")
        self.assertDraftContains(
            "minor",
            comment,
            [
                "strengthen the literature support",
                "recent and traceable references",
                "citation metadata",
            ],
        )

    def test_submission_disclosure_comment_gets_ethics_response(self) -> None:
        comment = "The cover letter should mention data availability and whether generative AI assistance was used."

        self.assertEqual(self.repository._infer_response_theme(comment), "ethics_submission")
        self.assertDraftContains(
            "minor",
            comment,
            [
                "submission and disclosure requirement",
                "data-availability",
                "AI-assistance statements",
            ],
        )

    def test_radiotherapy_method_comment_gets_planning_detail_response(self) -> None:
        comment = (
            "The Methods should report treatment planning system version, dose calculation "
            "algorithm, gamma criteria, and structure naming rules."
        )

        self.assertEqual(self.repository._infer_response_theme(comment), "radiotherapy_methods")
        self.assertDraftContains(
            "major",
            comment,
            [
                "radiotherapy planning details",
                "treatment planning system version",
                "structure-naming rules",
            ],
        )


    def test_explicit_major_comment_takes_precedence_over_clarify_keyword(self) -> None:
        comment = (
            "Reviewer 1\nMajor Comment 2: The Results appear to imply that the exploratory "
            "model predicts clinical outcome. Please clarify endpoint coding."
        )

        self.assertEqual(self.repository._infer_comment_type(comment), "major")

    def test_radiotherapy_method_theme_takes_precedence_over_binary_endpoint(self) -> None:
        comment = (
            "Major Comment 1: The Methods do not define QA failure. Please specify gamma "
            "pass rate criteria, TPS version, dose calculation algorithm, and whether "
            "gamma pass rate was treated as a binary endpoint."
        )

        self.assertEqual(self.repository._infer_response_theme(comment), "radiotherapy_methods")

    def test_figure_table_theme_takes_precedence_over_source_dataset(self) -> None:
        comment = (
            "Figure 2 and Table 1 need clearer captions and should state the source "
            "dataset and the number of complete cases."
        )

        self.assertEqual(self.repository._infer_response_theme(comment), "figures_tables")


    def test_ethics_submission_takes_precedence_over_raw_dicom_details(self) -> None:
        comment = (
            "The data availability statement is incomplete. Please clarify de-identification, "
            "IRB approval, whether raw DICOM RTDose/RTStruct/RTPlan files were retained, "
            "and how missing fields were handled."
        )

        self.assertEqual(self.repository._infer_response_theme(comment), "ethics_submission")


    def test_response_draft_includes_specific_reviewer_concern(self) -> None:
        comment = (
            "Major Comment 2: The manuscript should define QA failure and explain "
            "whether gamma pass rate was treated as a binary endpoint."
        )

        draft = self.repository._build_response_draft(comment, "major")

        self.assertIn(
            "We understand the concern to be that the manuscript should define QA failure",
            draft,
        )
        self.assertIn("gamma pass rate", draft)
        self.assertIn("binary endpoint", draft)

    def test_statistics_manuscript_change_is_theme_specific(self) -> None:
        comment = "The Results section should avoid causal wording because the model is exploratory."

        change = self.repository._build_manuscript_change(comment, "minor")

        self.assertIn("统计模型目的", change)
        self.assertIn("外部统计复核边界", change)
        self.assertIn("避免因果化", change)

    def test_split_warning_is_preserved_with_theme_specific_change(self) -> None:
        comment = "Please add page and line references for each revised manuscript location."

        change = self.repository._build_manuscript_change(
            comment,
            "minor",
            ["该条意见过短，可能只是标题片段。"],
        )

        self.assertIn("投稿声明", change)
        self.assertIn("拆分提醒", change)
        self.assertIn("该条意见过短", change)

if __name__ == "__main__":
    unittest.main()
