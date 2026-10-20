/** FIRSTLIGHT browser-side triage rules.
 *
 * This is a bounded UI fallback, not a replacement for the Python investigation
 * engine. Records with a detected hash mismatch are quarantined from findings.
 */
export function getTrustedFirstlightEvidence(evidence) {
  if (!Array.isArray(evidence)) return [];
  return evidence.filter(item => item && typeof item === 'object' && item.tampered !== true);
}

export function buildFirstlightFindings(evidence) {
  const trusted = getTrustedFirstlightEvidence(evidence);
  const all = trusted.map(item => String(item.summary || '') + ' ' + String(item.kind || '')).join(' ').toLowerCase();
  const out = [];
  const add = (condition, title, detail, severity, matcher, fields = 'summary') => {
    if (!condition) return;
    out.push({
      title,
      detail,
      severity,
      refs: trusted.filter(item => matcher.test(fields === 'summary' ? String(item.summary || '') : String(item.summary || '') + ' ' + String(item.kind || ''))).map(item => item.id),
    });
  };

  add(
    /new browser|new device|new location/.test(all),
    'Unfamiliar sign-in context',
    'A sign-in is described as coming from a new browser or device. Corroborate with identity-provider logs.',
    'Review',
    /new browser|new device|new location/i,
  );
  add(
    /forwarding rule|mailbox rule|rule_change/.test(all),
    'Mailbox forwarding or rule change',
    'Unexpected forwarding can support persistence or data exposure. Verify the rule owner and destination.',
    'High',
    /forwarding rule|mailbox rule|rule_change/i,
    'both',
  );
  add(
    /mfa|multi-factor|authentication settings/.test(all),
    'Authentication setting changed',
    'Check whether the change was authorized and whether recovery methods were altered.',
    'High',
    /mfa|multi-factor|authentication settings/i,
    'both',
  );
  add(
    /suspicious attachment|process/.test(all),
    'Potentially suspicious endpoint activity',
    'The imported summary mentions a process or attachment. This prototype does not inspect the endpoint or file.',
    'Review',
    /suspicious attachment|process/i,
    'both',
  );
  add(
    /lookalike|urgent|password|otp|credential/.test(all),
    'Social-engineering indicators',
    'Urgency, lookalike domains or credential requests warrant independent sender and destination verification.',
    'Review',
    /lookalike|urgent|password|otp|credential/i,
  );
  return out;
}
