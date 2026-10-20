"""Explicitly approved Microsoft Defender / Entra response CLI.

This tool can perform real, high-impact tenant actions. It never infers targets
from findings and requires a separate opt-in flag, server-side feature flag,
interactive terminal, reason, and exact target-bound confirmation.
"""
from __future__ import annotations

import argparse
import json
import sys

from integrations.response_actions import (
    ResponseIntegrationError,
    isolate_defender_device,
    live_response_enabled,
    revoke_entra_user_sessions,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", required=True, choices=("isolate-device", "revoke-user-sessions"))
    parser.add_argument("--target", required=True, help="Exact Defender device ID or Entra user ID/UPN")
    parser.add_argument("--reason", required=True, help="Incident/case reference and justification; 1–1000 characters")
    parser.add_argument("--isolation-type", choices=("Full", "Selective", "UnManagedDevice"), default="Full")
    parser.add_argument("--execute-live-action", action="store_true", help="Required second opt-in; without it, no provider request is made")
    args = parser.parse_args(argv)

    if not args.execute_live_action:
        print("No action performed. Re-run with --execute-live-action only after reviewing the target and impact.", file=sys.stderr)
        return 2
    if not sys.stdin.isatty():
        print("No action performed: live response requires an interactive terminal for target-bound confirmation.", file=sys.stderr)
        return 2
    if not live_response_enabled():
        print("No action performed: SATARK_ENABLE_LIVE_RESPONSE is not enabled in the trusted server environment.", file=sys.stderr)
        return 2
    if not args.target.strip() or not args.reason.strip():
        print("No action performed: target and reason are required.", file=sys.stderr)
        return 2

    verb = "ISOLATE" if args.action == "isolate-device" else "REVOKE_SESSIONS"
    expected = f"CONFIRM {verb} {args.target}"
    print("LIVE SECURITY RESPONSE — REVIEW BEFORE CONTINUING")
    print(f"Action: {args.action}")
    print(f"Exact target: {args.target}")
    print(f"Reason: {args.reason}")
    if args.action == "isolate-device":
        print(f"Isolation type: {args.isolation_type}")
        print("Impact: the device may lose access to network resources while isolated.")
    else:
        print("Impact: the user may need to authenticate again; session invalidation can take time.")
    print("This sends a real request to Microsoft. It is not a simulation.")
    try:
        confirmation = input(f"Type exactly {expected!r} to continue: ")
        if confirmation != expected:
            print("No action performed: confirmation did not match.", file=sys.stderr)
            return 2
        if args.action == "isolate-device":
            result = isolate_defender_device(
                args.target,
                confirmation=confirmation,
                isolation_type=args.isolation_type,
                reason=args.reason,
            )
        else:
            result = revoke_entra_user_sessions(
                args.target,
                confirmation=confirmation,
                reason=args.reason,
            )
        print(json.dumps({
            "provider": result.provider,
            "action": result.action,
            "target": result.target,
            "status": result.status,
            "detail": result.detail,
            "note": "Provider submission is not proof of completion. Verify final status in the Microsoft security/identity console.",
        }, indent=2, sort_keys=True))
        return 0 if result.status == "submitted" else 3
    except (ResponseIntegrationError, EOFError, KeyboardInterrupt) as exc:
        print(f"No confirmed successful response: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
