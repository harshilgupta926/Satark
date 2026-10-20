"""Tests for the real-telemetry acceptance validator; no network or fake live endpoint."""
from __future__ import annotations

import copy

import pytest

from scripts.accept_firstlight_wazuh_live import canonical_sha256, validate_response


def response_with_one_alert():
    record = {
        "event_id": "wazuh-" + "a" * 32,
        "timestamp": "2026-10-20T08:00:00.000Z",
        "source": "wazuh",
        "kind": "security_alert",
        "summary": "Actual alert summary from the source fixture",
        "details": {
            "index": "wazuh-alerts-4.x-2026.10.20",
            "document_id": "document-123",
            "source_record_sha256": "b" * 64,
        },
    }
    return {
        "source": "wazuh-indexer",
        "mode": "live_read_only_investigation",
        "persisted": False,
        "case_id": "WAZUH-0123456789abcdefabcd",
        "fetched_count": 1,
        "integrity_summary": {"total": 1, "sealed": 1, "source_verified": 0, "mismatched": 0},
        "evidence": [{
            "evidence_id": record["event_id"],
            "record": record,
            "sha256": canonical_sha256(record),
        }],
        "investigation": {"case_id": "WAZUH-0123456789abcdefabcd", "findings": []},
    }


def test_acceptance_validator_checks_normalized_digest_and_provenance():
    report = validate_response(response_with_one_alert())
    assert report["result"] == "PASS"
    assert report["alerts_verified"] == 1
    assert report["upstream_source_signatures_verified"] == 0
    assert report["response_actions_executed"] is False


def test_acceptance_validator_fails_closed_on_empty_live_results():
    payload = response_with_one_alert()
    payload["evidence"] = []
    payload["fetched_count"] = 0
    payload["integrity_summary"] = {"total": 0, "sealed": 0, "source_verified": 0, "mismatched": 0}
    with pytest.raises(ValueError, match="No real Wazuh alerts"):
        validate_response(payload)


def test_acceptance_validator_rejects_tampered_snapshot():
    payload = response_with_one_alert()
    payload["evidence"][0]["record"]["summary"] = "altered after sealing"
    with pytest.raises(ValueError, match="digest verification failed"):
        validate_response(payload)


def test_acceptance_validator_rejects_wrong_source():
    payload = response_with_one_alert()
    payload["evidence"][0]["record"]["source"] = "demo"
    payload["evidence"][0]["sha256"] = canonical_sha256(payload["evidence"][0]["record"])
    with pytest.raises(ValueError, match="normalized Wazuh"):
        validate_response(payload)


def test_acceptance_validator_rejects_case_mismatch():
    payload = response_with_one_alert()
    payload["investigation"]["case_id"] = "OTHER"
    with pytest.raises(ValueError, match="not bound"):
        validate_response(payload)
