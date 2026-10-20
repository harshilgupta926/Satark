"""Explicitly opted-in live acceptance probe for the persistent Wazuh worker.

This test performs real writes to the configured SATARK test case: evidence
objects/rows and the ingestion checkpoint. It refuses to run unless the
operator confirms the exact tenant and case IDs and enables the write gate.
Never run it against a shared or production tenant as a convenience test.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

from firstlight_wazuh_worker import (
    WazuhSupabaseWorker,
    _parse_timestamp,
    _safe_error_code,
)


WRITE_CONFIRMATION = "I_AUTHORIZE_WRITES_TO_THIS_TEST_CASE"


def validate_worker_acceptance(
    run_result: dict[str, Any],
    checkpoint_rows: Any,
    evidence_rows: Any,
    verified_snapshot_count: int,
) -> dict[str, Any]:
    """Fail closed unless a real non-empty poll persisted and verifies evidence."""
    if not isinstance(run_result, dict) or run_result.get("status") != "ok":
        raise ValueError("worker poll did not return status=ok")
    fetched = run_result.get("fetched")
    cursor = run_result.get("cursor")
    if not isinstance(fetched, int) or isinstance(fetched, bool) or fetched < 1:
        raise ValueError("no real Wazuh events were fetched; acceptance cannot pass")
    if not isinstance(cursor, str) or not cursor:
        raise ValueError("worker did not return its checkpoint cursor")
    if not isinstance(checkpoint_rows, list) or not checkpoint_rows:
        raise ValueError("durable ingestion checkpoint is missing")
    checkpoint = checkpoint_rows[0]
    if not isinstance(checkpoint, dict) or checkpoint.get("last_status") != "ok":
        raise ValueError("durable ingestion checkpoint is not marked successful")
    try:
        actual_cursor = _parse_timestamp(str(checkpoint.get("last_event_timestamp", "")), "stored checkpoint")
        expected_cursor = _parse_timestamp(cursor, "worker cursor")
    except ValueError as exc:
        raise ValueError("stored checkpoint timestamp is invalid") from exc
    if actual_cursor != expected_cursor:
        raise ValueError("durable checkpoint does not match the completed poll cursor")
    if not isinstance(evidence_rows, list) or not evidence_rows:
        raise ValueError("no durable Wazuh evidence rows were found for the configured case")
    if not isinstance(verified_snapshot_count, int) or verified_snapshot_count < 1:
        raise ValueError("no preserved source snapshots were re-read and verified")
    return {
        "result": "PASS",
        "component": "firstlight-wazuh-worker",
        "mode": "live_persistent_ingestion",
        "fetched_events": fetched,
        "checkpoint_status": "ok",
        "checkpoint_cursor": cursor,
        "durable_evidence_rows_examined": len(evidence_rows),
        "source_snapshot_objects_re_read_and_digest_verified": verified_snapshot_count,
        "response_actions_executed": False,
        "limitations": [
            "This proves a successful poll, a matching durable checkpoint, and byte-level verification of sampled preserved source objects.",
            "It does not independently prove Wazuh source authenticity, tenant RLS isolation, response execution, or production readiness.",
        ],
    }


def main() -> int:
    if os.getenv("FIRSTLIGHT_WAZUH_ACCEPTANCE_ALLOW_WRITES", "") != WRITE_CONFIRMATION:
        print(
            "Refusing to run: set FIRSTLIGHT_WAZUH_ACCEPTANCE_ALLOW_WRITES="
            + WRITE_CONFIRMATION
            + " only for an explicitly authorized isolated test case.",
            file=sys.stderr,
        )
        return 2
    try:
        worker = WazuhSupabaseWorker.from_env()
        tenant_confirmation = os.getenv("FIRSTLIGHT_WAZUH_ACCEPTANCE_CONFIRM_TENANT_ID", "").strip().lower()
        case_confirmation = os.getenv("FIRSTLIGHT_WAZUH_ACCEPTANCE_CONFIRM_CASE_ID", "").strip().lower()
        if tenant_confirmation != worker.tenant_id or case_confirmation != worker.case_id:
            print(
                "Refusing to run: confirmation tenant/case IDs must exactly match "
                "FIRSTLIGHT_WAZUH_TENANT_ID and FIRSTLIGHT_WAZUH_CASE_ID.",
                file=sys.stderr,
            )
            return 2

        # This is intentionally a real write-path test. The worker revalidates
        # target case ownership and actor membership before polling and before
        # privileged writes; no fixtures or synthetic events are created here.
        result = worker.run_once()
        checkpoint_rows = worker.rest.request(
            "GET",
            "satark_ingestion_checkpoints",
            query={
                "select": "tenant_id,case_id,source_key,last_event_timestamp,last_status",
                "tenant_id": "eq." + worker.tenant_id,
                "case_id": "eq." + worker.case_id,
                "source_key": "eq." + worker.source_key,
                "limit": "1",
            },
        )
        evidence_rows = worker.rest.request(
            "GET",
            "satark_evidence",
            query={
                "select": "id,tenant_id,case_id,source_label,source_sha256,record_sha256,metadata",
                "tenant_id": "eq." + worker.tenant_id,
                "case_id": "eq." + worker.case_id,
                "source_label": "eq.Wazuh",
                "order": "observed_at.desc",
                "limit": "10",
            },
        )
        if not isinstance(evidence_rows, list):
            raise ValueError("evidence query did not return a list")
        verified = 0
        for row in evidence_rows:
            if not isinstance(row, dict):
                raise ValueError("malformed durable evidence row")
            metadata = row.get("metadata")
            if not isinstance(metadata, dict):
                raise ValueError("durable evidence row has no metadata")
            source_path = metadata.get("source_object_path")
            source_digest = row.get("source_sha256")
            if not isinstance(source_path, str) or not source_path:
                raise ValueError("durable evidence row is missing its preserved source object path")
            if not isinstance(source_digest, str) or len(source_digest) != 64:
                raise ValueError("durable evidence row is missing its source snapshot digest")
            if not worker.rest.verify_source_snapshot(
                tenant_id=worker.tenant_id,
                case_id=worker.case_id,
                path=source_path,
                digest=source_digest,
            ):
                raise ValueError("a preserved source object failed byte-level digest verification")
            verified += 1
        report = validate_worker_acceptance(result, checkpoint_rows, evidence_rows, verified)
        report["tenant_id"] = worker.tenant_id
        report["case_id"] = worker.case_id
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        # Do not print exception text: URL errors and HTTP libraries can include
        # sensitive host details. Emit only a bounded category.
        print(
            json.dumps({
                "result": "FAIL",
                "component": "firstlight-wazuh-worker",
                "error_code": _safe_error_code(exc),
                "exception_type": type(exc).__name__,
                "response_actions_executed": False,
            }),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
