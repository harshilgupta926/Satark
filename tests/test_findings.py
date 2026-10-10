import unittest

from findings import build_findings, finding_severity


class FindingSeverityTests(unittest.TestCase):
    def test_empty_and_unrecognized_values_remain_unknown(self):
        for value in ("", None, "Needs review", "Safe", "not clear", "Not confirmed", "Not present"):
            with self.subTest(value=value):
                self.assertEqual(finding_severity(value), "unknown")

    def test_explicit_negative_states_take_precedence(self):
        for value in (
            "Not detected", "No signs of malware",
            "No indicators", "None detected", "Clear", "status: clear",
            "False", "Absent",
        ):
            with self.subTest(value=value):
                self.assertEqual(finding_severity(value), "clear")

    def test_explicit_severity_is_preserved(self):
        cases = {
            "Critical risk": "critical",
            "Severe indicator": "critical",
            "High risk": "high",
            "Medium": "medium",
            "Moderate concern": "medium",
            "Low risk": "low",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(finding_severity(value), expected)

    def test_negated_severity_does_not_become_a_positive_or_clear_finding(self):
        cases = {
            "Not high risk": "unknown",
            "No high risk detected": "unknown",
            "No evidence of high risk": "unknown",
            "No signs of high risk": "unknown",
            "No indicators of critical risk": "unknown",
            "High risk not detected": "unknown",
            "Low risk not present": "unknown",
            "This is not a high-risk event": "unknown",
            "Never considered critical": "unknown",
            "Not high, medium concern": "medium",
            "Not high; low risk": "low",
            "No critical threat; no high risk detected": "unknown",
            "Critical risk ruled out; low risk remains": "low",
            "No evidence of severe risk, but medium concern remains": "medium",
            "No indicators of critical risk, high risk detected": "high",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(finding_severity(value), expected)

    def test_negation_is_scoped_to_its_clause(self):
        cases = {
            "No indicators of critical risk; high risk detected": "high",
            "No evidence of fraud. High risk detected": "high",
            "Not high, low risk": "low",
            "No signs of malware, medium concern remains": "medium",
            "No indicators of critical risk": "unknown",
            "No signs of malware": "clear",
            "Not detected; high risk detected": "high",
            "Clear; low risk": "low",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(finding_severity(value), expected)

    def test_generic_detection_is_high_only_without_explicit_severity(self):
        self.assertEqual(finding_severity("Detected"), "high")
        self.assertEqual(finding_severity("Low risk — detected"), "low")
        self.assertEqual(finding_severity("Medium concern, indicator present"), "medium")
        self.assertEqual(finding_severity("Not detected"), "clear")

    def test_build_findings_handles_malformed_payload_and_orders_severity(self):
        self.assertEqual(build_findings(None), [])
        self.assertEqual(build_findings({"threat_analysis": []}), [])
        findings = build_findings({
            "threat_analysis": {
                "low check": "Low risk — detected",
                "high check": "High risk",
                "unknown check": "Needs review",
                "clear check": "Not detected",
                17: "Medium concern",
            }
        })
        self.assertEqual(
            [item["severity"] for item in findings],
            ["high", "medium", "low", "unknown", "clear"],
        )
        self.assertTrue(all("action" in item and "id" in item for item in findings))
        clear_finding = next(item for item in findings if item["severity"] == "clear")
        self.assertIn("does not prove", clear_finding["action"])


if __name__ == "__main__":
    unittest.main()
