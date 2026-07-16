import unittest

from chatbot.clinical_analysis import (
    build_clinical_analysis_prompt,
    detect_red_flags,
    merge_red_flags,
    parse_analysis_response,
)


class ClinicalAnalysisTests(unittest.TestCase):
    def test_detects_emergency_signs_deterministically(self):
        flags = detect_red_flags("The cat is straining to urinate with no urine and is vomiting.")
        self.assertEqual(flags[0]["flag"], "urinary obstruction")

    def test_prompt_requires_citations_and_missing_information(self):
        prompt = build_clinical_analysis_prompt("Dog with acute vomiting", "[S1] GI reference", [])
        self.assertIn('"source_refs":["S1"]', prompt)
        self.assertIn("missing_information", prompt)
        self.assertIn("ONLY valid JSON", prompt)

    def test_parses_fenced_json_and_adds_defaults(self):
        result = parse_analysis_response('```json\n{"differentials": []}\n```')
        self.assertEqual(len(result["differentials"]), 5)
        self.assertEqual(result["differentials"][0]["likelihood"], "unknown")
        self.assertIn("disclaimer", result)

    def test_deterministic_flags_are_retained_over_model_output(self):
        result = merge_red_flags(
            [{"flag": "seizure", "evidence": "model"}],
            [{"flag": "urinary obstruction", "evidence": "cannot urinate"}],
        )
        self.assertEqual({item["flag"] for item in result}, {"seizure", "urinary obstruction"})


if __name__ == "__main__":
    unittest.main()
