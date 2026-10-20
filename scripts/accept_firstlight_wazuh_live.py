#!/usr/bin/env python3
"""Live FIRSTLIGHT/Wazuh acceptance probe.

This script never creates alerts or falls back to demo data. It calls the
configured FIRSTLIGHT API and exits non-zero unless real Wazuh evidence is
returned and its normalized snapshot digests verify locally.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def canonical_sha256(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_response(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("API response must be a JSON object")
    if payload.get("source") != "wazuh-indexer" or payload.get("mode") != "live_read_only_investigation":
        raise ValueError("Response is not from the live Wazuh investigation endpoint")
    if payload.get("persisted") is not False:
        raise ValueError("Unexpected persistence contract; review the endpoint before accepting")
    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("No real Wazuh alerts returned; this is NOT a passing live acceptance test")
    summary = payload.get("integrity_summary")
    expected_summary = {
        "total": len(evidence),
        "sealed": len(evidence),
        "source_verified": 0,
        "mismatched": 0,
    }
    if summary != expected_summary:
        raise ValueError("Evidence integrity summary does not match the documented sealing contract")
    seen: set[str] = set()
    for item in evidence:
        if not isinstance(item, dict) or not isinstance(item.get("record"), dict):
            raise ValueError("Malformed evidence envelope")
        record = item["record"]
        evidence_id = item.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id or evidence_id in seen:
            raise ValueError("Evidence IDs must be non-empty and unique")
        seen.add(evidence_id)
        if record.get("event_id") != evidence_id:
            raise ValueError("Evidence envelope ID does not match the hashed record")
        if record.get("source") != "wazuh" or record.get("kind") != "security_alert":
            raise ValueError("Evidence does not identify as a normalized Wazuh security alert")
        details = record.get("details")
        if not isinstance(details, dict):
            raise ValueError("Wazuh evidence details are missing")
        if not all(isinstance(details.get(key), str) and details[key] for key in ("index", "document_id", "source_record_sha256")):
            raise ValueError("Wazuh source index/document/digest provenance is incomplete")
        source_digest = details["source_record_sha256"]
        if not re.fullmatch(r"[0-9a-f]{64}", source_digest):
            raise ValueError("Wazuh source snapshot digest is malformed")
        expected = item.get("sha256")
        actual = canonical_sha256(record)
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected) or not hashlib.compare_digest(expected, actual):
            raise ValueError("Normalized evidence snapshot digest verification failed")
    investigation = payload.get("investigation")
    if not isinstance(investigation, dict) or investigation.get("case_id") != payload.get("case_id"):
        raise ValueError("Investigation result is missing or not bound to the returned case ID")
    return {
        "result": "PASS",
        "source": "wazuh-indexer",
        "mode": payload["mode"],
        "case_id": payload.get("case_id"),
        "alerts_verified": len(evidence),
        "normalized_snapshot_digests_verified": len(evidence),
        "upstream_source_signatures_verified": 0,
        "persisted": False,
        "response_actions_executed": False,
        "findings_count": len(investigation.get("findings", [])) if isinstance(investigation.get("findings"), list) else None,
        "limitations": [
            "A passing result proves the API returned Wazuh-indexed records and their normalized snapshot digests verify.",
            "It does not prove Wazuh source authenticity, durable persistence, tenant RLS isolation, or provider-side response.",
        ],
    }


def main() -> int:
    base = os.getenv("FIRSTLIGHT_API_BASE_URL", "").strip().rstrip("/")
    token = os.getenv("FIRSTLIGHT_WAZUH_SYNC_TOKEN", "")
    tenant_id = os.getenv("FIRSTLIGHT_WAZUH_TENANT_ID", "").strip()
    if not base or len(token) < 32 or not tenant_id:
        print("Missing FIRSTLIGHT_API_BASE_URL, FIRSTLIGHT_WAZUH_SYNC_TOKEN (>=32 chars), or FIRSTLIGHT_WAZUH_TENANT_ID.", file=sys.stderr)
        return 2
    parsed = urlsplit(base)
    allow_http = os.getenv("FIRSTLIGHT_ACCEPTANCE_ALLOW_HTTP", "").lower() in {"1", "true", "yes"}
    if (
        parsed.scheme not in ({"https", "http"} if allow_http else {"https"})
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        print("API base URL must be an HTTPS origin/path without embedded credentials, query, or fragment.", file=sys.stderr)
        return 2
    try:
        limit = int(os.getenv("FIRSTLIGHT_WAZUH_ACCEPTANCE_LIMIT", "20"))
    except ValueError:
        print("FIRSTLIGHT_WAZUH_ACCEPTANCE_LIMIT must be an integer.", file=sys.stderr)
        return 2
    if not 1 <= limit <= 100:
        print("FIRSTLIGHT_WAZUH_ACCEPTANCE_LIMIT must be between 1 and 100.", file=sys.stderr)
        return 2
    query = {"tenant_id": tenant_id, "limit": limit}
    since = os.getenv("FIRSTLIGHT_WAZUH_SINCE", "").strip()
    if since:
        query["since"] = since
    url = base + "/api/v1/integrations/wazuh/investigate?" + urlencode(query)
    request = Request(
        url,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        method="POST",
    )
    try:
        with build_opener(NoRedirect()).open(request, timeout=15) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError("API response exceeded 2 MiB acceptance limit")
        payload = json.loads(raw.decode("utf-8"))
        report = validate_response(payload)
    except HTTPError as exc:
        print(f"Live acceptance failed: API returned HTTP {exc.code}.", file=sys.stderr)
        return 1
    except (URLError, TimeoutError, OSError) as exc:
        print(f"Live acceptance failed: API is unreachable ({type(exc).__name__}).", file=sys.stderr)
        return 1
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Live acceptance failed: {exc}.", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
