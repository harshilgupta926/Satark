import unittest

from firstlight_engine import (
    append_audit,
    apply_simulated_response,
    create_demo_case,
    investigate_case,
    seal_evidence,
    verify_audit_chain,
    verify_evidence,
)


class FirstlightEngineTests(unittest.TestCase):
    def setUp(self):
        self.case = create_demo_case()
        self.evidence = [seal_evidence(event) for event in self.case["events"]]

    def test_evidence_verifies_and_tampering_is_detected(self):
        item = self.evidence[0]
        self.assertTrue(verify_evidence(item)["valid"])
        item["record"]["summary"] += " tampered"
        self.assertFalse(verify_evidence(item)["valid"])

    def test_evidence_id_cannot_be_swapped_outside_the_hashed_record(self):
        item = dict(self.evidence[0])
        item["evidence_id"] = "EV-SUBSTITUTED"
        result = verify_evidence(item)
        self.assertFalse(result["valid"])
        self.assertIn("MISMATCH", result["status"])

    def test_malformed_evidence_record_fails_closed(self):
        item = {"evidence_id": "EV-001", "record": "not-an-object", "sha256": "abc"}
        result = verify_evidence(item)
        self.assertFalse(result["valid"])
        self.assertFalse(verify_evidence(None)["valid"])

    def test_investigate_case_rejects_malformed_case_and_evidence_container(self):
        for malformed_case in (None, [], {}, {"case_id": ""}, {"case_id": None}):
            with self.subTest(case=malformed_case):
                with self.assertRaises(ValueError):
                    investigate_case(malformed_case, self.evidence)
        for malformed_evidence in (None, {}, "not-a-list"):
            with self.subTest(evidence=malformed_evidence):
                with self.assertRaises(ValueError):
                    investigate_case(self.case, malformed_evidence)

    def test_investigate_case_ignores_malformed_items_inside_evidence_list(self):
        result = investigate_case(self.case, [None, "bad-record", *self.evidence])
        self.assertEqual(result["case_id"], self.case["case_id"])
        self.assertTrue(result["timeline"])

    def test_findings_reference_evidence(self):
        result = investigate_case(self.case, self.evidence)
        self.assertGreaterEqual(len(result["findings"]), 3)
        known = {item["evidence_id"] for item in self.evidence}
        for finding in result["findings"]:
            self.assertTrue(set(finding["evidence_ids"]).issubset(known))
            self.assertIn("explanation", finding)

    def test_timeline_sorts_by_instant_across_timezones(self):
        events = [dict(event) for event in self.case["events"]]
        events[0]["timestamp"] = "2026-10-10T09:00:00+02:00"
        events[1]["timestamp"] = "2026-10-10T08:00:00Z"
        evidence = [seal_evidence(event) for event in events]
        timeline = investigate_case(self.case, evidence)["timeline"]
        self.assertEqual(timeline[0]["event_id"], "EV-001")
        self.assertEqual(timeline[1]["event_id"], "EV-002")

    def test_audit_chain_detects_modification(self):
        chain = append_audit([], "created", "tester", {"case": "demo"})
        chain = append_audit(chain, "collected", "tester", {"evidence": "EV-001"})
        self.assertTrue(verify_audit_chain(chain))
        chain[0]["payload"]["case"] = "altered"
        self.assertFalse(verify_audit_chain(chain))

    def test_audit_append_rejects_corrupted_chain_and_invalid_inputs(self):
        chain = append_audit([], "created", "tester", {"case": "demo"})
        corrupted = [dict(chain[0], entry_hash="tampered")]
        for entries, action, actor, payload in (
            (corrupted, "next", "tester", {}),
            (None, "next", "tester", {}),
            ([], "", "tester", {}),
            ([], "next", "", {}),
            ([], "next", "tester", []),
        ):
            with self.subTest(entries=entries, action=action, actor=actor, payload=payload):
                with self.assertRaises(ValueError):
                    append_audit(entries, action, actor, payload)

    def test_response_is_simulated_and_requires_explicit_approval(self):
        result = investigate_case(self.case, self.evidence)
        proposals, rejected = apply_simulated_response(result["response_proposals"], "ACT-001", False, "reviewer")
        self.assertEqual(rejected["status"], "rejected")
        proposals, approved = apply_simulated_response(proposals, "ACT-002", True, "reviewer")
        self.assertEqual(approved["status"], "simulated_success")
        self.assertTrue(approved["simulated"])
        self.assertIn("No real", approved["message"])

    def test_non_boolean_approval_fails_closed(self):
        result = investigate_case(self.case, self.evidence)
        proposals, outcome = apply_simulated_response(
            result["response_proposals"], "ACT-001", "true", "reviewer"
        )
        self.assertEqual(outcome["status"], "rejected")
        self.assertEqual(proposals[0]["status"], "rejected")

    def test_malformed_audit_entries_fail_closed(self):
        self.assertFalse(verify_audit_chain([None]))
        self.assertFalse(verify_audit_chain([{"previous_hash": "GENESIS"}]))
        self.assertFalse(verify_audit_chain(None))
        cyclic = {}
        cyclic["self"] = cyclic
        self.assertFalse(verify_audit_chain([{
            "previous_hash": "GENESIS",
            "payload": cyclic,
            "entry_hash": "not-a-valid-hash",
        }]))

    def test_unknown_action_fails_closed(self):
        with self.assertRaises(ValueError):
            apply_simulated_response([], "ACT-404", True, "reviewer")
        with self.assertRaises(ValueError):
            apply_simulated_response(None, "ACT-001", True, "reviewer")
        with self.assertRaises(ValueError):
            apply_simulated_response([None], "ACT-001", True, "reviewer")

    def test_approver_label_is_bounded(self):
        result = investigate_case(self.case, self.evidence)
        _, outcome = apply_simulated_response(
            result["response_proposals"], "ACT-001", True, "x" * 500
        )
        self.assertEqual(len(outcome["approver"]), 128)


    def test_findings_never_reference_unavailable_or_invalid_evidence(self):
        # Keep only one valid record: findings may retain their explanatory
        # labels, but unsupported references must be removed and uncertainty
        # must be explicit.
        single = [self.evidence[0]]
        result = investigate_case(self.case, single)
        valid_ids = {item["evidence_id"] for item in single}
        for finding in result["findings"]:
            self.assertTrue(set(finding["evidence_ids"]).issubset(valid_ids))
            if not finding["evidence_ids"]:
                self.assertFalse(finding["evidence_available"])
                self.assertEqual(finding["state"], "unverified")
                self.assertEqual(finding["confidence"], "low")

    def test_timeline_places_unparseable_timestamps_last(self):
        events = [dict(event) for event in self.case["events"]]
        events[0]["timestamp"] = "not-a-timestamp"
        evidence = [seal_evidence(event) for event in events]
        result = investigate_case(self.case, evidence)
        self.assertEqual(result["timeline"][-1]["event_id"], events[0]["event_id"])

    def test_response_rejection_is_simulated_and_does_not_mark_success(self):
        result = investigate_case(self.case, self.evidence)
        proposals, outcome = apply_simulated_response(
            result["response_proposals"], "ACT-003", False, "reviewer"
        )
        self.assertTrue(outcome["simulated"])
        self.assertEqual(outcome["status"], "rejected")
        self.assertEqual(
            next(item for item in proposals if item["action_id"] == "ACT-003")["status"],
            "rejected",
        )
        self.assertNotIn("message", outcome)

    def test_response_approval_never_claims_real_world_execution(self):
        result = investigate_case(self.case, self.evidence)
        _, outcome = apply_simulated_response(
            result["response_proposals"], "ACT-001", True, "reviewer"
        )
        self.assertTrue(outcome["simulated"])
        self.assertEqual(outcome["status"], "simulated_success")
        self.assertIn("No real", outcome["message"])

    def test_audit_chain_rejects_reordered_entries(self):
        chain = append_audit([], "created", "tester", {"case": "demo"})
        chain = append_audit(chain, "reviewed", "tester", {"decision": "reject"})
        self.assertTrue(verify_audit_chain(chain))
        self.assertFalse(verify_audit_chain(list(reversed(chain))))

if __name__ == "__main__":
    unittest.main()
