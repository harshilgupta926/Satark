"""Unit tests for the live worker acceptance gate; no network or database writes."""
from __future__ import annotations

import copy

import pytest

from scripts.accept_firstlight_worker_live import validate_worker_acceptance


def valid_inputs():
    cursor = "2026-10-21T10:00:00.000Z"
    return (
        {"status": "ok", "fetched": 2, "cursor": cursor},
        [{"last_status": "ok", "last_event_timestamp": cursor}],
        [{"id": "evidence-row-1", "source_label": "Wazuh"}],
        1,
    )


def test_worker_acceptance_requires_nonempty_real_poll_and_verified_snapshot():
    report = validate_worker_acceptance(*valid_inputs())
    assert report["result"] == "PASS"
    assert report["fetched_events"] == 2
    assert report["source_snapshot_objects_re_read_and_digest_verified"] == 1
    assert report["response_actions_executed"] is False


@pytest.mark.parametrize("field,value", [
    ("status", "error"),
    ("fetched", 0),
    ("fetched", True),
    ("cursor", ""),
])
def test_worker_acceptance_rejects_failed_or_empty_poll(field, value):
    run_result, checkpoint, evidence, verified = valid_inputs()
    run_result = copy.deepcopy(run_result)
    run_result[field] = value
    with pytest.raises(ValueError):
        validate_worker_acceptance(run_result, checkpoint, evidence, verified)


def test_worker_acceptance_rejects_missing_or_failed_checkpoint():
    run_result, _, evidence, verified = valid_inputs()
    with pytest.raises(ValueError, match="checkpoint is missing"):
        validate_worker_acceptance(run_result, [], evidence, verified)
    with pytest.raises(ValueError, match="not marked successful"):
        validate_worker_acceptance(run_result, [{"last_status": "error", "last_event_timestamp": run_result["cursor"]}], evidence, verified)


def test_worker_acceptance_rejects_checkpoint_cursor_mismatch():
    run_result, checkpoint, evidence, verified = valid_inputs()
    checkpoint[0]["last_event_timestamp"] = "2026-10-21T09:00:00.000Z"
    with pytest.raises(ValueError, match="does not match"):
        validate_worker_acceptance(run_result, checkpoint, evidence, verified)


def test_worker_acceptance_rejects_missing_evidence_or_unverified_source_objects():
    run_result, checkpoint, _, _ = valid_inputs()
    with pytest.raises(ValueError, match="no durable Wazuh evidence"):
        validate_worker_acceptance(run_result, checkpoint, [], 0)
    with pytest.raises(ValueError, match="no preserved source snapshots"):
        validate_worker_acceptance(run_result, checkpoint, [{"id": "row"}], 0)
