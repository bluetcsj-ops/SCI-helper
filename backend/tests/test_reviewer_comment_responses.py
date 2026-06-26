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
